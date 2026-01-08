# ⚡ Guia Rápido - MCP Senado

## 🚀 Início Rápido (3 passos)

### 1️⃣ Configurar API Keys

```bash
cd backend
cp .env.example .env
nano .env
```

Adicione pelo menos UMA chave:

```bash
# Gemini (recomendado - gratuito)
GOOGLE_API_KEY=sua_chave_aqui

# OU Groq (alternativa - gratuito, rápido)
GROQ_API_KEY=sua_chave_aqui
```

**Obter chaves**:
- Gemini: https://makersuite.google.com/app/apikey
- Groq: https://console.groq.com/keys

### 2️⃣ Instalar Dependências

```bash
cd backend
pip3 install -r requirements.txt
```

### 3️⃣ Iniciar

```bash
# Do diretório raiz
./start.command
```

Abra: **http://localhost:3000**

---

## 💬 Exemplos de Perguntas

### Senadores

```
"Liste os senadores do Ceará"
"Quem são os senadores em exercício?"
"Mostre os senadores do PT"
```

### Proposições do Senado

```
"Busque as PECs de 2024"
"Liste os projetos de lei de 2025"
"Mostre as Medidas Provisórias atuais"
```

### Comissões do Senado

```
"Liste as comissões permanentes"
"Mostre a composição da CCJ"
"Qual a agenda da CAS esta semana?"
```

### Reuniões e Agenda

```
"Qual a agenda do Senado para hoje?"
"Mostre as reuniões da semana que vem"
"Detalhes da reunião da CAE de ontem"
"Me dê os links dos vídeos da reunião da CCJ de 14/10/2024"
"Mostre os vídeos da última reunião da CAE"
```

### Partidos e Composição

```
"Liste todos os partidos políticos do Senado"
"Quais são os tipos de cargo nas comissões?"
"Mostre a Mesa Diretora do Senado Federal"
"Quem compõe a Mesa Diretora do Congresso Nacional?"
```

### Deputados

```
"Liste os deputados de São Paulo"
"Quem são os deputados do PSDB?"
"Mostre deputados do Ceará"
```

### Proposições da Câmara

```
"Busque PLs sobre educação de 2024"
"Mostre PECs em tramitação"
"Liste MPVs de 2025"
```

### Despesas Parlamentares

```
"Mostre despesas do deputado [ID] em 2024"
"Quanto gastou o deputado [ID] em dezembro?"
"Despesas do deputado [ID] em novembro de 2024"
```

### Votações

```
"Votações do Senado em dezembro de 2024"
"Mostre as votações da Câmara de hoje"
"Resultados das votações da semana passada"
```

---

## 🎯 Fluxo de Uso Típico

### Cenário 1: Acompanhar Tramitação de PL

```
1. "Busque projetos de lei sobre meio ambiente de 2024"
   → Retorna lista de PLs

2. "Detalhes da proposição [código]"
   → Ementa, autoria, situação

3. "Votações relacionadas à proposição [ID]"
   → Histórico de votações
```

### Cenário 2: Preparar Briefing de Reunião

```
1. "Agenda da CCJ para 12/12/2024"
   → Lista de reuniões agendadas

2. "Detalhes da reunião [código]"
   → Pauta completa, participantes

3. "Buscar proposições [sigla/ano]"
   → Contexto das matérias na pauta

4. "Vídeos da reunião [código]"
   → Links de vídeo e áudio de cada fala
```

### Cenário 3: Analisar Atividade de Deputado

```
1. "Buscar deputados de [UF]"
   → Lista de deputados do estado

2. "Detalhes do deputado [ID]"
   → Biografia, contatos, mandato

3. "Despesas do deputado [ID] em 2024"
   → Gastos da cota parlamentar

4. "Buscar proposições autor:[nome]"
   → Projetos de autoria
```

---

## 🔍 Dicas de Busca

### Use Filtros Específicos

❌ **Genérico**: "Mostre proposições"
✅ **Específico**: "Mostre PECs de 2024"

❌ **Vago**: "Deputados"
✅ **Filtrado**: "Deputados do PT de São Paulo"

### Peça Detalhes Progressivos

```
1. "Liste comissões permanentes do Senado"
2. "Detalhes da CCJ"  (usa código da resposta anterior)
3. "Membros da CCJ"   (continua explorando)
```

