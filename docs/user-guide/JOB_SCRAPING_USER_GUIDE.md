# Guía de Usuario - Sistema de Scraping de Empleos OCC.com.mx

## Descripción General

El sistema de scraping de empleos permite a los usuarios de MoirAI buscar, rastrear y recibir alertas sobre oportunidades laborales del portal OCC.com.mx de manera automatizada e inteligente.

## Características Principales

### 🔍 Búsqueda Inteligente de Empleos
- **Filtros avanzados**: Ubicación, salario, modalidad de trabajo, experiencia
- **Resultados estructurados**: Información completa extraída con NLP
- **Historial de búsquedas**: Todas las consultas se guardan para análisis

### 📊 Seguimiento de Aplicaciones
- **Estados detallados**: Aplicado, entrevista, rechazado, aceptado
- **Notas personales**: Comentarios y seguimiento personalizado
- **Estadísticas de éxito**: Métricas personales de aplicaciones

### 🔔 Sistema de Alertas
- **Alertas personalizadas**: Por palabras clave y criterios específicos
- **Notificaciones automáticas**: Procesamiento diario o semanal
- **Gestión completa**: Crear, modificar y eliminar alertas

### 📈 Analytics y Tendencias
- **Empleos trending**: Los más buscados por la comunidad
- **Análisis de mercado**: Tendencias laborales en tiempo real

## Guía de Uso

### 1. Buscar Empleos

#### Endpoint: `POST /job-scraping/search`

**Búsqueda básica:**
```bash
curl -X POST "http://localhost:8000/job-scraping/search" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: TU_API_KEY" \
  -d '{
    "keyword": "Python Developer",
    "location": "Córdoba"
  }'
```

**Búsqueda avanzada:**
```bash
curl -X POST "http://localhost:8000/job-scraping/search" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: TU_API_KEY" \
  -d '{
    "keyword": "Desarrollador Full Stack",
    "location": "Buenos Aires",
    "salary_min": 100000,
    "work_mode": "remoto",
    "job_type": "tiempo-completo",
    "experience_level": "senior",
    "sort_by": "date",
    "page": 1
  }'
```

**Parámetros disponibles:**
- `keyword` (requerido): Palabra clave para la búsqueda
- `location`: Ubicación geográfica
- `salary_min`: Salario mínimo esperado
- `work_mode`: "presencial", "remoto", "hibrido"
- `job_type`: "tiempo-completo", "medio-tiempo", "freelance"
- `experience_level`: "junior", "semi-senior", "senior"
- `sort_by`: "relevance", "date", "salary"
- `page`: Número de página (por defecto 1)

**Respuesta esperada:**
```json
{
  "jobs": [
    {
      "job_id": "occ_12345",
      "title": "Desarrollador Python Sr",
      "company": "TechCorp SA",
      "location": "Córdoba, Argentina",
      "salary": "$120,000 - $180,000 mensual",
      "publication_date": "Hace 1 día",
      "category": "Tecnologías de la Información",
      "job_type": "Tiempo completo",
      "work_mode": "Híbrido",
      "skills": ["Python", "FastAPI", "PostgreSQL"],
      "is_new": true,
      "is_featured": false
    }
  ],
  "total_results": 45,
  "search_params": {
    "keyword": "Python Developer",
    "location": "Córdoba"
  }
}
```

### 2. Obtener Detalles Completos de un Empleo

#### Endpoint: `GET /job-scraping/job/{job_id}`

**Obtener información enriquecida del empleo:**
```bash
curl -X GET "http://localhost:8000/job-scraping/job/occ_20806805" \
  -H "X-API-Key: TU_API_KEY"
```

**Respuesta con extracción detallada:**
```json
{
  "job_details": {
    "job_id": "occ_20806805",
    "title": "Becario Data Science",
    "company": "Empresa confidencial",
    "location": "Ciudad de México",
    "salary": "$8,000 Mensual",
    "category": "Tecnologías de la Información",
    "subcategory": "Sistemas",
    "education_required": "Universitario sin título",
    "job_type": "Medio tiempo",
    "work_mode": "Presencial",
    "work_schedule": "Tiempo parcial, 8:30am - 5:30pm",
    "contract_type": "Contrato indefinido",
    "full_description": "Descripción detallada del puesto...",
    "requirements": [
      "Conocimiento en análisis de datos",
      "Dominio de SQL",
      "Experiencia con Python"
    ],
    "activities": [
      "Analizar bases de datos",
      "Generar reportes",
      "Proponer mejoras"
    ],
    "soft_skills": [
      "Comunicación efectiva",
      "Trabajo en equipo",
      "Adaptabilidad"
    ],
    "skills": ["R", "SQL", "Python"],
    "benefits": [
      "Prestaciones de ley",
      "Plan de carrera y crecimiento",
      "Capacitación pagada"
    ],
    "contact_info": "Nombre: Juan Pérez, rh@empresa.com",
    "share_url": "https://occ.com.mx/share/...",
    "is_featured": true,
    "is_new": true
  },
  "extraction_quality": {
    "has_title": true,
    "has_company": true,
    "has_salary": true,
    "has_benefits": true,
    "has_category": true,
    "has_description": true,
    "has_skills": true,
    "completeness_score": 92.5
  },
  "available_sections": {
    "basic_info": true,
    "categorization": true,
    "requirements": true,
    "activities": true,
    "soft_skills": true,
    "technical_skills": true,
    "benefits": true,
    "contact_info": true
  },
  "recommendations": [
    "Empresa confidencial - Considera preguntar sobre el nombre de la empresa en entrevista",
    "Modalidad presencial en CDMX - Verifica si puedes asistir a oficina",
    "Considera fortalecer tus conocimientos en R para mejorar candidatura"
  ],
  "success": true
}
```

