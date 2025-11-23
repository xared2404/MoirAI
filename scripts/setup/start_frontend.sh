#!/bin/bash
# Quick Start Script for MoirAI Frontend

echo "🚀 MoirAI Frontend - Quick Start"
echo "================================"
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python no encontrado. Por favor instala Python 3.8+"
    exit 1
fi

echo "✅ Python encontrado"

# Check requirements
echo ""
echo "📦 Verificando dependencias..."
if pip show fastapi &> /dev/null; then
    echo "✅ FastAPI instalado"
else
    echo "⚠️  FastAPI no encontrado. Instalando..."
    pip install fastapi uvicorn
fi

# Run verification
echo ""
echo "🔍 Verificando estructura del frontend..."
python verify_frontend.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Verificación exitosa"
    echo ""
    echo "🌐 Iniciando servidor..."
    echo ""
    echo "Accede a: http://localhost:8000"
    echo "Docs API: http://localhost:8000/docs"
    echo ""
    echo "Presiona Ctrl+C para detener el servidor"
    echo ""
    
    # Start the server
    uvicorn app.main:app --reload
else
    echo ""
    echo "❌ Error en la verificación"
    exit 1
fi
