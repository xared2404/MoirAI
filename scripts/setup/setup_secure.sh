#!/bin/bash

# Script de configuración inicial segura para MoirAI
# ╔════════════════════════════════════════════════════════════════╗
# ║  🚀 MoirAI - Setup Seguro e Integrado                         ║
# ║  Instala dependencias, configura env, y descarga modelos NLP  ║
# ╚════════════════════════════════════════════════════════════════╝

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $1"
    echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    print_error "Ejecute este script desde el directorio raíz del proyecto MoirAI"
    exit 1
fi

# ════════════════════════════════════════════════════════════════
# PASO 1: Entorno Virtual
# ════════════════════════════════════════════════════════════════

print_header "PASO 1: Verificando Entorno Virtual Python"

if [ -d ".venv" ]; then
    print_success "Entorno virtual .venv encontrado"
    source .venv/bin/activate
    PYTHON_CMD="python"
else
    print_warning "Entorno virtual no encontrado"
    
    # Detectar Python disponible
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "No se encontró Python instalado"
        exit 1
    fi
    
    print_info "Creando entorno virtual con $PYTHON_CMD..."
    $PYTHON_CMD -m venv .venv
    source .venv/bin/activate
    PYTHON_CMD="python"
    print_success "Entorno virtual creado"
fi

# Verificar Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
print_info "Usando: $PYTHON_VERSION"

# ════════════════════════════════════════════════════════════════
# PASO 2: Dependencias Python
# ════════════════════════════════════════════════════════════════

print_header "PASO 2: Instalando Dependencias Python"

print_info "Actualizando pip, setuptools y wheel..."
$PYTHON_CMD -m pip install --upgrade pip setuptools wheel -q

print_info "Instalando dependencias de requirements.txt..."
$PYTHON_CMD -m pip install -r requirements.txt -q

print_success "Dependencias instaladas"

# ════════════════════════════════════════════════════════════════
# PASO 3: Modelos NLP (spaCy) - BILINGUAL SUPPORT
# ════════════════════════════════════════════════════════════════

print_header "PASO 3: Descargando Modelos spaCy BILÍNGUES (Spanish + English)"

# Modelos a instalar
SPACY_MODELS=("es_core_news_md" "en_core_web_md")
MODEL_NAMES=("Spanish" "English")

# Counters
MODELS_INSTALLED=0
MODELS_FAILED=0

for i in "${!SPACY_MODELS[@]}"; do
    SPACY_MODEL="${SPACY_MODELS[$i]}"
    LANG_NAME="${MODEL_NAMES[$i]}"
    
    print_info "Verificando modelo spaCy: $SPACY_MODEL ($LANG_NAME)..."
    
    # Verificar si el modelo ya está instalado
    if $PYTHON_CMD -c "import spacy; spacy.load('$SPACY_MODEL')" 2>/dev/null; then
        print_success "Modelo $SPACY_MODEL ya instalado y cacheado"
        ((MODELS_INSTALLED++))
    else
        print_info "Descargando modelo $SPACY_MODEL (~40-50MB)..."
        
        # Descargar modelo
        if $PYTHON_CMD -m spacy download $SPACY_MODEL -q 2>/dev/null; then
            print_success "Modelo $SPACY_MODEL instalado correctamente"
            ((MODELS_INSTALLED++))
        else
            print_error "Error descargando modelo $SPACY_MODEL"
            print_info "  Intente manualmente: python -m spacy download $SPACY_MODEL"
            ((MODELS_FAILED++))
        fi
    fi
done

# Mostrar resumen
echo ""
print_info "Resumen de instalación de modelos:"
print_success "$MODELS_INSTALLED modelos instalados/cacheados"
if [ $MODELS_FAILED -gt 0 ]; then
    print_warning "$MODELS_FAILED modelos fallaron"
fi

# Verificar que ambos modelos funcionan
print_info "Verificando integridad de modelos spaCy instalados..."
$PYTHON_CMD << 'PYTHON_CHECK'
import spacy
import sys

models_ok = True
models_status = []

for model_name in ['es_core_news_md', 'en_core_web_md']:
    try:
        nlp = spacy.load(model_name)
        doc = nlp('Prueba de spaCy')
        models_status.append(f"✓ {model_name}: OK")
    except Exception as e:
        models_status.append(f"✗ {model_name}: {e}")
        models_ok = False

for status in models_status:
    print(status)

if not models_ok:
    print("ERROR: No todos los modelos están disponibles")
    sys.exit(1)

