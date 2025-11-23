# Sistema de Scraping y Seguimiento de Empleos OCC.com.mx

## Descripción General

Este módulo implementa un sistema completo de scraping y seguimiento de ofertas de empleo del portal OCC.com.mx, proporcionando funcionalidades de búsqueda automatizada, aplicación tracking y alertas personalizadas para estudiantes de la UNRC.

## Arquitectura del Sistema

### Componentes Principales

#### 1. **OCCScraper Service** (`app/services/occ_scraper_service.py`)
- Scraper asíncrono para OCC.com.mx
- Manejo de rate limiting y headers anti-detección
- **Extracción detallada de 25+ campos** desde el contenedor `job-detail-container`
- Soporte para búsquedas filtradas y paginación
- Análisis inteligente de información oculta en inputs HTML y JSON

#### 2. **Job Application Manager** (`app/services/job_application_service.py`)
- Gestión de aplicaciones de empleo
- Seguimiento de estados de aplicaciones
- Estadísticas de éxito y métricas de usuario
- Sistema de alertas automáticas

#### 3. **Database Models** (`app/models/job_scraping.py`)
- `JobOfferDB`: Ofertas de trabajo scraped
- `JobApplicationDB`: Aplicaciones de usuarios
- `SearchQueryDB`: Historial de búsquedas
- `UserJobAlertDB`: Alertas personalizadas
- `ScrapingLogDB`: Auditoría de operaciones

#### 4. **API Endpoints** (`app/api/endpoints/job_scraping_api.py`)
- RESTful API para todas las operaciones
- Autenticación y autorización
- Validación de datos con Pydantic
- Manejo de errores y logging

## Funcionalidades

### 🔍 Búsqueda y Extracción de Empleos

#### Búsqueda Simple
```bash
POST /job-scraping/search
```
- Búsqueda por palabra clave, ubicación, salario
- Filtros por modalidad de trabajo, experiencia requerida
- Resultados paginados y ordenación personalizada

#### Extracción Detallada de Empleo
```bash
GET /job-scraping/job/{job_id}
```

**Respuesta estructurada con:**
```json
{
  "job_details": {
    "job_id": "occ_20806805",
    "title": "Becario Data Science",
    "company": "Empresa confidencial",
    "location": "Ciudad de México",
    "salary": "$8,000 Mensual",
    "category": "Tecnologías de la Información - Sistemas",
    "subcategory": "Redes - Telecomunicaciones",
    "education_required": "Universitario sin título",
    "job_type": "Medio tiempo",
    "work_mode": "Presencial",
    "work_schedule": "Tiempo parcial",
    "benefits": ["Prestaciones de ley", "Plan de carrera"],
    "full_description": "Descripción completa del empleo...",
    "requirements": ["Requisito 1", "Requisito 2"],
    "activities": ["Actividad 1", "Actividad 2"],
    "soft_skills": ["Comunicación", "Trabajo en equipo"],
    "skills": ["R", "SQL", "Python"],
    "is_featured": true,
    "is_new": false,
    "share_url": "https://occ.com.mx/share/..."
  },
  "extraction_quality": {
    "has_title": true,
    "has_company": true,
    "has_salary": true,
    "has_benefits": true,
    "has_category": true,
    "has_description": true,
    "has_skills": true,
    "completeness_score": 85.7
  },
  "available_sections": {
    "basic_info": true,
    "requirements": true,
    "benefits": true,
    "skills": true,
    "contact_info": true
  },
  "recommendations": [
    "Empresa confidencial - Considera preguntar sobre la empresa en entrevista",
    "Considera adquirir experiencia en R si no tienes"
  ],
  "success": true
}
```

**Campos extraídos (25+):**
- **Información básica**: Título, Empresa, Ubicación, Salario, Fecha
- **Categorización**: Categoría, Subcategoría, Tipo de contrato
- **Requisitos laborales**: Educación, Experiencia, Modalidad, Horario
- **Contenido detallado**: Descripción completa, Requisitos, Actividades, Soft skills
- **Habilidades técnicas**: Lista de tecnologías requeridas
- **Beneficios**: Plan de carrera, Prestaciones, Capacitación
- **Contacto**: Nombre, Teléfono, Email (cuando está disponible)
- **Metadata**: Share URL, Featured status, Estado "Nuevo"

