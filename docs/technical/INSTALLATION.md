# Guía de Instalación y Configuración - MoirAI

## Prerrequisitos Detallados

### Python 3.9+
```bash
# Verificar versión de Python
python --version
# o
python3 --version

# Si necesita instalar Python:
# Ubuntu/Debian
sudo apt update && sudo apt install python3.11 python3.11-venv python3.11-dev

# macOS (con Homebrew)
brew install python@3.11

# Windows
# Descargar desde https://python.org
```

### Git
```bash
# Verificar instalación
git --version

# Instalar si es necesario:
# Ubuntu/Debian
sudo apt install git

# macOS
brew install git

# Windows
# Descargar desde https://git-scm.com
```

## Instalación Paso a Paso

### 1. Clonar y Preparar Proyecto
```bash
# Clonar repositorio
git clone https://github.com/HenrySpark369/MoirAI.git
cd moirai

# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows Command Prompt
.venv\Scripts\activate.bat
```

### 2. Instalar Dependencias del Proyecto

```bash
# ⚠️ IMPORTANTE: Asegúrate de tener el entorno virtual activado
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Actualizar pip para evitar problemas de compatibilidad
pip install --upgrade pip setuptools wheel

# Instalar TODAS las dependencias del proyecto
# El archivo requirements.txt contiene TODAS las dependencias necesarias:
# - Scraping: BeautifulSoup4, lxml, httpx
# - NLP: spaCy, scikit-learn, pandas, numpy
# - Validación: pydantic, email-validator
# - Base de datos: sqlmodel, psycopg2, alembic
pip install -r requirements.txt

# Verificar instalación exitosa
pip list
```

### 3. Configurar spaCy
```bash
# Instalar modelo de inglés (recomendado para términos técnicos)
python -m spacy download en_core_web_sm

# Opcional: modelo de español
python -m spacy download es_core_news_sm

# Verificar instalación
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('spaCy configurado correctamente')"
```

### 4. Configurar Variables de Entorno
```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar archivo .env con su editor preferido
nano .env
# o
code .env
```

### 📌 IMPORTANTE: Generar SECRET_KEY Segura

**⚠️ NUNCA use la SECRET_KEY del archivo .env.example en producción**

#### Métodos para generar SECRET_KEY segura:

**Método 1: Python (Recomendado)**
```bash
# ⚠️ IMPORTANTE: Activar entorno virtual primero
source .venv/bin/activate

# Generar clave segura de 32 bytes (256 bits)
python -c "import secrets; print('SECRET_KEY=\"' + secrets.token_urlsafe(32) + '\"')"

# Ejemplo de salida:
# SECRET_KEY="vJ8kL3nP9qR5sT2wU7xA4bC6eF1gH8iK0mN5pQ9rS2t"
```

**Método 2: OpenSSL**
```bash
# Generar usando OpenSSL
echo "SECRET_KEY=\"$(openssl rand -base64 32)\"" 

# Ejemplo de salida:
# SECRET_KEY="K8mN5pQ9rS2tU7xA4bC6eF1gH8iJ0kL3nP5qR9sT2wV="
```

**Método 3: Script Automatizado (Recomendado para principiantes)**
```bash
# Usar el script incluido que configura todo automáticamente
# El script detecta y usa el entorno virtual automáticamente
./setup_secure.sh
```

**Método 4: Online (Solo para desarrollo)**
```bash
# Generar en https://djecrety.ir/ (Solo para pruebas locales)
# ⚠️ NO usar para producción - generar localmente siempre
```

#### Requisitos de SECRET_KEY:
- **Mínimo 32 caracteres** (256 bits)
- **Aleatoria y única** para cada instalación
- **URL-safe** (sin caracteres especiales problemáticos)
- **Nunca reutilizar** entre entornos (desarrollo/staging/producción)

### Configuración Mínima para Desarrollo (.env)
```env
# Básico
PROJECT_NAME="MoirAI - UNRC Job Matching Platform"

# GENERAR UNA SECRET_KEY SEGURA - Ver sección anterior
SECRET_KEY="CAMBIAR-POR-CLAVE-GENERADA-SECURELY"

# Base de datos (SQLite para desarrollo)
DATABASE_URL="sqlite:///./moirai.db"

# API Keys para desarrollo (generar claves únicas)
ADMIN_API_KEYS=["admin-dev-key-123"]
COMPANY_API_KEYS=["company-dev-key-456"] 
STUDENT_API_KEYS=["student-dev-key-789"]

# CORS para desarrollo
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

### 🔐 Ejemplo de Configuración Segura

```env
# Configuración con SECRET_KEY real generada
PROJECT_NAME="MoirAI - UNRC Job Matching Platform"
SECRET_KEY="vJ8kL3nP9qR5sT2wU7xA4bC6eF1gH8iK0mN5pQ9rS2t"
DATABASE_URL="sqlite:///./moirai.db"