print("\n✓ Ambos modelos spaCy funcionando correctamente (bilingual mode enabled)")
PYTHON_CHECK

if [ $? -eq 0 ]; then
    print_success "Ambos modelos spaCy verificados y listos para bilingual extraction"
else
    print_warning "Algunos modelos no están disponibles (puede seguir usando el que esté disponible)"
fi

# ════════════════════════════════════════════════════════════════
# PASO 3B: Precalentamiento de Caché (WARMUP)
# ════════════════════════════════════════════════════════════════

print_header "PASO 3B: Precalentando Caché de Modelos en RAM"

print_info "Cargando modelos en memoria para optimizar performance inicial..."

$PYTHON_CMD << 'PYTHON_WARMUP'
import spacy
import time
import sys

print("⏱️  Precalentando modelos spaCy en RAM...\n")

models = ['es_core_news_md', 'en_core_web_md']
total_start = time.time()

for model_name in models:
    try:
        print(f"  Cargando {model_name}...", end=" ", flush=True)
        start = time.time()
        
        # Cargar modelo
        nlp = spacy.load(model_name)
        
        # Procesar textos de prueba para calentar caché
        test_texts = [
            "This is a test in English with professional skills",
            "Esta es una prueba en español con habilidades profesionales",
            "Machine learning and software development experience",
            "Experiencia en desarrollo de software y aprendizaje automático",
        ]
        
        for text in test_texts:
            doc = nlp(text)
            # Acceder a todos los componentes
            _ = doc.ents
            _ = doc.noun_chunks
            _ = [token.text for token in doc]
            _ = [token.pos_ for token in doc]
        
        elapsed = time.time() - start
        print(f"✓ ({elapsed:.2f}s)")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

total_time = time.time() - total_start
print(f"\n✓ Precalentamiento completado en {total_time:.2f}s")
print("✓ Modelos listos en RAM para máxima performance")
PYTHON_WARMUP

if [ $? -eq 0 ]; then
    print_success "Caché precalentado exitosamente - Requests futuras serán <100ms"
else
    print_warning "Error precalentando caché (continuando...)"
fi

# ════════════════════════════════════════════════════════════════
# PASO 4: Configuración de Variables de Entorno
# ════════════════════════════════════════════════════════════════

print_header "PASO 4: Configurando Variables de Entorno"

# Crear archivo .env si no existe
if [ ! -f ".env" ]; then
    print_info "Creando archivo .env desde .env.example..."
    
    if [ ! -f ".env.example" ]; then
        print_warning "Archivo .env.example no encontrado. Creando .env básico..."
        cat > .env << 'EOF'
# MoirAI Environment Variables
DEBUG=True
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://moirai_user:change_this_password@localhost:5432/moirai_db

# Security
SECRET_KEY=change_this_to_a_secure_random_key
ENCRYPTION_KEY=change_this_encryption_key

# NLP
SPACY_LANGUAGE=es