### Use Datas Corretas

**Senado** usa formato: `AAAAMMDD`
```
"Agenda de 20241224" ✅
"Agenda de 2024-12-24" ❌
```

**Câmara** usa formato: `AAAA-MM-DD`
```
"Eventos de 2024-12-24" ✅
"Eventos de 20241224" ❌
```

---

## ⚙️ Configurações

### Mudar Provider de LLM

Na interface web, selecione:
- **Gemini** - Melhor qualidade, free tier generoso
- **Groq** - Mais rápido, free tier limitado

### Ajustar Timeout

Se as respostas são muito lentas, edite `backend/main.py`:

```python
# Linha ~56
await asyncio.wait_for(session.initialize(), timeout=10.0)
# Aumente para 30.0 se necessário
```

### Usar Terminal sem Interface

```bash
cd backend
python3 -c "
from senado_camara_mcp_server import buscar_senadores
print(buscar_senadores('CE'))
"
```

---

## 🐛 Problemas Comuns

### "Timeout ao conectar"

**Causa**: Servidor MCP não iniciou

**Solução**:
```bash
# Teste manual
cd backend
python3 senado_camara_mcp_server.py
```

### "API Key não encontrada"

**Causa**: `.env` não configurado

**Solução**:
```bash
cd backend
cat .env  # Verificar se tem GOOGLE_API_KEY ou GROQ_API_KEY
```

### Respostas incompletas

**Causa**: Limite de tokens do LLM

**Solução**: Perguntas mais específicas ou use filtros

### Interface não abre

**Causa**: Porta 3000 em uso

**Solução**:
```bash
# Usar outra porta
cd frontend
python3 -m http.server 3001
```

---

## 📊 Referência Rápida de Códigos

### Comissões do Senado (Principais)

| Código | Sigla | Nome |
|--------|-------|------|
| 34 | CCJ | Constituição e Justiça |
| 38 | CAE | Assuntos Econômicos |
| 40 | CAS | Assuntos Sociais |
| 42 | CDH | Direitos Humanos |
| 56 | CMA | Meio Ambiente |

### Tipos de Proposições

**Senado**:
- `PEC` - Proposta de Emenda Constitucional
- `PLS` - Projeto de Lei do Senado
- `MPV` - Medida Provisória
- `PRS` - Projeto de Resolução

**Câmara**:
- `PL` - Projeto de Lei
- `PEC` - Proposta de Emenda Constitucional
- `MPV` - Medida Provisória
- `PLP` - Projeto de Lei Complementar

---

## 🎓 Recursos Adicionais

### Documentação das APIs

- **Senado**: https://legis.senado.leg.br/dadosabertos/docs/
- **Câmara**: https://dadosabertos.camara.leg.br/swagger/api.html

### Ferramentas Disponíveis

Execute para ver todas:
```bash
cd backend
python3 senado_camara_mcp_server.py
```

Lista inclui:
- 15 funções do Senado
- 13 funções da Câmara
- Total: 28 ferramentas

---

## 💡 Casos de Uso Avançados

### 1. Monitoramento de Projeto

Crie um script para acompanhar PL específico:

```python
from senado_camara_mcp_server import detalhes_proposicao_senado

# Acompanhar diariamente
codigo = "132046"
resultado = detalhes_proposicao_senado(codigo)
# Salvar/notificar se mudou status
```

### 2. Análise de Despesas

Compare gastos entre deputados:

```python
from senado_camara_mcp_server import despesas_deputado

deputados = ["123", "456", "789"]
for dep in deputados:
    despesas = despesas_deputado(dep, "2024")
    # Processar e comparar
```

### 3. Dashboard de Reuniões

Busque agenda semanal:

```python
from senado_camara_mcp_server import buscar_agenda_comissao
from datetime import datetime, timedelta

hoje = datetime.now().strftime("%Y%m%d")
semana = (datetime.now() + timedelta(days=7)).strftime("%Y%m%d")

agenda = buscar_agenda_comissao(hoje, semana)
# Exibir em dashboard
```

---

**Versão**: 1.0.0
**Última atualização**: 24/12/2024

---

[↑ Voltar ao README](README.md)
