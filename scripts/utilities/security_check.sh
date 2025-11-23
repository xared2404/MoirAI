#!/bin/bash

# Script de verificación de seguridad antes de commit
# Ejecutar antes de hacer push al repositorio remoto

echo "🔍 Verificando seguridad del proyecto antes del commit..."

ISSUES_FOUND=0

# Verificar archivos sensibles
echo "📁 Verificando archivos sensibles..."

# Buscar archivos .env (excepto .example)
ENV_FILES=$(find . -name ".env" -not -name "*.example" -not -path "./.venv/*" 2>/dev/null)
if [ ! -z "$ENV_FILES" ]; then
    echo "❌ ALERTA: Archivos .env encontrados:"
    echo "$ENV_FILES"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo "✅ No se encontraron archivos .env"
fi

# Buscar archivos de base de datos
DB_FILES=$(find . -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" 2>/dev/null)
if [ ! -z "$DB_FILES" ]; then
    echo "❌ ALERTA: Archivos de base de datos encontrados:"
    echo "$DB_FILES"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo "✅ No se encontraron archivos de base de datos"
fi

# Buscar archivos de log
LOG_FILES=$(find . -name "*.log" 2>/dev/null)
if [ ! -z "$LOG_FILES" ]; then
    echo "❌ ALERTA: Archivos de log encontrados:"
    echo "$LOG_FILES"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo "✅ No se encontraron archivos de log"
fi

# Buscar claves hardcodeadas en archivos Python
echo "🔑 Verificando claves hardcodeadas..."
HARDCODED_SECRETS=$(grep -r -i --include="*.py" --include="*.yml" --include="*.yaml" \
    -E "(password|secret|key).*=.*['\"][^'\"]*['\"]" . \
    | grep -v ".example" \
    | grep -v "example" \
    | grep -v "placeholder" \
    | grep -v "your-" \
    | grep -v "change" \
    | grep -v "#" \
    2>/dev/null)

if [ ! -z "$HARDCODED_SECRETS" ]; then
    echo "⚠️  Posibles credenciales hardcodeadas encontradas:"
    echo "$HARDCODED_SECRETS"
    echo "ℹ️  Verifique que no son credenciales reales"
else
    echo "✅ No se encontraron credenciales hardcodeadas obvias"
fi

# Verificar .gitignore
echo "📝 Verificando .gitignore..."
if [ -f ".gitignore" ]; then
    if grep -q "\.env" .gitignore; then
        echo "✅ .env está en .gitignore"
    else
        echo "❌ ALERTA: .env no está en .gitignore"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
    
    if grep -q "\.db" .gitignore || grep -q "\.sqlite" .gitignore; then
        echo "✅ Archivos de base de datos están en .gitignore"
    else
        echo "❌ ALERTA: Archivos de base de datos no están en .gitignore"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
else
    echo "❌ ALERTA: No se encontró archivo .gitignore"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

# Verificar que existen archivos de ejemplo
echo "📋 Verificando archivos de ejemplo..."
if [ -f ".env.example" ]; then
    echo "✅ .env.example existe"
else
    echo "⚠️  .env.example no encontrado"
fi

if [ -f ".env.docker.example" ]; then
    echo "✅ .env.docker.example existe"
else
    echo "⚠️  .env.docker.example no encontrado"
fi

# Resultado final
echo ""
echo "═══════════════════════════════════════"
if [ $ISSUES_FOUND -eq 0 ]; then
    echo "🎉 ¡VERIFICACIÓN EXITOSA!"
    echo "✅ El proyecto está listo para subir al repositorio remoto"
    echo ""
    echo "📝 Recordatorio final:"
    echo "- Asegúrese de configurar GitHub Secrets para CI/CD"
    echo "- Configure Dependabot para actualizaciones de seguridad"
    echo "- Habilite branch protection rules"
    exit 0
else
    echo "❌ VERIFICACIÓN FALLIDA"
    echo "🚨 Se encontraron $ISSUES_FOUND problemas de seguridad"
    echo "Por favor, corrija los problemas antes de hacer commit"
    exit 1
fi
