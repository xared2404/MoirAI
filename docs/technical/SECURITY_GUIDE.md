# Guía de Seguridad para Despliegue en Producción

## 🔐 CHECKLIST DE SEGURIDAD PARA PRODUCCIÓN

### 1. Variables de Entorno y Secretos
- [ ] Generar SECRET_KEY único y fuerte (mínimo 32 caracteres)
- [ ] Configurar contraseñas de base de datos seguras
- [ ] Usar variables de entorno para todas las credenciales
- [ ] Nunca hardcodear secretos en el código
- [ ] Usar servicios de gestión de secretos (AWS Secrets Manager, HashiCorp Vault)

### 2. Base de Datos
- [ ] Configurar PostgreSQL en lugar de SQLite
- [ ] Habilitar SSL/TLS para conexiones de BD
- [ ] Configurar backup automático
- [ ] Limitar acceso de red a la BD
- [ ] Usar usuarios de BD con privilegios mínimos

### 3. Configuración del Servidor
- [ ] Deshabilitar modo debug/desarrollo
- [ ] Configurar HTTPS con certificados válidos
- [ ] Configurar CORS apropiadamente
- [ ] Implementar rate limiting
- [ ] Configurar logs de seguridad

### 4. Autenticación y Autorización
- [ ] Implementar OAuth2/JWT en lugar de API keys estáticas
- [ ] Configurar expiración de tokens
- [ ] Implementar refresh tokens
- [ ] Habilitar autenticación de dos factores
- [ ] Audit logs de accesos

### 5. Configuración de Red
- [ ] Configurar firewall (solo puertos necesarios)
- [ ] Usar reverse proxy (nginx/Apache)
- [ ] Configurar DDoS protection
- [ ] Implementar WAF (Web Application Firewall)

### 6. Monitoreo y Logging
- [ ] Configurar logs centralizados
- [ ] Monitoreo de recursos del sistema
- [ ] Alertas de seguridad
- [ ] Backup y recovery plan

## 🚀 CONFIGURACIÓN PARA DIFERENTES ENTORNOS

### Desarrollo Local
```bash
# Usar SQLite para simplicidad
DATABASE_URL="sqlite:///./moirai.db"
DEBUG=true
LOG_LEVEL="DEBUG"
```

### Staging
```bash
# PostgreSQL con datos de prueba
DATABASE_URL="postgresql://user:pass@staging-db:5432/moirai_staging"
DEBUG=false
LOG_LEVEL="INFO"
```

### Producción
```bash
# PostgreSQL con alta disponibilidad
DATABASE_URL="postgresql://user:pass@prod-db:5432/moirai_prod"
DEBUG=false
LOG_LEVEL="WARNING"
ENABLE_AUDIT_LOGGING=true
```

## 🛡️ CONFIGURACIONES ESPECÍFICAS DE FASTAPI

### Configuración Segura
```python
# app/core/config.py
class Settings(BaseSettings):
    # Seguridad
    SECRET_KEY: str = Field(..., min_length=32)
    DEBUG: bool = False
    ALLOWED_HOSTS: List[str] = ["your-domain.com"]
    
    # HTTPS
    FORCE_HTTPS: bool = True
    SECURE_COOKIES: bool = True
    
    # Headers de seguridad
    SECURITY_HEADERS: bool = True
```

### Middleware de Seguridad
```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["your-domain.com", "*.your-domain.com"]
)
```

## 📊 MÉTRICAS Y MONITOREO

### Health Checks
- Endpoint `/health` para verificar estado
- Verificación de conectividad de BD
- Verificación de servicios externos

### Logs de Auditoría
- Accesos a la API
- Cambios en datos sensibles
- Intentos de autenticación fallidos
- Operaciones administrativas

## 🔧 HERRAMIENTAS RECOMENDADAS

### Desarrollo
- `bandit` - Análisis de seguridad de código Python
- `safety` - Verificación de vulnerabilidades en dependencias
- `semgrep` - Análisis estático de código

### Producción
- `fail2ban` - Protección contra ataques de fuerza bruta
- `certbot` - Gestión automática de certificados SSL
- `prometheus` + `grafana` - Monitoreo y métricas
- `elk stack` - Logs centralizados

## 🏢 Acceso Seguro a Datos de Estudiantes por Empresas

### Requisitos de Verificación

Solo las empresas verificadas (`is_verified = true`) pueden acceder a la funcionalidad de búsqueda de estudiantes. El proceso de verificación incluye:

**Documentos Requeridos**:
- RFC (Registro Federal de Contribuyentes)
- Comprobante de domicilio fiscal (no mayor a 3 meses)
- Identificación oficial del representante legal
- Acta constitutiva o comprobante legal de existencia

