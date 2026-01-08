import os
import sys
import json
import asyncio
from contextlib import asynccontextmanager, AsyncExitStack
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import httpx

# Importações do MCP
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

# --- Configuração de Caminhos e Ambiente ---
# Define o diretório base para garantir acesso correto aos arquivos no Vercel
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "mcp_servers.json")
ENV_FILE = os.path.join(BASE_DIR, ".env")

# Carrega variáveis de ambiente
load_dotenv(ENV_FILE)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Inicializa cliente Groq se a chave existir
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Estado Global (Resetado a cada execução serverless)
mcp_sessions = {}
mcp_tools_map = {}
gemini_tools_schema = []

# --- Funções Auxiliares MCP ---

def convert_schema_to_gemini(schema):
    """Converte schemas JSON para formato aceito pelo Gemini."""
    if not isinstance(schema, dict):
        return schema

    skip_fields = {"default", "additionalProperties", "examples", "nullable"}
    converted = {}
    
    for key, value in schema.items():
        if key in skip_fields:
            continue

        if key == "properties" and isinstance(value, dict):
            converted[key] = {k: convert_schema_to_gemini(v) for k, v in value.items()}
        elif key == "type" and isinstance(value, str):
            converted[key] = value.upper()
        elif isinstance(value, dict):
            converted[key] = convert_schema_to_gemini(value)
        elif isinstance(value, list):
            converted[key] = [convert_schema_to_gemini(item) if isinstance(item, dict) else item for item in value]
        else:
            converted[key] = value
    return converted

async def connect_to_server(name, config, stack):
    """Conecta a um servidor MCP via Stdio."""
    print(f"🔌 Conectando ao servidor Stdio: {name}...")

    # Ajuste para garantir caminho absoluto se for script Python
    cmd = config["command"]
    args = config["args"]
    
    if (cmd == "python" or cmd == "python3") and args and args[0].endswith(".py"):
        script_path = os.path.join(BASE_DIR, args[0])
        args[0] = script_path

    server_params = StdioServerParameters(
        command=cmd,
        args=args,
        env=os.environ.copy()
    )

    try:
        transport = await stack.enter_async_context(stdio_client(server_params))
        read, write = transport
        session = await stack.enter_async_context(ClientSession(read, write))

        await asyncio.wait_for(session.initialize(), timeout=5.0)
        result = await asyncio.wait_for(session.list_tools(), timeout=5.0)

        mcp_sessions[name] = session

        for tool in result.tools:
            mcp_tools_map[tool.name] = name
            gemini_tools_schema.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": convert_schema_to_gemini(tool.inputSchema)
            })
            print(f"   🛠️  Ferramenta carregada: {tool.name}")

    except Exception as e:
        print(f"❌ Falha ao conectar em {name} (Stdio): {e}")

async def connect_to_http_server(name, config, stack):
    """Conecta a um servidor MCP via HTTP."""
    print(f"🌐 Conectando ao servidor HTTP: {name}...")

    url = config["url"]
    headers = config.get("headers", {})

    for key, value in headers.items():
        if isinstance(value, str) and value.startswith("$"):
            headers[key] = os.getenv(value[1:], value)

    try:
        http_client = httpx.AsyncClient(headers=headers, timeout=10.0)
        transport = await stack.enter_async_context(streamable_http_client(url, http_client=http_client))
        read, write, _ = transport

        session = ClientSession(read, write)
        await stack.enter_async_context(session)

        await asyncio.wait_for(session.initialize(), timeout=5.0)
        mcp_sessions[name] = session

        result = await asyncio.wait_for(session.list_tools(), timeout=5.0)

        for tool in result.tools:
            mcp_tools_map[tool.name] = name
            gemini_tools_schema.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": convert_schema_to_gemini(tool.inputSchema)
            })
            print(f"   🛠️  Ferramenta carregada (HTTP): {tool.name}")

    except Exception as e:
        print(f"❌ Falha ao conectar em {name} (HTTP): {e}")

# --- Lifespan (Inicialização) ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação e conexões MCP."""
    print("🚀 Iniciando lifespan do FastAPI...")
    async with AsyncExitStack() as stack:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                
                # Executa conexões em paralelo para reduzir tempo de boot
                tasks = []
                for name, conf in config.get("mcpServers", {}).items():
                    tasks.append(connect_to_server(name, conf, stack))
                
                for name, conf in config.get("mcpServersHTTP", {}).items():
                    tasks.append(connect_to_http_server(name, conf, stack))
                
                if tasks:
                    await asyncio.gather(*tasks)
            except Exception as e:
                print(f"⚠️ Erro ao carregar configurações MCP: {e}")
        else:
            print(f"⚠️ Arquivo {CONFIG_FILE} não encontrado.")

        yield
        print("🛑 Desligando conexões MCP...")

