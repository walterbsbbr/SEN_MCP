import os
import sys
import json
import asyncio
from datetime import datetime
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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Garante que lê o JSON dentro da pasta api
CONFIG_FILE = os.path.join(BASE_DIR, "mcp_servers.json")
ENV_FILE = os.path.join(BASE_DIR, ".env")

# Carrega variáveis de ambiente
load_dotenv(ENV_FILE)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Inicializa cliente Groq
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Estado Global
mcp_sessions = {}
mcp_tools_map = {}
gemini_tools_schema = []

# --- Helpers ---

def get_system_date_context():
    """Retorna a string de contexto com a data atual."""
    now = datetime.now()
    return f"Hoje é dia {now.strftime('%d/%m/%Y')} (Dia da semana: {now.strftime('%A')}). O horário atual é {now.strftime('%H:%M')}."

def convert_schema_to_gemini(schema):
    if not isinstance(schema, dict):
        return schema
    skip_fields = {"default", "additionalProperties", "examples", "nullable"}
    converted = {}
    for key, value in schema.items():
        if key in skip_fields: continue
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

# --- Conexões MCP ---

async def connect_to_server(name, config, stack):
    print(f"🔌 Conectando ao servidor Stdio: {name}...")
    cmd = config["command"]
    args = config["args"]
    
    # Ajuste de caminho para scripts Python: garante path absoluto baseado no diretório atual (api)
    if (cmd == "python" or cmd == "python3") and args and args[0].endswith(".py"):
        script_path = os.path.join(BASE_DIR, args[0])
        args[0] = script_path

    # Copia variáveis de ambiente para o subprocesso
    env = os.environ.copy()
    # Garante que o Python encontre módulos na pasta atual
    env["PYTHONPATH"] = BASE_DIR

    server_params = StdioServerParameters(command=cmd, args=args, env=env)

    try:
        transport = await stack.enter_async_context(stdio_client(server_params))
        read, write = transport
        session = await stack.enter_async_context(ClientSession(read, write))
        
        # Timeout aumentado para garantir inicialização de scripts pesados
        await asyncio.wait_for(session.initialize(), timeout=10.0)
        result = await asyncio.wait_for(session.list_tools(), timeout=10.0)
        
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
        print(f"❌ Falha Stdio {name}: {e}")

async def connect_to_http_server(name, config, stack):
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
        await asyncio.wait_for(session.initialize(), timeout=10.0)
        mcp_sessions[name] = session
        
        result = await asyncio.wait_for(session.list_tools(), timeout=10.0)
        for tool in result.tools:
            mcp_tools_map[tool.name] = name
            gemini_tools_schema.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": convert_schema_to_gemini(tool.inputSchema)
            })
            print(f"   🛠️  Ferramenta HTTP carregada: {tool.name}")
    except Exception as e:
        print(f"❌ Falha HTTP {name}: {e}")

# --- Lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Iniciando lifespan...")
    async with AsyncExitStack() as stack:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                tasks = []
                for name, conf in config.get("mcpServers", {}).items():
                    tasks.append(connect_to_server(name, conf, stack))
                for name, conf in config.get("mcpServersHTTP", {}).items():
                    tasks.append(connect_to_http_server(name, conf, stack))
                if tasks: await asyncio.gather(*tasks)
            except Exception as e:
                print(f"⚠️ Erro config: {e}")
        else:
            print(f"⚠️ Arquivo de configuração não encontrado: {CONFIG_FILE}")
            
        yield
        print("🛑 Desligando...")

# --- App Setup ---

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

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "mcp_servers": list(mcp_sessions.keys()), "tools_count": len(mcp_tools_map)}

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    if request.model == "groq":
        return await chat_with_groq(request)
    else:
        return await chat_with_gemini(request)

# --- Groq Logic ---

async def chat_with_groq(request: ChatRequest):
    if not groq_client: raise HTTPException(500, "Groq API key missing")
    try:
        # Injeta System Prompt com a data
        system_msg = {
            "role": "system", 
            "content": f"Você é um assistente útil. {get_system_date_context()} Use esta data como referência absoluta."
        }
        messages = [system_msg] + request.history + [{"role": "user", "content": request.message}]

        tools_groq = [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}} for t in gemini_tools_schema] if gemini_tools_schema else None

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=tools_groq,
            tool_choice="auto" if tools_groq else None
        )

        if response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                
                tool_output = "Erro desconhecido"
                if fn_name in mcp_tools_map:
                    try:
                        session = mcp_sessions[mcp_tools_map[fn_name]]
                        res = await asyncio.wait_for(session.call_tool(fn_name, arguments=fn_args), timeout=25.0)
                        tool_output = res.content[0].text if res.content else str(res)
                    except Exception as e:
                        tool_output = f"Erro ferramenta: {e}"
                
                messages.append(response.choices[0].message)
                messages.append({"role": "tool", "content": tool_output, "tool_call_id": tool_call.id})
                
                final_res = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages
                )
                return {"reply": final_res.choices[0].message.content}

        return {"reply": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(500, str(e))

# --- Gemini Logic ---

async def chat_with_gemini(request: ChatRequest):
    try: import google.generativeai as genai
    except ImportError: raise HTTPException(500, "google-generativeai missing")
    
    if not GOOGLE_API_KEY: raise HTTPException(500, "Google API key missing")
    genai.configure(api_key=GOOGLE_API_KEY)

    # Injeta System Instruction com a data
    system_instruction = f"Você é um assistente prestativo. {get_system_date_context()} Responda considerando esta data atual."

    model = genai.GenerativeModel(
        'gemini-2.0-flash-exp',
        tools=gemini_tools_schema if gemini_tools_schema else None,
        system_instruction=system_instruction
    )
    
    chat = model.start_chat(history=request.history)
    
    try:
        response = chat.send_message(request.message)
        
        while response.candidates and response.candidates[0].content.parts[0].function_call:
            part = response.candidates[0].content.parts[0]
            fn_call = part.function_call
            fn_name = fn_call.name
            fn_args = dict(fn_call.args)
            
            print(f"🤖 Gemini Call: {fn_name}")
            tool_output = ""
            
            if fn_name in mcp_tools_map:
                try:
                    session = mcp_sessions[mcp_tools_map[fn_name]]
                    res = await asyncio.wait_for(session.call_tool(fn_name, arguments=fn_args), timeout=25.0)
                    tool_output = res.content[0].text if res.content and hasattr(res.content[0], 'text') else str(res)
                except Exception as e:
                    tool_output = f"Erro execucao: {e}"
            else:
                tool_output = f"Ferramenta {fn_name} nao encontrada."

            response = chat.send_message(
                genai.protos.Content(parts=[genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(name=fn_name, response={'result': tool_output})
                )])
            )
            
        return {"reply": response.text}
    except Exception as e:
        print(f"Erro Gemini: {e}")
        return {"reply": f"Erro interno: {e}"}