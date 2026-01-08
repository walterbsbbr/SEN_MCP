@echo off
echo 🚀 Iniciando ambiente de desenvolvimento Windows (SenMCP)...

:: 1. Verificacao e Instalacao de Dependencias do Frontend
if not exist "frontend\node_modules" (
    echo 📦 Instalando dependencias do frontend...
    cd frontend
    call npm install
    cd ..
)

:: 2. Inicia o Backend (Porta 8081, Localhost apenas)
echo 🐍 Iniciando Backend (127.0.0.1:8081)...
start "Backend API" cmd /k "python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8081"

:: Pausa para garantir que o backend subiu
timeout /t 4 /nobreak >nul

:: 3. Inicia o Frontend
echo ⚛️  Iniciando Frontend...
cd frontend
start "Frontend Vite" cmd /k "npm run dev"

echo.
echo ✅ Backend e Frontend iniciados.
echo Backend: http://127.0.0.1:8081/api/health
echo Frontend: http://localhost:5173
pause