**Proceso de Aprobación**:
1. Empresa envía solicitud de verificación con documentos
2. Administrador UNRC revisa dentro de 48-72 horas
3. Se contacta a la empresa si hay preguntas
4. Empresa recibe `is_verified=true` después de aprobación
5. Acceso a búsqueda de estudiantes se activa automáticamente

**Validaciones Implementadas**:
```python
# En endpoint GET /companies/{id}/search-students
if not company.is_verified:
    raise HTTPException(
        status_code=403,
        detail="Empresa no verificada. Complete el proceso de verificación primero."
    )
```

### Información Pública vs Privada

**Información Disponible para Empresas Verificadas**:
- ✅ Nombre completo del estudiante
- ✅ Ubicación/Municipio
- ✅ Programa académico
- ✅ Habilidades técnicas identificadas
- ✅ Habilidades blandas inferidas
- ✅ Proyectos completados (descripción y tecnologías)
- ✅ Años de experiencia aproximados
- ✅ Fecha de perfil público (sin hora exacta)

**Información PROTEGIDA (Nunca se expone)**:
- ❌ Email personal/institucional
- ❌ Teléfono directo
- ❌ Dirección completa
- ❌ Notas académicas detalladas
- ❌ Calificaciones numéricas
- ❌ Información de padres/tutores
- ❌ Datos biométricos
- ❌ Historial académico detallado
- ❌ Documentos personales

### Auditoría de Búsquedas

Cada búsqueda realizada por una empresa es registrada en el sistema para cumplimiento normativo:

**Información Registrada en AuditLog**:
```python
AuditLog(
    actor_role="company",
    actor_id=company.id,
    action="SEARCH_STUDENTS",
    resource=f"students:search",
    success=True,
    details=json.dumps({
        "company_id": company.id,
        "search_keywords": search_params.get("keywords", []),
        "filters_applied": {
            "program": search_params.get("program"),
            "skills": search_params.get("skills"),
            "experience_min": search_params.get("experience_min")
        },
        "results_count": len(results),
        "timestamp": datetime.utcnow().isoformat()
    })
)
```

**Acceso a Auditoría**:
- Solo administradores UNRC pueden ver logs de búsquedas
- Endpoint: `GET /api/v1/admin/audit_logs?resource=students:search`
- Filtros disponibles: `actor_id`, `action`, `date_from`, `date_to`
- Retención: Mínimo 1 año (configurable en `DATA_RETENTION_DAYS`)

**Cumplimiento LFPDPPP**:
- ✅ Registro de accesos (Arts. 32-33)
- ✅ Derecho de acceso del titular (Art. 52)
- ✅ Auditoría de uso de datos (Art. 59)
- ✅ Anonimización después de retención (Art. 63)

### Rate Limiting para Búsquedas

Para evitar abuso y garantizar equidad en el acceso:

**Límites por Rol**:
- **Empresas Verificadas**: 100 búsquedas/hora
- **Empresas No Verificadas**: 0 búsquedas (bloqueado)
- **Admin UNRC**: Sin límite

**Implementación**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/companies/{id}/search-students")
@limiter.limit("100/hour")
async def search_students(id: int, ...):
    # Si límite excedido, retorna 429 Too Many Requests
    pass
```

**Headers Retornados**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1636401234
```

### Restricciones de Búsqueda

**Lo que Las Empresas NO Pueden Hacer**:
- ❌ Buscar por email o teléfono
- ❌ Acceder a perfiles de estudiantes inactivos
- ❌ Descargar listas completas de estudiantes
- ❌ Buscar información eliminada
- ❌ Acceder a datos de estudiantes que pidieron anonimización

**Lo que Las Empresas SÍ Pueden Hacer**:
- ✅ Buscar por habilidades técnicas
- ✅ Filtrar por programa académico
- ✅ Filtrar por ubicación
- ✅ Buscar por palabras clave en proyectos
- ✅ Ver perfiles públicos de estudiantes activos
- ✅ Contactar a través del sistema (futuro)

### Consentimiento y Privacidad

**Consentimiento del Estudiante**:
- Estudiantes dan consentimiento en `Student.consent_data_processing` al registrarse
- Pueden revocar consentimiento en cualquier momento
- Al revocar: perfil se marca como no disponible para búsquedas (`is_active=False`)
- Pueden solicitar anonimización completa (derecho al olvido)

**Notificación a Estudiantes**:
- ✅ Email notificando cuando su perfil es encontrado en búsqueda (futuro)
- ✅ Dashboard mostrando qué empresas han accedido a su perfil (futuro)
- ✅ Opción de bloquearse de empresa específica (futuro)

---

