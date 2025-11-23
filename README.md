# 🎓 MoirAI - Plataforma de Vinculación Laboral Universitaria

[![Estado](https://img.shields.io/badge/Estado-MVP%20Listo%20para%20Producción-brightgreen?style=flat-square)](https://github.com/HenrySpark369/MoirAI)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688?style=flat-square)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-336791?style=flat-square)](https://www.postgresql.org/)
[![Licencia](https://img.shields.io/badge/Licencia-Apache%202.0-blue?style=flat-square)](LICENSE)

> **Plataforma inteligente de vinculación laboral que conecta estudiantes universitarios con empresas basándose en competencias inferidas, no solo palabras clave.**

## 🚀 Inicio Rápido

### 1️⃣ Instalación
```bash
# Clonar repositorio
git clone https://github.com/HenrySpark369/MoirAI.git
cd MoirAI

# Configurar entorno
bash scripts/setup/setup_secure.sh

# Instalar dependencias
pip install -r requirements.txt

# Descargar modelos de spaCy (bilingües)
python -m spacy download es_core_news_md
python -m spacy download en_core_web_md
```

### 2️⃣ Configuración de Base de Datos
```bash
# Configurar conexión PostgreSQL en .env
createdb moirai_db

# Ejecutar migraciones
python manage.py db upgrade

# Cargar datos de prueba (opcional)
python scripts/utilities/load_sample_data.py
```

### 3️⃣ Iniciar Servicios
```bash
# Backend (FastAPI)
python main.py

# Frontend (terminal separada)
bash scripts/setup/start_frontend.sh
```

**Backend:** http://localhost:8000  
**Frontend:** http://localhost:5173  
**Docs API:** http://localhost:8000/docs

---

## 📋 Características

### ✅ Características Principales (MVP)
- 🧠 **Emparejamiento Inteligente** - NLP con spaCy para coincidencia semántica entre empleos y habilidades
- 📄 **Análisis de CV** - Extracción automática de competencias desde CVs (NER + análisis de dependencias)
- 🔐 **Autenticación Segura** - Tokens JWT + API keys para integraciones
- 👥 **Control de Acceso por Rol** - Estudiantes, Empresas, Administradores con permisos diferenciados
- 📊 **Panel de Administración** - KPIs en tiempo real, métricas de emparejamiento, gestión de usuarios
- 🌐 **Soporte Bilingüe** - Análisis de CVs en Español e Inglés
- 📝 **Auditoría de Acciones** - Rastreo de todas las acciones de usuarios para cumplimiento normativo
- 🔍 **Web Scraping de Empleos** - Integración con OCC.com.mx para publicaciones de empleos

### 🔄 Trabajo Actual (En Progreso)
- Optimización de rendimiento (Redis cache, índices DB)
- Mejoras del panel de administración
- Notificaciones por correo
- App móvil (React Native)

### 🎯 Roadmap Futuro
Ver [ROADMAP.md](ROADMAP.md) para cronograma detallado y oportunidades

---

## 📂 Estructura del Proyecto

```
MoirAI/
├── app/                          # Aplicación principal
│   ├── api/                      # Rutas de FastAPI
│   │   ├── endpoints/
│   │   │   ├── students.py       # Operaciones de estudiantes
│   │   │   ├── companies.py      # Operaciones de empresas
│   │   │   ├── admin.py          # Operaciones admin + auditoría
│   │   │   └── matching.py       # Motor de emparejamiento
│   │   └── middleware/           # Autenticación, CORS, etc
│   ├── core/                     # Configuraciones principales
│   │   ├── config.py             # Configuración de entorno
│   │   ├── database.py           # PostgreSQL asincrónico
│   │   └── security.py           # JWT, hash de contraseñas
│   ├── services/                 # Lógica de negocio
│   │   ├── cv_extractor.py       # Análisis de CV con spaCy (v2)
│   │   ├── matcher.py            # Algoritmo de emparejamiento
│   │   └── nlp_service.py        # Utilidades de NLP
│   ├── models/                   # Definiciones de SQLModel
│   ├── schemas/                  # Esquemas de Pydantic
│   └── static/                   # Archivos del frontend
│
├── tests/                         # Suite de pruebas
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/                          # Documentación
│   ├── user-guide/
│   │   └── USER_GUIDE.md          # Documentación completa del usuario
│   ├── technical/
│   │   ├── DATABASE_SETUP.md
│   │   ├── EXECUTION_GUIDE.md
│   │   ├── SPACY_CACHE_GUIDE.md
│   │   └── ...
│   └── developer-notes/           # Scripts de análisis
│
├── scripts/                       # Scripts de utilidad
│   ├── setup/                    # Inicialización
│   ├── testing/                  # Ejecutores de pruebas
│   └── utilities/                # Admin, NLP, seguridad
│
├── main.py                        # Punto de entrada de la aplicación
├── requirements.txt               # Dependencias de Python
├── ROADMAP.md                     # Roadmap de desarrollo
└── README.md                      # Este archivo
```

---

## 🔧 Referencia de API

### Autenticación
```bash
# Registrarse como estudiante
POST /api/v1/auth/register/student
Content-Type: application/json
{
  "email": "estudiante@universidad.edu",
  "password": "contraseña_segura",
  "full_name": "Juan Pérez"
}

# Iniciar sesión
POST /api/v1/auth/login
Content-Type: application/json
{
  "email": "estudiante@universidad.edu",
  "password": "contraseña_segura"
}
# Respuesta: { "access_token": "...", "token_type": "bearer" }
```

### Operaciones de Estudiante
```bash
# Cargar CV
POST /api/v1/students/profile/upload-cv
Authorization: Bearer <token>
Content-Type: multipart/form-data
Files: cv_file=@ruta/a/cv.pdf

# Obtener perfil de estudiante
GET /api/v1/students/profile
Authorization: Bearer <token>

# Obtener coincidencias de empleos
GET /api/v1/students/matches?limit=10
Authorization: Bearer <token>
```

### Operaciones de Empresa
```bash
# Publicar oferta de empleo
POST /api/v1/companies/jobs
Authorization: Bearer <token>
Content-Type: application/json
{
  "title": "Ingeniero de Software Senior",
  "description": "...",
  "location": "Ciudad de México",
  "salary_min": 80000,
  "salary_max": 120000,
  "required_skills": ["Python", "FastAPI"]
}

# Ver candidatos
GET /api/v1/companies/candidates
Authorization: Bearer <token>
```

### Operaciones de Administrador
```bash
# Obtener KPIs
GET /api/v1/admin/kpis
Authorization: Bearer <admin-token>

# Ver registros de auditoría
GET /api/v1/admin/audit-logs
Authorization: Bearer <admin-token>

# Gestionar usuarios
GET /api/v1/admin/users
Authorization: Bearer <admin-token>
```

**Documentación completa de API:** http://localhost:8000/docs (UI interactivo de Swagger)

---

## 🧠 Cómo Funciona el Emparejamiento

### 1. Análisis de CV
- Cargar CV en PDF/DOCX
- spaCy NER extrae: habilidades, experiencia, educación
- Análisis de dependencias infiere habilidades blandas (liderazgo, adaptabilidad)
- Crear perfil estructurado en formato Harvard

### 2. Análisis de Oferta de Empleo
- Procesar descripción de oferta para extraer habilidades requeridas
- Normalizar habilidades y codificar semánticamente

### 3. Emparejamiento Semántico
- Cada par estudiante-oferta obtiene puntuación de coincidencia (0-100%)
- La puntuación considera:
  - Coincidencias directas de habilidades (70% peso)
  - Similitud semántica (20% peso)
  - Inferencia de habilidades blandas (10% peso)
- Resultados ordenados por puntuación

### 4. Recomendaciones
- Estudiantes ven los 10 empleos con mejor coincidencia
- Empresas ven los mejores candidatos para cada oferta

---

## 🔐 Seguridad

### Características
- ✅ Autenticación basada en tokens JWT
- ✅ Hash de contraseñas (bcrypt)
- ✅ Protección CORS
- ✅ Prevención de inyección SQL (SQLModel)
- ✅ Limitación de velocidad (en progreso)
- ✅ Auditoría de todas las acciones

### Ejecutar Verificaciones de Seguridad
```bash
bash scripts/utilities/security_check.sh
```

### Variables de Entorno
Crear archivo `.env`:
```env
# Base de Datos
DATABASE_URL=postgresql+asyncpg://usuario:contraseña@localhost/moirai_db

# Seguridad
SECRET_KEY=tu_clave_secreta_aqui (generar con: openssl rand -hex 32)
ALGORITHM=HS256

# Frontend
VITE_API_URL=http://localhost:8000

# Correo (opcional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_correo@gmail.com
SMTP_PASSWORD=tu_contraseña_app
```

---

## 🧪 Pruebas

### Ejecutar Todas las Pruebas
```bash
pytest tests/ -v
```

### Ejecutar Suite Específica de Pruebas
```bash
# Pruebas unitarias
pytest tests/unit/ -v

# Pruebas de integración
pytest tests/integration/ -v

# Pruebas de NLP
bash scripts/testing/run_nlp_tests.sh
```

### Cobertura de Pruebas
```bash
pytest tests/ --cov=app --cov-report=html
# Abrir htmlcov/index.html
```

---

## 📊 Esquema de Base de Datos

### Tablas Principales
- **users** - Cuentas de estudiantes, empresas, administradores
- **profiles** - Perfiles detallados de estudiantes (formato Harvard)
- **jobs** - Publicaciones de empleos de empresas
- **matches** - Puntuaciones de emparejamiento estudiante-oferta
- **audit_logs** - Rastreo de acciones para cumplimiento

Para esquema detallado: [DATABASE_SETUP.md](docs/technical/DATABASE_SETUP.md)

---

## 🚀 Despliegue

### Despliegue con Docker
```bash
# Construir imagen
docker build -t moirai:latest .

# Ejecutar contenedor
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e SECRET_KEY=... \
  moirai:latest
```

### Docker Compose
```bash
docker-compose up -d
```

### Checklist de Producción
- [ ] Establecer `SECRET_KEY` fuerte
- [ ] Habilitar HTTPS/SSL
- [ ] Configurar copia de seguridad de PostgreSQL
- [ ] Configurar monitoreo/logging
- [ ] Habilitar limitación de velocidad
- [ ] Configurar reglas de firewall

---

## 📚 Documentación

| Documento | Propósito |
|-----------|-----------|
| [USER_GUIDE.md](docs/user-guide/USER_GUIDE.md) | Guía completa para estudiantes, empresas, admins |
| [ROADMAP.md](ROADMAP.md) | Cronograma de desarrollo y oportunidades |
| [DATABASE_SETUP.md](docs/technical/DATABASE_SETUP.md) | Esquema de BD y migraciones |
| [SPACY_CACHE_GUIDE.md](docs/technical/SPACY_CACHE_GUIDE.md) | Configuración de NLP y caché |
| [EXECUTION_GUIDE.md](docs/technical/EXECUTION_GUIDE.md) | Instrucciones detalladas de instalación |

---

## ❓ Preguntas Frecuentes

**P: ¿Cómo restablezco mi contraseña?**  
R: Haz clic en "Olvidé mi contraseña" en la página de inicio de sesión. Se enviará un enlace a tu correo.

**P: ¿Puedo usar mi propio portal de empleos?**  
R: ¡Sí! Ve la documentación de integración en [ROADMAP.md](ROADMAP.md#integraciones-externas)

**P: ¿Qué tan preciso es el análisis de CV?**  
R: ~95% de precisión en CVs estándar. Mejores resultados con formato Harvard.

**P: ¿Puedo exportar mis datos?**  
R: Sí. Configuración de cuenta → Descargar mis datos (JSON/CSV)

**P: ¿Qué hago si encuentro un error?**  
R: Reporta en [GitHub Issues](https://github.com/HenrySpark369/MoirAI/issues)

---

## 🤝 Contribuciones

¡Aceptamos contribuciones! Por favor:

1. Fork el repositorio
2. Crear rama de características: `git checkout -b feature/tu-caracteristica`
3. Hacer commit de cambios: `git commit -m "Agregar tu característica"`
4. Push a la rama: `git push origin feature/tu-caracteristica`
5. Abrir Pull Request

Ver [ROADMAP.md](ROADMAP.md) para oportunidades próximas.

---

## 📊 Estado del Proyecto

### Fase Actual
🟢 **MVP Listo para Producción** (21 de Noviembre de 2025)

### Completado
- ✅ API Backend (FastAPI + PostgreSQL asincrónico)
- ✅ Análisis de CV (spaCy NER + análisis de dependencias)
- ✅ Algoritmo de Emparejamiento (puntuación semántica)
- ✅ Frontend (Vanilla JS responsivo)
- ✅ Autenticación (JWT + API keys)
- ✅ Panel de Admin (KPIs + registros de auditoría)

### En Progreso
- ⏳ Optimización de rendimiento
- ⏳ Mejoras del UI de administración
- ⏳ Notificaciones por correo

### Planificado
- 📋 Modelos ML de ranking
- 📋 App móvil (React Native)
- 📋 Integraciones externas (LinkedIn, Indeed)

---

## 📞 Soporte

- 📖 **Documentación**: [docs/](docs/)
- 🐛 **Reportar Error**: [GitHub Issues](https://github.com/HenrySpark369/MoirAI/issues)
- 💬 **Discusiones**: [GitHub Discussions](https://github.com/HenrySpark369/MoirAI/discussions)
- 📧 **Correo**: support@moirai.dev

---

## 📜 Licencia

Licencia Apache 2.0 - ver archivo [LICENSE](LICENSE)

---

## 👥 Equipo

**Líder del Proyecto**: Henry Spark  
**Contribuidores**: Ver [GitHub Contributors](https://github.com/HenrySpark369/MoirAI/graphs/contributors)

---

## 🙏 Agradecimientos

- **spaCy** - Librería NLP para análisis de CVs
- **FastAPI** - Framework web moderno para Python
- **SQLModel** - ORM de base de datos SQL
- **PostgreSQL** - Motor de base de datos robusto

---

**Última Actualización**: 21 de Noviembre de 2025  
**Rama**: feature/frontend-mvp  
**Versión**: 1.0.0-MVP