**Campos extraídos automáticamente:**

| Campo | Descripción |
|-------|------------|
| `full_description` | Descripción completa del empleo |
| `requirements` | Lista de requisitos específicos |
| `activities` | Principales actividades a realizar |
| `soft_skills` | Competencias blandas requeridas |
| `skills` | Habilidades técnicas identificadas |
| `job_type` | Tipo de contrato (tiempo completo, medio tiempo, etc.) |
| `work_schedule` | Horario específico |
| `contract_type` | Modalidad de contratación |
| `category` / `subcategory` | Clasificación del empleo |

**Métricas de extracción:**
- `completeness_score`: Porcentaje de campos extraídos (0-100%)
- `available_sections`: Qué secciones se pudieron extraer
- `recommendations`: Sugerencias basadas en el contenido

### 2. Registrar Aplicación a Empleo

#### Endpoint: `POST /job-scraping/apply`

```bash
curl -X POST "http://localhost:8000/job-scraping/apply" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: TU_API_KEY" \
  -d '{
    "job_id": "occ_12345",
    "external_url": "https://company.com/careers/apply/789",
    "notes": "CV enviado por email, contacto con HR confirmado"
  }'
```

**Parámetros:**
- `job_id` (requerido): ID del empleo en OCC
- `external_url`: URL de aplicación externa si aplica
- `notes`: Notas personales sobre la aplicación

### 4. Actualizar Estado de Aplicación

#### Endpoint: `PUT /job-scraping/application/{id}/status`

```bash
curl -X PUT "http://localhost:8000/job-scraping/application/123/status" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: TU_API_KEY" \
  -d '{
    "status": "interview",
    "notes": "Entrevista técnica agendada para el viernes 10am"
  }'
```

**Estados válidos:**
- `applied`: Aplicación enviada
- `pending`: Esperando respuesta
- `interview`: En proceso de entrevistas
- `rejected`: Rechazado
- `accepted`: Aceptado
- `withdrawn`: Retirado por el candidato

### 5. Ver Mis Aplicaciones

#### Endpoint: `GET /job-scraping/applications`

```bash
# Todas las aplicaciones
curl -X GET "http://localhost:8000/job-scraping/applications" \
  -H "X-API-Key: TU_API_KEY"

# Filtrar por estado
curl -X GET "http://localhost:8000/job-scraping/applications?status=interview" \
  -H "X-API-Key: TU_API_KEY"
```

### 6. Estadísticas Personales

#### Endpoint: `GET /job-scraping/applications/stats`

```bash
curl -X GET "http://localhost:8000/job-scraping/applications/stats" \
  -H "X-API-Key: TU_API_KEY"
```

**Respuesta esperada:**
```json
{
  "total_applications": 15,
  "status_breakdown": {
    "applied": 5,
    "interview": 3,
    "rejected": 4,
    "accepted": 2,
    "pending": 1
  },
  "recent_applications": 8,
  "success_rate": 13.33
}
```

### 7. Crear Alerta de Empleo

#### Endpoint: `POST /job-scraping/alerts`

```bash
curl -X POST "http://localhost:8000/job-scraping/alerts" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: TU_API_KEY" \
  -d '{
    "keywords": ["Python", "FastAPI", "Django"],
    "location": "Córdoba",
    "salary_min": 80000,
    "work_mode": "remoto",
    "frequency": "daily"
  }'
```

**Parámetros:**
- `keywords` (requerido): Lista de palabras clave
- `location`: Ubicación preferida
- `salary_min`: Salario mínimo
- `work_mode`: Modalidad de trabajo
- `frequency`: "daily" o "weekly"

### 8. Gestionar Alertas

#### Listar alertas: `GET /job-scraping/alerts`
```bash
curl -X GET "http://localhost:8000/job-scraping/alerts" \
  -H "X-API-Key: TU_API_KEY"
```

#### Eliminar alerta: `DELETE /job-scraping/alerts/{id}`
```bash
curl -X DELETE "http://localhost:8000/job-scraping/alerts/123" \
  -H "X-API-Key: TU_API_KEY"
```

### 9. Empleos en Tendencia

#### Endpoint: `GET /job-scraping/trending-jobs`

```bash
curl -X GET "http://localhost:8000/job-scraping/trending-jobs?limit=20" \
  -H "X-API-Key: TU_API_KEY"
```