# --- Configuração FastAPI ---

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: list = []
    model: str = "gemini"

# --- Endpoints ---

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "mcp_servers": list(mcp_sessions.keys()),
        "tools_count": len(mcp_tools_map),
        "tools": list(mcp_tools_map.keys())
    }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    if request.model == "groq":
        return await chat_with_groq(request)
    else:
        return await chat_with_gemini(request)

# --- Lógica de Chat: Groq ---

async def chat_with_groq(request: ChatRequest):
    if not groq_client:
        raise HTTPException(status_code=500, detail="Groq API key não configurada")

    try:
        tools_for_groq = [{
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
        } for tool in gemini_tools_schema] if gemini_tools_schema else []

        messages = request.history + [{"role": "user", "content": request.message}]

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=tools_for_groq if tools_for_groq else None,
            tool_choice="auto" if tools_for_groq else None
        )

        if response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                if fn_name in mcp_tools_map:
                    try:
                        server_name = mcp_tools_map[fn_name]
                        session = mcp_sessions[server_name]
                        mcp_result = await asyncio.wait_for(
                            session.call_tool(fn_name, arguments=fn_args),
                            timeout=25.0
                        )
                        tool_output = mcp_result.content[0].text if mcp_result.content else str(mcp_result)
                    except asyncio.TimeoutError:
                        tool_output = f"Erro: Timeout ao executar {fn_name}"
                    except Exception as e:
                        tool_output = f"Erro ao executar ferramenta: {str(e)}"

                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": response.choices[0].message.tool_calls
                    })
                    messages.append({
                        "role": "tool",
                        "content": tool_output,
                        "tool_call_id": tool_call.id
                    })

                    final_response = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=messages
                    )
                    return {"reply": final_response.choices[0].message.content}

        return {"reply": response.choices[0].message.content}

    except Exception as e:
        print(f"Erro Groq: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Lógica de Chat: Gemini ---

async def chat_with_gemini(request: ChatRequest):
    try:
        import google.generativeai as genai
    except ImportError:
         raise HTTPException(status_code=500, detail="Biblioteca google-generativeai não instalada.")

    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="Google API key não configurada")

    genai.configure(api_key=GOOGLE_API_KEY)

    # Nota: Em serverless, instanciar o modelo a cada requisição é aceitável
    model = genai.GenerativeModel(
        'gemini-2.0-flash-exp', # Versão atualizada recomendada
        tools=gemini_tools_schema if gemini_tools_schema else None
    )

    chat = model.start_chat(history=request.history)

    try:
        response = chat.send_message(request.message)

        # Loop de Function Calling
        while response.candidates and response.candidates[0].content.parts[0].function_call:
            part = response.candidates[0].content.parts[0]
            fn_call = part.function_call
            fn_name = fn_call.name
            fn_args = dict(fn_call.args)
            
            print(f"🤖 Gemini pediu: {fn_name}")
            
            server_name = mcp_tools_map.get(fn_name)
            tool_output = ""
            
            if server_name:
                try:
                    session = mcp_sessions[server_name]
                    mcp_result = await asyncio.wait_for(
                        session.call_tool(fn_name, arguments=fn_args),
                        timeout=25.0
                    )
                    
                    if mcp_result.content and hasattr(mcp_result.content[0], 'text'):
                        tool_output = mcp_result.content[0].text
                    else:
                        tool_output = str(mcp_result)
                except asyncio.TimeoutError:
                    tool_output = f"Erro: Timeout na ferramenta {fn_name}"
                except Exception as e:
                    tool_output = f"Erro na execução da ferramenta: {str(e)}"
            else:
                tool_output = f"Erro: Ferramenta {fn_name} desconhecida."

            # Envia resposta da ferramenta de volta ao Gemini
            response = chat.send_message(
                genai.protos.Content(
                    parts=[genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=fn_name,
                            response={'result': tool_output}
                        )
                    )]
                )
            )
            
        return {"reply": response.text}

    except Exception as e:
        print(f"Erro Crítico no Gemini Chat: {e}")
        return {"reply": f"Erro interno: {str(e)}"}