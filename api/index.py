import os
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

from senado_camara_tools import AVAILABLE_TOOLS, TOOLS_SCHEMA

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

app = FastAPI()
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

def get_system_date_context():
    now = datetime.now()
    return f"Hoje é dia {now.strftime('%d/%m/%Y')} (Dia da semana: {now.strftime('%A')}). O horário atual é {now.strftime('%H:%M')}."

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "tools_available": len(AVAILABLE_TOOLS),
        "tools_list": list(AVAILABLE_TOOLS.keys())
    }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    if request.model == "groq":
        return await chat_with_groq(request)
    else:
        return await chat_with_gemini(request)

async def chat_with_groq(request: ChatRequest):
    if not groq_client:
        raise HTTPException(500, "Groq API key missing")
    
    try:
        system_msg = {
            "role": "system",
            "content": f"""Você é um assistente especializado em dados do Senado Federal e Câmara dos Deputados do Brasil. {get_system_date_context()}

REGRA CRÍTICA: Você DEVE SEMPRE usar as ferramentas disponíveis para responder perguntas sobre dados legislativos.

NUNCA invente informações. Se o usuário perguntar sobre senadores, deputados, proposições, votações, reuniões, agendas - SEMPRE chame a ferramenta apropriada.

Você tem 31 ferramentas disponíveis. USE-AS para buscar dados reais."""
        }
        messages = [system_msg] + request.history + [{"role": "user", "content": request.message}]

        tools_groq = []
        for tool in TOOLS_SCHEMA:
            tools_groq.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": {
                        "type": "object",
                        "properties": {
                            k: {"type": v.get("type", "string").lower(), "description": v.get("description", "")}
                            for k, v in tool["parameters"].get("properties", {}).items()
                        },
                        "required": tool["parameters"].get("required", [])
                    }
                }
            })

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=tools_groq if tools_groq else None,
            tool_choice="auto" if tools_groq else None
        )

        if response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                print(f"🤖 Groq chamou: {fn_name} com args: {fn_args}")

                tool_output = "Erro: ferramenta não encontrada"
                if fn_name in AVAILABLE_TOOLS:
                    try:
                        result = AVAILABLE_TOOLS[fn_name](**fn_args)
                        tool_output = json.dumps(result, ensure_ascii=False)
                    except Exception as e:
                        tool_output = f"Erro ao executar {fn_name}: {str(e)}"
                        print(f"❌ Erro na ferramenta: {e}")

                messages.append(response.choices[0].message)
                messages.append({
                    "role": "tool",
                    "content": tool_output,
                    "tool_call_id": tool_call.id
                })

                final_res = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages
                )
                return {"reply": final_res.choices[0].message.content}

        return {"reply": response.choices[0].message.content}

    except Exception as e:
        print(f"❌ Erro Groq: {e}")
        raise HTTPException(500, str(e))

async def chat_with_gemini(request: ChatRequest):
    try:
        import google.generativeai as genai
    except ImportError:
        raise HTTPException(500, "google-generativeai missing")

    if not GOOGLE_API_KEY:
        raise HTTPException(500, "Google API key missing")

    genai.configure(api_key=GOOGLE_API_KEY)

    system_instruction = f"""Você é um assistente especializado em dados do Senado Federal e Câmara dos Deputados do Brasil. {get_system_date_context()} 

REGRA CRÍTICA: Você DEVE SEMPRE usar as ferramentas disponíveis para responder perguntas sobre:
- Senadores, deputados, comissões
- Proposições, votações, reuniões
- Agendas, eventos, despesas
- Qualquer dado legislativo

NUNCA invente ou adivinhe informações. Se o usuário perguntar algo sobre dados legislativos, SEMPRE chame a ferramenta apropriada primeiro.

Exemplos:
- "Quem são os senadores de SP?" -> CHAME buscar_senadores(uf="SP")
- "Qual o ID da reunião da CCJ de 17/12/2025?" -> CHAME buscar_agenda_comissao(data_inicio="20251217")
- "Busque proposições PEC de 2025" -> CHAME buscar_proposicoes_senado(sigla="PEC", ano="2025")

Você tem 31 ferramentas disponíveis. USE-AS."""

    model = genai.GenerativeModel(
        'gemini-2.0-flash-exp',
        tools=TOOLS_SCHEMA if TOOLS_SCHEMA else None,
        system_instruction=system_instruction
    )

    chat = model.start_chat(history=request.history)

    try:
        response = chat.send_message(request.message)

        max_iterations = 10
        iteration = 0

        while response.candidates and response.candidates[0].content.parts:
            iteration += 1
            if iteration > max_iterations:
                print("⚠️ Limite de iterações atingido")
                break

            has_function_call = False
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    has_function_call = True
                    fn_call = part.function_call
                    fn_name = fn_call.name
                    fn_args = dict(fn_call.args)

                    print(f"🤖 Gemini chamou: {fn_name} com args: {fn_args}")

                    tool_output = ""
                    if fn_name in AVAILABLE_TOOLS:
                        try:
                            result = AVAILABLE_TOOLS[fn_name](**fn_args)
                            tool_output = json.dumps(result, ensure_ascii=False)
                            print(f"✅ Resultado obtido com sucesso")
                        except Exception as e:
                            tool_output = f"Erro ao executar {fn_name}: {str(e)}"
                            print(f"❌ Erro na ferramenta: {e}")
                    else:
                        tool_output = f"Ferramenta {fn_name} não encontrada."
                        print(f"⚠️ Ferramenta não encontrada: {fn_name}")

                    response = chat.send_message(
                        genai.protos.Content(parts=[
                            genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=fn_name,
                                    response={'result': tool_output}
                                )
                            )
                        ])
                    )
                    break

            if not has_function_call:
                break

        return {"reply": response.text}

    except Exception as e:
        print(f"❌ Erro Gemini: {e}")
        return {"reply": f"Erro interno: {e}"}