### 10. Historial de Búsquedas

#### Endpoint: `GET /job-scraping/search-history`

```bash
curl -X GET "http://localhost:8000/job-scraping/search-history?limit=10" \
  -H "X-API-Key: TU_API_KEY"
```

## Casos de Uso Prácticos

### Caso 1: Búsqueda Inicial de Empleos
```bash
# 1. Buscar empleos Python en Córdoba
curl -X POST "http://localhost:8000/job-scraping/search" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: TU_API_KEY" \
  -d '{"keyword": "Python", "location": "Córdoba"}'

# 2. Aplicar a empleo específico
curl -X POST "http://localhost:8000/job-scraping/apply" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: TU_API_KEY" \
  -d '{"job_id": "occ_12345", "notes": "CV enviado"}'

# 3. Configurar alerta para empleos similares
curl -X POST "http://localhost:8000/job-scraping/alerts" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: TU_API_KEY" \
  -d '{"keywords": ["Python", "Backend"], "location": "Córdoba", "frequency": "daily"}'
```

### Caso 2: Seguimiento de Aplicaciones
```bash
# 1. Ver todas mis aplicaciones
curl -X GET "http://localhost:8000/job-scraping/applications" \
  -H "X-API-Key: TU_API_KEY"

# 2. Actualizar estado cuando me llamen para entrevista
curl -X PUT "http://localhost:8000/job-scraping/application/123/status" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: TU_API_KEY" \
  -d '{"status": "interview", "notes": "Entrevista técnica viernes 10am"}'

# 3. Ver mis estadísticas
curl -X GET "http://localhost:8000/job-scraping/applications/stats" \
  -H "X-API-Key: TU_API_KEY"
```

### Caso 3: Análisis de Mercado Laboral
```bash
# 1. Ver empleos en tendencia
curl -X GET "http://localhost:8000/job-scraping/trending-jobs" \
  -H "X-API-Key: TU_API_KEY"

# 2. Revisar mi historial de búsquedas
curl -X GET "http://localhost:8000/job-scraping/search-history" \
  -H "X-API-Key: TU_API_KEY"

# 3. Buscar empleos con salarios altos
curl -X POST "http://localhost:8000/job-scraping/search" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: TU_API_KEY" \
  -d '{"keyword": "Senior Developer", "salary_min": 150000, "sort_by": "salary"}'
```

## Mejores Prácticas

### Para Estudiantes

1. **Configura alertas específicas**: Usa palabras clave relacionadas a tu carrera
2. **Mantén actualizado el seguimiento**: Actualiza estados de aplicaciones regularmente
3. **Usa notas detalladas**: Registra información importante de cada aplicación
4. **Revisa estadísticas**: Analiza tu tasa de éxito y ajusta estrategia
5. **Aprovecha trending**: Mantente al día con empleos en tendencia

### Para Administradores

1. **Monitorea el sistema**: Usa endpoint `/job-scraping/admin/process-alerts`
2. **Revisa logs**: Supervisa operaciones de scraping en la base de datos
3. **Optimiza alertas**: Procesa alertas en horarios de baja carga
4. **Analiza métricas**: Usa datos agregados para mejorar el servicio

## Limitaciones y Consideraciones

### Rate Limiting
- Máximo 30 requests por minuto por usuario
- Delays automáticos entre requests al sitio OCC.com.mx
- Sistema de circuit breaker para evitar bloqueos

### Disponibilidad de Datos
- Dependiente de la disponibilidad de OCC.com.mx
- Estructura del sitio puede cambiar (requiere actualizaciones)
- Algunos empleos pueden no ser accesibles por restricciones del sitio

### Privacidad
- Todas las búsquedas y aplicaciones se registran para análisis
- Datos personales protegidos según LFPDPPP
- Logs de auditoría completos para cumplimiento normativo

## Solución de Problemas

### Error: "Job not found"
- Verificar que el `job_id` sea válido y actual
- El empleo puede haber sido eliminado del sitio OCC.com.mx

### Error: "Rate limit exceeded"
- Esperar algunos minutos antes de hacer nuevas requests
- Implementar delays entre llamadas automáticas

### Error: "Search returned no results"
- Probar con keywords más generales
- Verificar filtros aplicados (ubicación, salario)
- Revisar si hay empleos disponibles en OCC.com.mx

### Error: "Alert creation failed"
- Verificar que las keywords no estén vacías
- Revisar formato de frecuencia ("daily" o "weekly")
- Contactar administrador si persiste

## API Keys y Autenticación

Todos los endpoints requieren autenticación mediante API Key:

```bash
-H "X-API-Key: TU_API_KEY_AQUI"
```

Para obtener una API Key:
1. Contactar administrador del sistema
2. Usar las claves de desarrollo del archivo `.env`
3. Implementar OAuth2/JWT en producción

## Soporte

Para soporte técnico:
- **Documentación API**: http://localhost:8000/docs
- **Email**: contacto@ing.unrc.edu.mx
- **Issues**: GitHub del proyecto
- **Logs**: Revisar logs de aplicación para errores detallados
