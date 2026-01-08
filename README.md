# 🏛️ MCP Senado - Consulta APIs do Congresso Nacional

Sistema de consulta às APIs públicas do **Senado Federal** e **Câmara dos Deputados** usando MCP (Model Context Protocol) e LLMs (Gemini/Groq).

## 🎯 Funcionalidades

### Senado Federal
- ✅ Listar senadores (com filtro por UF)
- ✅ Buscar proposições (PEC, PL, PLS, MPV)
- ✅ Detalhes de proposições
- ✅ Votações plenárias
- ✅ Comissões (permanentes, CPIs, temporárias)
- ✅ Agenda de comissões e reuniões
- ✅ Detalhes de reuniões
- ✅ Vídeos de reuniões de comissões
- ✅ Matérias legislativas
- ✅ Autorias de senadores
- ✅ Partidos políticos (ativos e extintos)
- ✅ Tipos de cargo em comissões
- ✅ Mesa Diretora do Congresso Nacional
- ✅ Mesa Diretora do Senado Federal

### Câmara dos Deputados
- ✅ Listar deputados (com filtros por UF e partido)
- ✅ Buscar proposições (PL, PEC, MPV)
- ✅ Detalhes de proposições
- ✅ Votações
- ✅ Despesas parlamentares
- ✅ Eventos e audiências
- ✅ Órgãos (comissões, frentes)
- ✅ Partidos e blocos parlamentares
- ✅ Frentes parlamentares

## 🚀 Instalação

### 1. Criar arquivo .env

```bash
cd backend
cp .env.example .env
```

Edite `.env` e adicione suas chaves de API:

```bash
GOOGLE_API_KEY=sua_chave_gemini
GROQ_API_KEY=sua_chave_groq
```

### 2. Instalar dependências

```bash
cd backend
pip3 install -r requirements.txt
```

### 3. Iniciar o servidor

```bash
# Do diretório raiz
./start.command
```

Ou manualmente:

```bash
# Terminal 1 - Backend
cd backend
python3 main.py

# Terminal 2 - Frontend
cd frontend
python3 -m http.server 3000
```

### 4. Abrir no navegador

```
http://localhost:3000
```

## 📖 Como Usar

### Exemplos de Consultas

**Senadores**:
- "Liste os senadores do Ceará"
- "Quem são os senadores em exercício?"

**Proposições**:
- "Busque as PECs de 2024"
- "Mostre os projetos de lei sobre educação"

**Comissões**:
- "Liste as comissões permanentes do Senado"
- "Qual a agenda da CCJ para esta semana?"

**Deputados**:
- "Liste deputados do PT"
- "Quem são os deputados de São Paulo?"

**Despesas**:
- "Mostre as despesas do deputado X em 2024"
- "Quanto gastou o deputado Y em dezembro?"

## 🏗️ Arquitetura

```
MCP SENADO/
├── backend/
│   ├── main.py                          # FastAPI + MCP
│   ├── senado_camara_mcp_server.py     # Servidor MCP (ÚNICO)
│   ├── mcp_servers.json                 # Configuração
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── styles.css
├── start.command                        # Inicia tudo
└── README.md
```

## 🔧 Configuração

### MCP Servers

O arquivo `backend/mcp_servers.json` configura apenas o servidor do Senado e Câmara:

```json
{
  "mcpServers": {
    "senado-camara": {
      "command": "python3",
      "args": ["backend/senado_camara_mcp_server.py"]
    }
  }
}
```

### LLM Provider

O sistema suporta:
- **Gemini** (recomendado) - Generoso free tier
- **Groq** - Muito rápido, free tier limitado

Configure no `.env`:

```bash
# Gemini (padrão)
GOOGLE_API_KEY=sua_chave

# OU Groq (alternativa)
GROQ_API_KEY=sua_chave
```

## 📊 APIs Utilizadas

### Senado Federal
- **Base URL**: `https://legis.senado.leg.br/dadosabertos`
- **Formato**: JSON e XML
- **Documentação**: https://legis.senado.leg.br/dadosabertos/docs/

### Câmara dos Deputados
- **Base URL**: `https://dadosabertos.camara.leg.br/api/v2`
- **Formato**: JSON
- **Documentação**: https://dadosabertos.camara.leg.br/swagger/api.html

## 🐛 Troubleshooting

### Erro: "Timeout ao conectar"

**Causa**: Caminho do Python ou do servidor incorreto

**Solução**: Verifique em `mcp_servers.json` se o caminho está correto:

```bash
# Descobrir caminho do Python
which python3

# Atualizar mcp_servers.json com o caminho correto
```

### Erro: "API Key não encontrada"

**Causa**: `.env` não configurado

**Solução**:
```bash
cd backend
cp .env.example .env
nano .env  # Adicione suas chaves
```

### Porta 8000 em uso

**Solução**: Mude a porta em `backend/main.py`:

```python
# Linha final
uvicorn.run(app, host="0.0.0.0", port=8001)
```

## 🔗 Links Úteis

- **Dados Abertos do Senado**: https://www12.senado.leg.br/dados-abertos
- **Dados Abertos da Câmara**: https://dadosabertos.camara.leg.br/
- **MCP Protocol**: https://modelcontextprotocol.io/
- **FastMCP**: https://github.com/jlowin/fastmcp

## 📝 Notas

- ✅ **100% Gratuito** - Usa apenas APIs públicas
- ✅ **Sem autenticação** - APIs abertas do governo
- ✅ **Tempo real** - Dados atualizados constantemente
- ✅ **Completo** - Acesso a todas as funcionalidades das APIs

## 🎓 Casos de Uso

### 1. Acompanhamento Legislativo
- Monitore tramitação de projetos específicos
- Acompanhe votações importantes
- Veja agenda de comissões

### 2. Transparência
- Verifique despesas parlamentares
- Veja autorias e coautorias
- Analise votações nominais

### 3. Pesquisa
- Busque proposições por tema
- Analise composição de comissões
- Estude padrões de votação

### 4. Assessoria
- Prepare briefings sobre matérias
- Acompanhe agenda de reuniões
- Monitore atividade de parlamentares

## 📞 Suporte

Para dúvidas sobre as APIs:
- **Senado**: https://www12.senado.leg.br/dados-abertos/ajuda
- **Câmara**: dados.abertos@camara.leg.br

---

**Versão**: 1.0.0
**Data**: 24/12/2024
**Baseado em**: Mini_browser_MCP_API (clone simplificado)
