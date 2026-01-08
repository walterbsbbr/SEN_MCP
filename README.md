# Sistema MCP - Senado e Câmara (Vercel Ready)

Sistema de chat com IA integrado às APIs do Senado Federal e Câmara dos Deputados, otimizado para deploy no Vercel.

## 🔧 Problema Resolvido

**Antes:** O sistema usava MCP com stdio (subprocessos Python), que não funciona em ambientes serverless como Vercel.

**Agora:** Ferramentas integradas diretamente no FastAPI, sem dependência de processos externos.

## 📁 Arquivos Principais

- `index.py` - Backend FastAPI com Gemini/Groq
- `senado_camara_tools.py` - Todas as 25 ferramentas das APIs
- `app.jsx` - Frontend React
- `requirements.txt` - Dependências Python

## 🚀 Deploy no Vercel

### 1. Configurar Variáveis de Ambiente

No painel do Vercel, adicione:

```
GOOGLE_API_KEY=sua_chave_google
GROQ_API_KEY=sua_chave_groq
```

### 2. Estrutura de Arquivos

```
/
├── api/
│   ├── index.py
│   ├── senado_camara_tools.py
│   └── requirements.txt
├── src/
│   ├── app.jsx
│   ├── main.jsx
│   └── index.css
└── vercel.json
```

### 3. Criar vercel.json

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    },
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "dist"
      }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api/index.py"
    },
    {
      "src": "/(.*)",
      "dest": "/$1"
    }
  ]
}
```

## 🧪 Testar Localmente

```bash
# Backend
cd api
pip install -r requirements.txt
python index.py

# Frontend (em outro terminal)
npm install
npm run dev
```

## 📊 Ferramentas Disponíveis

### Senado Federal (12 ferramentas)
- buscar_senadores
- buscar_proposicoes_senado
- detalhes_proposicao_senado
- votacoes_senado
- listar_comissoes_senado
- detalhes_comissao_senado
- membros_comissao_senado
- reunioes_comissao_senado
- buscar_agenda_comissao
- detalhes_reuniao_comissao
- videos_reuniao_comissao
- mesa_diretora_senado_federal

### Câmara dos Deputados (13 ferramentas)
- buscar_deputados
- detalhes_deputado
- buscar_proposicoes_camara
- detalhes_proposicao_camara
- votacoes_camara
- despesas_deputado
- eventos_camara
- listar_orgaos_camara
- detalhes_orgao_camara
- membros_orgao_camara
- partidos_camara
- blocos_camara
- frentes_parlamentares

## 🔍 Verificação de Funcionamento

Acesse `/api/health` para verificar:

```json
{
  "status": "ok",
  "tools_available": 25,
  "tools_list": ["buscar_senadores", "buscar_deputados", ...]
}
```

## 📝 Exemplos de Perguntas

- "Quem são os senadores de São Paulo?"
- "Busque proposições do tipo PEC de 2025"
- "Liste os deputados do PT"
- "Mostre as votações da semana passada"
- "Quais são as comissões permanentes do Senado?"

## ⚠️ Importante

- Sem dependências de MCP/stdio
- Funciona 100% em serverless
- Ferramentas executam diretamente via Python
- APIs públicas (sem autenticação necessária)

## 🐛 Debug

Logs aparecem no console do Vercel:
- ✅ "Gemini chamou: buscar_senadores"
- ✅ "Resultado obtido com sucesso"
- ❌ "Erro na ferramenta: [detalhes]"