### 📋 Gestión de Aplicaciones
```bash
POST /job-scraping/apply
PUT /job-scraping/application/{id}/status
GET /job-scraping/applications
GET /job-scraping/applications/stats
```
- Registro de aplicaciones a empleos
- Seguimiento de estados (aplicado, entrevista, rechazado, aceptado)
- Estadísticas personales de éxito
- Notas y URLs de aplicación externa

### 🔔 Sistema de Alertas
```bash
POST /job-scraping/alerts
GET /job-scraping/alerts
DELETE /job-scraping/alerts/{id}
```
- Alertas automáticas por palabras clave
- Frecuencia configurable (diaria, semanal)
- Filtros por ubicación y salario mínimo
- Procesamiento batch para notificaciones

### 📊 Analytics y Tendencias
```bash
GET /job-scraping/trending-jobs
GET /job-scraping/search-history
```
- Empleos en tendencia por búsquedas populares
- Historial personal de búsquedas
- Métricas de uso del sistema

## Instalación y Configuración

### 1. Dependencias
```bash
pip install beautifulsoup4>=4.12.2 lxml>=4.9.3 httpx
```

### 2. Migración de Base de Datos
```bash
python migrate_job_scraping.py
```

### 3. Configuración de Variables de Entorno
```env
# Configuración de scraping
OCC_SCRAPER_DELAY=2  # Segundos entre requests
OCC_MAX_RETRIES=3
OCC_TIMEOUT=30

# Rate limiting
OCC_REQUESTS_PER_MINUTE=30
OCC_BURST_LIMIT=10
```

## Ejemplos de Uso

### Búsqueda Básica
```python
from app.services.occ_scraper_service import OCCScraper, SearchFilters

async def buscar_empleos_python():
    filters = SearchFilters(
        keyword="Python desarrollador",
        location="Córdoba",
        work_mode="remoto",
        salary_min=80000,
        experience_level="junior"
    )
    
    async with OCCScraper() as scraper:
        jobs, total = await scraper.search_jobs(filters)
        
    for job in jobs:
        print(f"{job.title} - {job.company} - {job.salary}")
```

### Crear Aplicación
```python
from app.services.job_application_service import JobApplicationManager

def aplicar_empleo(user_id: int, job_id: str):
    with get_session() as db:
        manager = JobApplicationManager(db)
        application = manager.create_application(
            user_id=user_id,
            job_offer_id=job_id,
            notes="Enviado con portfolio actualizado"
        )
    return application
```

### Configurar Alerta
```python
from app.services.job_application_service import JobAlertManager

def crear_alerta_python(user_id: int):
    with get_session() as db:
        alert_manager = JobAlertManager(db)
        alert = alert_manager.create_job_alert(
            user_id=user_id,
            keywords=["Python", "FastAPI", "Django"],
            location="Córdoba",
            work_mode="remoto",
            frequency="daily"
        )
    return alert
```

## Estructura de Datos

### JobOffer (Scraped Data)
```python
{
    "job_id": "occ_12345",
    "title": "Desarrollador Python Sr",
    "company": "TechCorp SA",
    "company_verified": true,
    "location": "Córdoba, Argentina", 
    "salary": "$120,000 - $180,000 mensual",
    "publication_date": "Hace 1 día",
    
    # Campos de descripción completa
    "full_description": "Descripción detallada del empleo...",
    "requirements": ["Requisito 1", "Requisito 2"],
    "activities": ["Actividad 1", "Actividad 2"],
    "soft_skills": ["Liderazgo", "Comunicación"],
    
    # Información laboral detallada
    "category": "Tecnologías de la Información",
    "subcategory": "Sistemas - Redes",
    "job_type": "Tiempo completo",
    "work_mode": "Híbrido",
    "work_schedule": "De lunes a viernes, 8:30am - 5:30pm",
    "contract_type": "Contrato indefinido",
    "minimum_education": "Universitario sin título",
    
    # Beneficios y contacto
    "benefits": ["Obra social", "Vacaciones", "Capacitación pagada"],
    "skills": ["Python", "FastAPI", "PostgreSQL"],
    
    # Metadata de extracción
    "contact_info": "Nombre: Juan Pérez, Email: rh@company.com",
    "share_url": "https://occ.com.mx/compartir/12345",
    "job_detail_id": "20806805",
    "is_featured": true,
    "is_new": true,
    "url": "https://occ.com.mx/empleos/12345"
}
```

