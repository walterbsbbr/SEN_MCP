#!/bin/bash

# Script para parar todos os serviços

echo "🛑 Encerrando Mini Browser MCP API..."

# Mata processos nas portas
echo "   Parando Backend (porta 8000)..."
lsof -ti:8000 | xargs kill -9 2>/dev/null

echo "   Parando Frontend (porta 5173)..."
lsof -ti:5173 | xargs kill -9 2>/dev/null

# Limpa logs
rm -f /tmp/mini-browser-backend.log
rm -f /tmp/mini-browser-frontend.log

echo ""
echo "✅ Todos os serviços foram encerrados"
