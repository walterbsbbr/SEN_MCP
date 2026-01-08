#!/bin/bash

# Script para iniciar Frontend e Backend simultaneamente

echo "🚀 Iniciando Mini Browser MCP API..."
echo ""

# Diretórios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Função para limpar processos ao sair
cleanup() {
    echo ""
    echo "🛑 Encerrando serviços..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Captura Ctrl+C
trap cleanup INT TERM

# Verifica se os diretórios existem
if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ Diretório backend não encontrado: $BACKEND_DIR"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ Diretório frontend não encontrado: $FRONTEND_DIR"
    exit 1
fi

# Mata processos anteriores nas portas
echo "🧹 Limpando processos anteriores..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null
sleep 1

# Inicia o Backend
echo "🔧 Iniciando Backend (Python FastAPI)..."
cd "$BACKEND_DIR"
python main.py > /tmp/mini-browser-backend.log 2>&1 &
BACKEND_PID=$!
echo "   ✅ Backend iniciado (PID: $BACKEND_PID)"
echo "   📝 Logs: /tmp/mini-browser-backend.log"

# Aguarda o backend iniciar
echo "   ⏳ Aguardando backend inicializar..."
sleep 5

# Verifica se o backend está rodando
if ! ps -p $BACKEND_PID > /dev/null; then
    echo "   ❌ Backend falhou ao iniciar. Verifique os logs:"
    tail -20 /tmp/mini-browser-backend.log
    exit 1
fi

# Inicia o Frontend
echo ""
echo "🎨 Iniciando Frontend (Vite React)..."
cd "$FRONTEND_DIR"

# Verifica se node_modules existe
if [ ! -d "node_modules" ]; then
    echo "   📦 Instalando dependências do frontend..."
    npm install
fi

npm run dev > /tmp/mini-browser-frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   ✅ Frontend iniciado (PID: $FRONTEND_PID)"
echo "   📝 Logs: /tmp/mini-browser-frontend.log"

# Aguarda o frontend iniciar
echo "   ⏳ Aguardando frontend inicializar..."
sleep 3

# Verifica se o frontend está rodando
if ! ps -p $FRONTEND_PID > /dev/null; then
    echo "   ❌ Frontend falhou ao iniciar. Verifique os logs:"
    tail -20 /tmp/mini-browser-frontend.log
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Sistema iniciado com sucesso!"
echo ""
echo "🌐 Frontend:  http://localhost:5173"
echo "🔧 Backend:   http://localhost:8000"
echo "📚 API Docs:  http://localhost:8000/docs"
echo ""
echo "🛠️  Ferramentas MCP disponíveis:"
echo "   - Brasil API (CEP)"
echo "   - RapidAPI (Clima, Tradução, Cripto, etc.)"
echo ""
echo "💡 Dica: Use o seletor Gemini/Groq no frontend"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⌨️  Pressione Ctrl+C para encerrar ambos os serviços"
echo ""

# Monitora logs em tempo real
echo "📊 Monitorando logs (últimas 5 linhas de cada)..."
echo ""

# Função para mostrar logs
show_logs() {
    while true; do
        sleep 5
        echo "--- Backend ($(date +%H:%M:%S)) ---"
        tail -3 /tmp/mini-browser-backend.log 2>/dev/null | grep -v "^$" || echo "Sem novos logs"
        echo ""
        echo "--- Frontend ($(date +%H:%M:%S)) ---"
        tail -3 /tmp/mini-browser-frontend.log 2>/dev/null | grep -v "^$" || echo "Sem novos logs"
        echo ""
    done
}

# Inicia monitoramento de logs em background
show_logs &
MONITOR_PID=$!

# Aguarda indefinidamente
wait $BACKEND_PID $FRONTEND_PID

# Se chegar aqui, algum processo morreu
echo ""
echo "⚠️  Um dos serviços encerrou inesperadamente"
cleanup