### Application Tracking
```python
{
    "id": 1,
    "user_id": 123,
    "job_offer_id": 456,
    "status": "interview",  # applied, pending, interview, rejected, accepted
    "external_application_url": "https://company.com/apply/789",
    "notes": "Entrevista técnica agendada para el viernes",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-18T14:20:00Z"
}
```

## Considerciones de Extracción

### Métricas de Calidad

El endpoint `/job/{job_id}` retorna un objeto `extraction_quality` que reporta:

| Métrica | Descripción |
|---------|------------|
| `has_title` | Si se extrajo título del empleo |
| `has_company` | Si se extrajo nombre de empresa |
| `has_salary` | Si se extrajo información de salario |
| `has_benefits` | Si se identificaron beneficios |
| `has_category` | Si se clasificó en categoría |
| `has_description` | Si se obtuvo descripción completa |
| `has_skills` | Si se identificaron habilidades técnicas |
| `completeness_score` | Porcentaje de campos extraídos (0-100%) |

**Ejemplo de respuesta con métricas:**
```json
"extraction_quality": {
  "has_title": true,
  "has_company": true,
  "has_salary": true,
  "has_benefits": true,
  "has_category": true,
  "has_description": true,
  "has_skills": true,
  "completeness_score": 92.5
}
```

### Recomendaciones Automáticas

El sistema genera recomendaciones contextuales:
- ⚠️ "Empresa confidencial - Considera preguntar sobre la empresa en entrevista"
- 💡 "Considera adquirir experiencia en tecnología X"
- 📍 "Modalidad presencial en ubicación Y"
- 💰 "Salario a negociar directamente"

## Consideraciones de Seguridad

### Rate Limiting
- Máximo 30 requests por minuto a OCC.com.mx
- Delays configurables entre requests
- Circuit breaker para evitar baneos

### Headers Anti-Detección
```python
{
    "User-Agent": "Mozilla/5.0 (compatible; MoirAI-JobBot/1.0)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "es-MX,es;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}
```

### Privacidad de Datos
- Cifrado de información personal
- Anonimización de métricas agregadas
- Cumplimiento LFPDPPP para datos de estudiantes

## Monitoreo y Logging

### ScrapingLogDB
- Registro de todas las operaciones de scraping
- Métricas de éxito/fallo
- Análisis de rendimiento y errores
- Alertas automáticas por fallos recurrentes

### Métricas Clave
- Tasa de éxito de scraping (>95% objetivo)
- Tiempo de respuesta promedio (<5s)
- Número de empleos nuevos por día
- Tasa de conversión aplicación → entrevista

## Roadmap

### Próximas Funcionalidades
- [ ] Extracción de imágenes y logos de empresas
- [ ] Integración con LinkedIn Jobs
- [ ] OCR para análisis de imágenes de ofertas
- [ ] ML para scoring automático de compatibilidad
- [ ] Notificaciones push móviles
- [ ] Dashboard analytics avanzado
- [ ] Análisis de satisfacción post-aplicación

### Optimizaciones Técnicas
- [ ] Cache Redis para búsquedas frecuentes
- [ ] Procesamiento asíncrono con Celery
- [ ] Índices de búsqueda con Elasticsearch
- [ ] API GraphQL para consultas complejas
- [ ] Mejora de selectores CSS para mayor robustez ante cambios de OCC

## Contribución

### Setup Desarrollo
```bash
# Clonar y configurar entorno
git clone <repo>
cd MoirAI
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar base de datos de prueba
cp .env.example .env.test
python migrate_job_scraping.py --sample-data

# Ejecutar tests
pytest tests/test_job_scraping.py -v
```

### Estructura de Tests
- `tests/unit/test_occ_scraper.py` - Tests del scraper
- `tests/unit/test_job_application_service.py` - Tests de servicios
- `tests/integration/test_job_scraping_api.py` - Tests de API
- `tests/e2e/test_job_scraping_flow.py` - Tests end-to-end

---

**Contacto**: Equipo de desarrollo MoirAI - UNRC  
**Versión**: 1.0.0  
**Última actualización**: Enero 2024
