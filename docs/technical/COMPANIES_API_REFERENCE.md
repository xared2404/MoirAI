# 🔗 Referencia Técnica de API: Endpoints de Empresas

**Versión**: 1.0.0 (Planificación - No Implementado)  
**Base URL**: `http://localhost:8000/api/v1`  
**Autenticación**: `X-API-Key` header

---

## 📚 Tabla de Contenidos

1. [Autenticación](#autenticación)
2. [Códigos de Estado](#códigos-de-estado)
3. [Endpoints CRUD](#endpoints-crud)
4. [Esquemas](#esquemas)
5. [Ejemplos](#ejemplos)
6. [Rate Limiting](#rate-limiting)
7. [Errores Comunes](#errores-comunes)

---

## 🔐 Autenticación

### Header Requerido

```http
X-API-Key: your-api-key-here
```

### Tipos de API Keys

| Tipo | Alcance | Permisos |
|------|---------|----------|
| **ADMIN** | Todas las empresas | Crear, leer, actualizar, eliminar, verificar |
| **COMPANY** | Solo propia empresa | Leer propia, actualizar propia, buscar estudiantes |
| **STUDENT** | Lectura pública | Leer empresas verificadas |
| **ANONYMOUS** | Lectura mínima | Listar empresas públicas (sin verificación requerida) |

### Ejemplo de Autenticación

```bash
curl -H "X-API-Key: sk_live_your_key_here" \
  "http://localhost:8000/api/v1/companies/"
```

---

## 📊 Códigos de Estado HTTP

| Código | Significado | Descripción |
|--------|------------|-------------|
| **200** | OK | Solicitud exitosa (GET, PUT, PATCH, DELETE) |
| **201** | Created | Recurso creado exitosamente (POST) |
| **400** | Bad Request | Validación de datos fallida |
| **401** | Unauthorized | API key inválida o no enviada |
| **403** | Forbidden | Permisos insuficientes para la operación |
| **404** | Not Found | Recurso no encontrado |
| **409** | Conflict | Email duplicado u otro conflicto de datos |
| **422** | Unprocessable Entity | Datos mal formados o tipos incorrectos |
| **429** | Too Many Requests | Rate limiting (demasiadas solicitudes) |
| **500** | Internal Server Error | Error del servidor |

---

## 🚀 Endpoints CRUD

### 1. CREATE - Registrar Empresa

```http
POST /companies/
```

#### Request

```json
{
  "name": "Tech Solutions S.A.",
  "email": "contacto@techsolutions.mx",
  "industry": "Tecnología",
  "size": "mediana",
  "location": "Ciudad de México, México"
}
```

#### Response (201 Created)

```json
{
  "id": 42,
  "name": "Tech Solutions S.A.",
  "email": "contacto@techsolutions.mx",
  "industry": "Tecnología",
  "size": "mediana",
  "location": "Ciudad de México, México",
  "is_verified": false,
  "is_active": true,
  "created_at": "2025-11-04T10:30:00Z",
  "updated_at": null
}
```

#### Validaciones

- ✅ `name`: 1-100 caracteres, requerido
- ✅ `email`: Formato válido, único en BD, requerido
- ✅ `industry`: 0-50 caracteres, opcional
- ✅ `size`: Enum (startup|pequeña|mediana|grande), opcional
- ✅ `location`: 0-100 caracteres, opcional

#### Errores Posibles

| Error | Causa | Solución |
|-------|-------|----------|
| 400 | Nombre vacío | Proporcionar nombre válido |
| 400 | Email inválido | Usar formato válido: usuario@dominio.com |
| 409 | Email duplicado | Usar diferente email o contactar admin |
| 422 | Size no válido | Usar: startup, pequeña, mediana, o grande |

---

### 2. READ - Listar Empresas

```http
GET /companies/?skip=0&limit=20&industry=Tecnología&is_verified=true
```

#### Query Parameters

| Parámetro | Tipo | Default | Max | Descripción |
|-----------|------|---------|-----|-------------|
| `skip` | int | 0 | - | Registros a saltar (paginación) |
| `limit` | int | 20 | 100 | Registros a retornar |
| `industry` | str | - | 50 | Filtrar por sector |
| `size` | str | - | - | Filtrar: startup, pequeña, mediana, grande |
| `location` | str | - | 100 | Filtrar por ubicación (búsqueda parcial) |
| `is_verified` | bool | - | - | Filtrar verificadas/no verificadas |
| `sort_by` | str | name | - | Ordenar: name, created_at, verified |
| `search` | str | - | - | Búsqueda en name/email (admin only) |

#### Response

```json
{
  "total": 150,
  "skip": 0,
  "limit": 20,
  "data": [
    {
      "id": 42,
      "name": "Tech Solutions S.A.",
      "email": "contacto@techsolutions.mx",
      "industry": "Tecnología",
      "size": "mediana",
      "location": "Ciudad de México, México",
      "is_verified": true,
      "is_active": true,
      "created_at": "2025-11-04T10:30:00Z",
      "updated_at": "2025-11-05T14:22:00Z"
    }
  ]
}
```

#### Control de Acceso

- **Admin**: Ve todas las empresas (activas + inactivas)
- **Company**: Solo empresas verificadas
- **Student**: Solo empresas verificadas con info pública
- **Anonymous**: Empresas verificadas (info mínima)

---

### 3. READ - Obtener Empresa Específica

```http
GET /companies/{company_id}
```

#### Path Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `company_id` | int | ID único de la empresa |

#### Response (200 OK)

```json
{
  "id": 42,
  "name": "Tech Solutions S.A.",
  "email": "contacto@techsolutions.mx",
  "industry": "Tecnología",
  "size": "mediana",
  "location": "Ciudad de México, México",
  "is_verified": true,
  "is_active": true,
  "created_at": "2025-11-04T10:30:00Z",
  "updated_at": "2025-11-05T14:22:00Z"
}
```

#### Errores Posibles

| Código | Causa | Solución |
|--------|-------|----------|
| 404 | Empresa no existe | Verificar company_id |
| 403 | Acceso denegado | Verificar permisos |

---

### 4. READ - Buscar Candidatos Estudiantes

```http
GET /companies/{company_id}/search-students?skills=Python&skills=React&limit=20
```

#### Requisitos

⚠️ **La empresa DEBE estar verificada** (`is_verified = true`)

#### Query Parameters

| Parámetro | Tipo | Default | Max | Descripción |
|-----------|------|---------|-----|-------------|
| `skills` | List[str] | - | - | Habilidades técnicas (puede repetirse) |
| `location` | str | - | - | Ubicación del estudiante |
| `program` | str | - | - | Programa académico |
| `experience_level` | str | - | - | junior, mid, senior |
| `soft_skills` | List[str] | - | - | Habilidades blandas |
| `skip` | int | 0 | - | Paginación |
| `limit` | int | 20 | 100 | Resultados por página |

#### Response

```json
{
  "total": 45,
  "skip": 0,
  "limit": 20,
  "data": [
    {
      "id": 101,
      "name": "Juan García López",
      "program": "Ingeniería en Sistemas",
      "skills": ["Python", "SQL", "Django"],
      "soft_skills": ["Trabajo en equipo", "Comunicación"],
      "location": "Rosario",
      "is_active": true,
      "created_at": "2025-09-15T14:22:00Z"
    }
  ]
}
```

#### Errores Posibles

| Código | Causa | Solución |
|--------|-------|----------|
| 403 | Empresa no verificada | Contactar admin para verificación |
| 403 | Acceso denegado | Verificar API key y permisos |
| 404 | Empresa no existe | Verificar company_id |

---

### 5. UPDATE - Modificar Empresa

```http
PUT /companies/{company_id}
```

#### Request

```json
{
  "name": "Tech Solutions México S.A.",
  "industry": "Tecnología",
  "size": "grande",
  "location": "Guadalajara, México"
}
```

#### Response (200 OK)

```json
{
  "id": 42,
  "name": "Tech Solutions México S.A.",
  "email": "contacto@techsolutions.mx",
  "industry": "Tecnología",
  "size": "grande",
  "location": "Guadalajara, México",
  "is_verified": true,
  "is_active": true,
  "created_at": "2025-11-04T10:30:00Z",
  "updated_at": "2025-11-06T09:15:00Z"
}
```

#### Campos Actualizables

| Campo | Actualizable | Notas |
|-------|-------------|-------|
| `name` | ✅ | Max 100 caracteres |
| `industry` | ✅ | Max 50 caracteres |
| `size` | ✅ | Enum válido |
| `location` | ✅ | Max 100 caracteres |
| `email` | ❌ | Inmutable por auditoría |
| `is_verified` | ❌ | Solo PATCH /verify |
| `is_active` | ❌ | Solo PATCH /activate |

#### Control de Acceso

- ✅ Owner (company_id == user_id)
- ✅ Admin

#### Errores Posibles

| Código | Causa | Solución |
|--------|-------|----------|
| 403 | No es owner ni admin | Usar API key correcta |
| 422 | Size inválido | Usar valores permitidos |
| 404 | Empresa no existe | Verificar company_id |

---

### 6. UPDATE - Verificar Empresa (Admin Only)

```http
PATCH /companies/{company_id}/verify
```

#### Request

```json
{
  "is_verified": true,
  "reason": "Documentación validada correctamente"
}
```

#### Response (200 OK)

```json
{
  "success": true,
  "message": "Empresa verificada exitosamente",
  "company_id": 42,
  "is_verified": true
}
```

#### Validaciones

- ✅ Solo admin puede ejecutar
- ✅ `is_verified`: boolean, requerido
- ✅ `reason`: string, max 500 caracteres, opcional

#### Errores Posibles

| Código | Causa | Solución |
|--------|-------|----------|
| 403 | No es admin | Usar API key de admin |
| 404 | Empresa no existe | Verificar company_id |

---

### 7. UPDATE - Activar/Desactivar Empresa

```http
PATCH /companies/{company_id}/activate
```

#### Request

```json
{
  "is_active": false,
  "reason": "Pausa temporal en operaciones de reclutamiento"
}
```

#### Response (200 OK)

```json
{
  "success": true,
  "message": "Empresa desactivada exitosamente",
  "company_id": 42,
  "is_active": false
}
```

#### Validaciones

- ✅ Owner o admin pueden ejecutar
- ✅ `is_active`: boolean, requerido
- ✅ `reason`: string, max 500 caracteres, opcional

#### Lógica

- `is_active = false`: Soft delete (reversible)
- `is_active = true`: Reactivar

#### Errores Posibles

| Código | Causa | Solución |
|--------|-------|----------|
| 403 | No es owner ni admin | Usar API key correcta |
| 404 | Empresa no existe | Verificar company_id |

---

### 8. DELETE - Eliminar Empresa

```http
DELETE /companies/{company_id}?permanently=false&reason=Cambio+de+estrategia
```

#### Query Parameters

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `permanently` | bool | false | Hard delete (solo admin) |
| `reason` | str | - | Razón de eliminación (requerida si permanently=true) |

#### Response (200 OK)

```json
{
  "success": true,
  "message": "Empresa eliminada correctamente",
  "company_id": 42,
  "deleted_permanently": false
}
```

#### Comportamientos

**Soft Delete** (default, reversible):
- `is_active = false`
- Empresa no aparece en búsquedas
- Datos protegidos
- Puede reactivarse

**Hard Delete** (admin only, irreversible):
- Eliminación física de BD
- AuditLog mantiene histórico
- Empleos publicados marcados como inactivos
- ❌ Datos de estudiantes NUNCA se elimina

#### Control de Acceso

- ✅ Owner: Solo soft delete
- ✅ Admin: Ambos (soft y hard)

#### Errores Posibles

| Código | Causa | Solución |
|--------|-------|----------|
| 403 | No es owner ni admin | Usar API key correcta |
| 403 | Hard delete sin ser admin | Solo admin puede hacer hard delete |
| 404 | Empresa no existe | Verificar company_id |
| 422 | Reason faltante en hard delete | Proporcionar razón |

---

## 📋 Esquemas (JSON Schema)

### CompanyBase

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "description": "Nombre legal de la empresa"
    },
    "email": {
      "type": "string",
      "format": "email",
      "description": "Email corporativo (unique)"
    },
    "industry": {
      "type": "string",
      "maxLength": 50,
      "description": "Sector industrial"
    },
    "size": {
      "type": "string",
      "enum": ["startup", "pequeña", "mediana", "grande"],
      "description": "Tamaño de empresa"
    },
    "location": {
      "type": "string",
      "maxLength": 100,
      "description": "Ubicación principal"
    }
  },
  "required": ["name", "email"]
}
```

### CompanyProfile (Full)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": {
      "type": "integer",
      "description": "ID único"
    },
    "name": {
      "type": "string"
    },
    "email": {
      "type": "string",
      "format": "email"
    },
    "industry": {
      "type": "string"
    },
    "size": {
      "type": "string"
    },
    "location": {
      "type": "string"
    },
    "is_verified": {
      "type": "boolean",
      "description": "Empresa verificada por UNRC"
    },
    "is_active": {
      "type": "boolean",
      "description": "Empresa activa (soft delete)"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

---

## 💻 Ejemplos Prácticos

### Ejemplo 1: Crear Empresa

```bash
curl -X POST "http://localhost:8000/api/v1/companies/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Innovation Labs",
    "email": "hr@innovationlabs.com",
    "industry": "Tecnología",
    "size": "mediana",
    "location": "México"
  }'
```

### Ejemplo 2: Buscar Empresas Verificadas

```bash
curl -X GET "http://localhost:8000/api/v1/companies/?is_verified=true&limit=50" \
  -H "X-API-Key: your-api-key"
```

### Ejemplo 3: Buscar Candidatos Python/React

```bash
curl -X GET "http://localhost:8000/api/v1/companies/42/search-students" \
  -H "X-API-Key: your-api-key" \
  -G \
  --data-urlencode "skills=Python" \
  --data-urlencode "skills=React" \
  --data-urlencode "location=Rosario" \
  --data-urlencode "experience_level=mid" \
  --data-urlencode "limit=30"
```

### Ejemplo 4: Actualizar Empresa

```bash
curl -X PUT "http://localhost:8000/api/v1/companies/42" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Innovation Labs Mexico",
    "industry": "Consultoría Tecnológica"
  }'
```

### Ejemplo 5: Desactivar Empresa

```bash
curl -X PATCH "http://localhost:8000/api/v1/companies/42/activate" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false,
    "reason": "Cambios organizacionales internos"
  }'
```

---

## 🚦 Rate Limiting

### Límites por Rol

| Rol | Requests/Hora | Burst | Ventana |
|-----|-------------|-------|---------|
| Admin | 10000 | 500 | 1 hora |
| Company | 1000 | 100 | 1 hora |
| Student | 500 | 50 | 1 hora |
| Anonymous | 100 | 20 | 1 hora |

### Headers de Rate Limiting

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1667529600
```

### Respuesta cuando se excede límite (429)

```json
{
  "error": "Rate limit exceeded",
  "message": "Demasiadas solicitudes. Reintente en 3600 segundos.",
  "retry_after": 3600
}
```

---

## ⚠️ Errores Comunes

### Error 400: Bad Request

```json
{
  "detail": {
    "error": "validation_error",
    "fields": {
      "email": "Email format invalid"
    }
  }
}
```

**Solución**: Verificar validación de campos

### Error 401: Unauthorized

```json
{
  "detail": "Invalid or missing API key"
}
```

**Solución**: Proporcionar API key válida en header

### Error 409: Conflict

```json
{
  "detail": "Company with email already exists"
}
```

**Solución**: Usar diferente email

### Error 429: Too Many Requests

```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 3600
}
```

**Solución**: Esperar antes de reintent ar

---

## 📝 Notas Importantes

1. **Auditoría**: Todas las operaciones se registran en AuditLog
2. **Soft Delete**: Por defecto, eliminación es reversible
3. **Verificación**: Requerida para acceder a búsqueda de estudiantes
4. **Email Inmutable**: No puede cambiar email luego de creación
5. **LFPDPPP**: Cumplimiento obligatorio de protección de datos
6. **IP Tracking**: Se registra IP de todas las solicitudes
7. **Encriptación**: TLS 1.3 requerido en producción

---

**Última Actualización**: 4 de noviembre de 2025
