@echo off
REM Quick Start Script for MoirAI Frontend (Windows)

echo.
echo 🚀 MoirAI Frontend - Quick Start
echo ================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python no encontrado. Por favor instala Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python encontrado

REM Check FastAPI
echo.
echo 📦 Verificando dependencias...
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  FastAPI no encontrado. Instalando...
    pip install fastapi uvicorn
) else (
    echo ✅ FastAPI instalado
)

REM Run verification
echo.
echo 🔍 Verificando estructura del frontend...
python verify_frontend.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Error en la verificación
    pause
    exit /b 1
)

echo.
echo ✅ Verificación exitosa
echo.
echo 🌐 Iniciando servidor...
echo.
echo Accede a: http://localhost:8000
echo Docs API: http://localhost:8000/docs
echo.
echo Presiona Ctrl+C para detener el servidor
echo.

REM Start the server
uvicorn app.main:app --reload

pause
