# 🚀 GUIA DE INSTALAÇÃO - VERCEL DEPLOY

## ⚠️ MUDANÇAS IMPORTANTES

**O QUE MUDOU:**
- ❌ Removido: Sistema MCP com stdio (não funciona no Vercel)
- ✅ Adicionado: Integração direta das ferramentas no FastAPI
- ✅ Resultado: 100% compatível com Vercel serverless

## 📂 ESTRUTURA DE ARQUIVOS

Organize seu projeto desta forma:

```
seu-projeto/
├── api/
│   ├── index.py                    (NOVO - backend sem MCP)
│   ├── senado_camara_tools.py      (NOVO - ferramentas diretas)
│   ├── requirements.txt            (ATUALIZADO - sem MCP)
│   └── mcp_servers.json           (mantido vazio por compatibilidade)
│
├── src/
│   ├── app.jsx                    (frontend - mantém o mesmo)
│   ├── main.jsx
│   └── index.css
│
├── vercel.json                    (NOVO - configuração Vercel)
├── package.json
├── vite.config.js
└── README.md

```

## 🔧 PASSO A PASSO

### 1. Substituir Arquivos na Pasta `api/`

**DELETAR:**
- ❌ `senado_camara_mcp_server.py` (versão MCP antiga)
- ❌ O `index.py` antigo

**ADICIONAR:**
- ✅ `index.py` (novo - baixe dos arquivos gerados)
- ✅ `senado_camara_tools.py` (novo)
- ✅ `requirements.txt` (atualizado)

### 2. Adicionar na Raiz do Projeto

**ADICIONAR:**
- ✅ `vercel.json` (configuração essencial)

### 3. Frontend NÃO Precisa de Mudanças

Seus arquivos React (`app.jsx`, `main.jsx`, `index.css`) continuam iguais!

## 🌐 DEPLOY NO VERCEL

### Opção 1: Via GitHub (Recomendado)

```bash
# 1. Commit das mudanças
git add .
git commit -m "Migração para arquitetura serverless"
git push

# 2. No Vercel Dashboard:
# - Conecte seu repositório
# - Configure variáveis de ambiente:
#   GOOGLE_API_KEY=sua_chave
#   GROQ_API_KEY=sua_chave
# - Deploy automático!
```

### Opção 2: Via Vercel CLI

```bash
# 1. Instalar Vercel CLI
npm i -g vercel

# 2. Login
vercel login

# 3. Deploy
vercel

# 4. Adicionar variáveis de ambiente
vercel env add GOOGLE_API_KEY
vercel env add GROQ_API_KEY

# 5. Redeploy
vercel --prod
```

## ✅ VERIFICAÇÃO

### Teste Local Primeiro:

```bash
# Backend
cd api
pip install -r requirements.txt
python index.py

# Abra: http://localhost:8000/api/health
# Deve retornar: {"status": "ok", "tools_available": 25, ...}
```

### Após Deploy no Vercel:

```bash
# Acesse: https://seu-app.vercel.app/api/health
# Deve retornar as 25 ferramentas carregadas
```

## 🐛 TROUBLESHOOTING

### Se o /api/health mostrar tools_available: 0

**Problema:** Ferramentas não carregadas
**Solução:**
1. Verifique se `senado_camara_tools.py` está em `api/`
2. Verifique logs do Vercel
3. Confirme que `requirements.txt` tem `requests`

### Se aparecer "Module not found: senado_camara_tools"

**Problema:** Estrutura de pastas incorreta
**Solução:**
1. `senado_camara_tools.py` DEVE estar em `api/`
2. No mesmo nível que `index.py`

### Se o chat não chamar as ferramentas

**Problema:** IA não está usando tools
**Solução:**
1. Verifique se as API keys estão configuradas
2. Faça perguntas mais explícitas:
   - ✅ "Busque os senadores de SP"
   - ❌ "Me fale sobre senadores"

## 📊 DIFERENÇAS TÉCNICAS

| Aspecto | Antes (MCP) | Agora (Direto) |
|---------|-------------|----------------|
| Arquitetura | Stdio subprocess | Funções Python diretas |
| Compatibilidade | Só local | Vercel + Local |
| Latência | Alta | Baixa |
| Manutenção | Complexa | Simples |
| Logs | Obscuros | Claros no Vercel |

## 🎯 RESULTADO ESPERADO

Após o deploy, você deve conseguir:

✅ Perguntar: "Quem são os deputados de SP?"
✅ Ver no log: "🤖 Gemini chamou: buscar_deputados"
✅ Receber resposta real da API

## 💡 DICAS PRO

1. **Use o endpoint /api/health para monitorar**
2. **Monitore logs do Vercel em tempo real**
3. **Teste localmente antes de fazer deploy**
4. **As 25 ferramentas estarão sempre disponíveis**

## 📞 SUPORTE

Se algo não funcionar:
1. Confira a estrutura de pastas
2. Veja os logs do Vercel
3. Teste o /api/health endpoint
4. Verifique se as variáveis de ambiente estão setadas