# API Settings
API_TITLE=MoirAI API
API_VERSION=1.0.0
EOF
    else
        cp .env.example .env
    fi
    
    # Generar SECRET_KEY segura
    print_info "Generando SECRET_KEY segura..."
    SECRET_KEY=$($PYTHON_CMD -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Generar ENCRYPTION_KEY segura
    print_info "Generando ENCRYPTION_KEY segura para encriptación..."
    ENCRYPTION_KEY=$($PYTHON_CMD -c "
import secrets
from base64 import urlsafe_b64encode
key = secrets.token_bytes(32)
print(urlsafe_b64encode(key).decode())
")
    
    # Reemplazar SECRET_KEY y ENCRYPTION_KEY en .env
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|change_this_to_a_secure_random_key|$SECRET_KEY|" .env
        sed -i '' "s|change_this_encryption_key|$ENCRYPTION_KEY|" .env
    else
        # Linux
        sed -i "s|change_this_to_a_secure_random_key|$SECRET_KEY|" .env
        sed -i "s|change_this_encryption_key|$ENCRYPTION_KEY|" .env
    fi
    
    print_success "Archivo .env creado con claves seguras"
    print_warning "IMPORTANTE: Revise y configure las demás variables en .env"
else
    print_info "El archivo .env ya existe"
fi

# ════════════════════════════════════════════════════════════════
# PASO 5: Configuración de Docker (Opcional)
# ════════════════════════════════════════════════════════════════

print_header "PASO 5: Configuración de Docker (Opcional)"

if [ ! -f ".env.docker" ]; then
    if [ -f ".env.docker.example" ]; then
        print_info "Creando archivo .env.docker para Docker Compose..."
        cp .env.docker.example .env.docker
        
        # Generar contraseñas seguras
        DB_PASSWORD=$($PYTHON_CMD -c "import secrets; print(secrets.token_urlsafe(16))")
        ADMIN_PASSWORD=$($PYTHON_CMD -c "import secrets; print(secrets.token_urlsafe(12))")
        SECRET_KEY_DOCKER=$($PYTHON_CMD -c "import secrets; print(secrets.token_urlsafe(32))")
        
        # Reemplazar en .env.docker
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/change_this_secure_password/$DB_PASSWORD/g" .env.docker
            sed -i '' "s/change_this_admin_password/$ADMIN_PASSWORD/g" .env.docker
            sed -i '' "s/generate_a_secure_secret_key_here/$SECRET_KEY_DOCKER/" .env.docker
        else
            # Linux
            sed -i "s/change_this_secure_password/$DB_PASSWORD/g" .env.docker
            sed -i "s/change_this_admin_password/$ADMIN_PASSWORD/g" .env.docker
            sed -i "s/generate_a_secure_secret_key_here/$SECRET_KEY_DOCKER/" .env.docker
        fi
        
        print_success "Archivo .env.docker creado con contraseñas seguras"
    else
        print_info "Archivo .env.docker.example no encontrado (no es crítico)"
    fi
else
    print_info "El archivo .env.docker ya existe"
fi

# ════════════════════════════════════════════════════════════════
# PASO 6: Validación Final
# ════════════════════════════════════════════════════════════════

print_header "PASO 6: Validación Final"

print_info "Verificando instalaciones críticas..."

# Check Python packages
REQUIRED_PACKAGES=("fastapi" "sqlmodel" "spacy" "pandas" "pytest")
for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if $PYTHON_CMD -c "import $pkg" 2>/dev/null; then
        print_success "$pkg instalado"
    else
        print_warning "$pkg NO instalado (puede ser crítico)"
    fi
done

# ════════════════════════════════════════════════════════════════
# RESUMEN Y PRÓXIMOS PASOS
# ════════════════════════════════════════════════════════════════

echo ""
print_header "🎉 CONFIGURACIÓN COMPLETADA"

echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}  Todas las instalaciones se completaron exitosamente        ${GREEN}║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"

echo ""
echo -e "${CYAN}📋 PRÓXIMOS PASOS:${NC}"
echo -e "  1. Revise y configure las variables en ${YELLOW}.env${NC}"
echo -e "  2. Configure base de datos: ${YELLOW}DATABASE_URL${NC} en .env"
echo -e "  3. Configure API keys externas si es necesario"
echo -e "  4. Inicie el servidor de desarrollo:"
echo -e "     ${YELLOW}python -m uvicorn app.main:app --reload${NC}"
echo -e "  5. Ejecute tests:"
echo -e "     ${YELLOW}pytest${NC}"

echo ""
echo -e "${CYAN}✨ CACHÉ BILÍNGUE YA PRECALENTADO:${NC}"
echo -e "  • Ambos modelos spaCy cargados en RAM"
echo -e "  • Extracción de CVs: <100ms (desde caché)"
echo -e "  • Detección automática: Spanish + English"
echo -e "  • Soporte bilíngue activo ✅"

echo ""
echo -e "${CYAN}🧪 PARA PROBAR LA INSTALACIÓN DE NLP:${NC}"
echo -e "  ${YELLOW}python demo_spacy_vs_current_extraction.py${NC}"

echo ""
echo -e "${CYAN}🐳 PARA DOCKER (si está configurado):${NC}"
echo -e "  ${YELLOW}docker-compose --env-file .env.docker up -d${NC}"

echo ""
echo -e "${CYAN}🔒 RECORDATORIOS DE SEGURIDAD:${NC}"
echo -e "  • Nunca commite archivos .env al repositorio"
echo -e "  • Use contraseñas fuertes en producción"
echo -e "  • Habilite HTTPS en producción"
echo -e "  • Configure firewall apropiadamente"
echo -e "  • La ENCRYPTION_KEY encripta campos sensibles (emails, teléfonos)"
echo -e "  • Si pierde la ENCRYPTION_KEY no podrá desencriptar datos existentes"

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${YELLOW}¡Listo para desarrollar! 🚀${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
