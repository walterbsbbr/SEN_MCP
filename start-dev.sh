#!/bin/bash

# Função para encerrar processos filhos ao fechar o script (Ctrl+C)
cleanup() {
    echo ""
    echo "🛑 Encerrando servidores..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit
}

# Captura sinal de interrupção (SIGINT)
trap cleanup SIGINT

echo "🚀 Iniciando ambiente de desenvolvimento (SenMCP)..."

# 1. Iniciar Backend (FastAPI) na porta 8000
# Executa a partir da raiz para garantir que os imports funcionem
echo "🐍 Iniciando Backend..."
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Aguarda alguns segundos para o backend subir
sleep 2

# 2. Iniciar Frontend (Vite)
# O Vite usará o proxy configurado no vite.config.js para falar com a porta 8000
echo "⚛️  Iniciando Frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!

# Mantém o script rodando para segurar os processos
wait