# API Keys únicas para desarrollo
ADMIN_API_KEYS=["admin-dev-a1b2c3d4e5f6"]
COMPANY_API_KEYS=["company-dev-g7h8i9j0k1l2"]
STUDENT_API_KEYS=["student-dev-m3n4o5p6q7r8"]

# Resto de configuración...
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
SPACY_MODEL="en_core_web_sm"
LOG_LEVEL="INFO"
```

## Ejecución de la Aplicación

### Modo Desarrollo
```bash
# Método 1: uvicorn directo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Método 2: Python directo
python -m app.main

# Método 3: Usando el script en main.py
cd app && python main.py
```

### Verificar Instalación
```bash
# Health check
curl http://localhost:8000/health

# Documentación interactiva
# Abrir en navegador: http://localhost:8000/docs
```

## Configuración de Base de Datos

### SQLite (Desarrollo)
No requiere configuración adicional. La base de datos se crea automáticamente.

### PostgreSQL (Producción Recomendada)
```bash
# Instalar PostgreSQL
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql

# Crear base de datos y usuario
sudo -u postgres psql
CREATE DATABASE moirai_db;
CREATE USER moirai_user WITH PASSWORD 'tu_password_seguro';
GRANT ALL PRIVILEGES ON DATABASE moirai_db TO moirai_user;
\q

# Actualizar .env
DATABASE_URL="postgresql://moirai_user:tu_password_seguro@localhost:5432/moirai_db"
```

## Configuración de Proveedores Externos

### JSearch API (RapidAPI)
```bash
# 1. Registrarse en RapidAPI: https://rapidapi.com
# 2. Suscribirse a JSearch API
# 3. Obtener API Key
# 4. Configurar en .env

JSEARCH_API_KEY="tu_rapidapi_key_aqui"
JSEARCH_HOST="jsearch.p.rapidapi.com"
```

## Solución de Problemas Comunes

### Error: "No module named 'app'"
```bash
# Asegurarse de estar en el directorio correcto
pwd  # Debe mostrar .../moirai

# Verificar estructura
ls -la app/

# Reinstalar en modo editable
pip install -e .
```

### Error: "spacy.util.LanguageNotFound"
```bash
# Reinstalar modelo de spaCy
python -m spacy download en_core_web_sm --force

# Verificar modelos instalados
python -m spacy info
```

### Error de Base de Datos
```bash
# Eliminar y recrear base de datos SQLite
rm moirai.db

# Reiniciar aplicación para recrear tablas
uvicorn app.main:app --reload
```

### Error de Permisos
```bash
# Linux/macOS: verificar permisos del directorio
chmod -R 755 .
chown -R $USER:$USER .

# Windows: ejecutar como administrador si es necesario
```

### Error de Puerto en Uso
```bash
# Verificar qué proceso usa el puerto 8000
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Terminar proceso o usar puerto diferente
uvicorn app.main:app --reload --port 8001
```

## Configuración de Desarrollo

### VS Code
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.testing.pytestEnabled": true
}
```

### PyCharm
1. File -> Settings -> Project -> Python Interpreter
2. Seleccionar `.venv/bin/python`
3. Configurar formateador Black
4. Habilitar pytest para testing

## Configuración para Producción

### Variables de Entorno Críticas
```env
# Seguridad
SECRET_KEY="clave-super-segura-generada-aleatoriamente"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Base de datos
DATABASE_URL="postgresql://usuario:password@host:5432/db"

# CORS (solo dominios permitidos)
BACKEND_CORS_ORIGINS=["https://tu-dominio.com"]

# Audit y compliance
ENABLE_AUDIT_LOGGING=true
DATA_RETENTION_DAYS=365
```

### Optimizaciones
```bash
# Usar múltiples workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Con Gunicorn (recomendado para producción)
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Testing de la Configuración

### Test Básico de API
```bash
# Test de health
curl -X GET "http://localhost:8000/health"

# Test con autenticación
curl -X GET "http://localhost:8000/api/v1/students" \
  -H "X-API-Key: student-dev-key-789"
```

### Test de NLP
```python
# tests/test_installation.py
from app.services.nlp_service import nlp_service

def test_nlp_service():
    text = "I have experience with Python, machine learning, and data analysis projects."
    result = nlp_service.analyze_resume(text)
    assert len(result["skills"]) > 0
    assert "python" in [s.lower() for s in result["skills"]]
```

## Próximos Pasos

1. **Verificar documentación**: http://localhost:8000/docs
2. **Subir un currículum de prueba**: Usar endpoint `/api/v1/students/upload_resume`
3. **Explorar API**: Probar diferentes endpoints con las API keys
4. **Configurar monitoreo**: Implementar logging y métricas
5. **Desplegar en producción**: Seguir guía de deployment

## Soporte

Si encuentra problemas durante la instalación:

1. **Verificar logs**: Revisar output de uvicorn
2. **Consultar documentación**: README.md principal
3. **Reportar issues**: GitHub Issues del proyecto
4. **Contacto**: contacto@ing.unrc.edu.mx
