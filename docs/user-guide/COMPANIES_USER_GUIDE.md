# 👥 Guía de Usuario: Gestión de Empresas en MoirAI

**Versión**: 1.0.0  
**Última Actualización**: 4 de noviembre de 2025

---

## 📖 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Registro de Empresa](#registro-de-empresa)
3. [Búsqueda de Candidatos](#búsqueda-de-candidatos)
4. [Gestión del Perfil](#gestión-del-perfil)
5. [Casos de Uso Comunes](#casos-de-uso-comunes)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## 📝 Introducción

La plataforma MoirAI permite a empresas colaboradoras:

✅ Registrarse y crear un perfil empresarial  
✅ Buscar y filtrar candidatos con habilidades específicas  
✅ Acceder a información pública de estudiantes UNRC  
✅ Gestionar su información de contacto y verificación  
✅ Recibir notificaciones de candidatos relevantes (futuro)

**Requisitos**:
- Correo electrónico corporativo válido
- Información básica de la empresa
- Documentos de verificación (en proceso de verificación UNRC)

---

## 🚀 Registro de Empresa

### Paso 1: Crear Cuenta

**Endpoint**: `POST /api/v1/companies/`

**Campos Requeridos**:
- `name` (max 100 caracteres): Nombre legal de la empresa
- `email` (unique): Correo electrónico corporativo

**Campos Opcionales**:
- `industry` (max 50 caracteres): Sector (ej: "Tecnología", "Finanzas")
- `size`: Tamaño de empresa
  - `startup`: Menos de 10 empleados
  - `pequeña`: 10-50 empleados
  - `mediana`: 50-250 empleados
  - `grande`: Más de 250 empleados
- `location` (max 100 caracteres): Ubicación principal (ciudad, país)

### Ejemplo de Solicitud

```bash
curl -X POST "http://localhost:8000/api/v1/companies/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech Solutions S.A.",
    "email": "contacto@techsolutions.mx",
    "industry": "Tecnología",
    "size": "mediana",
    "location": "Ciudad de México, México"
  }'
```

### Respuesta Exitosa (201 Created)

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

### Siguiente: Esperar Verificación

1. **Estado Inicial**: `is_verified = false`
2. **Enviar Documentación**: Contactar a administrador UNRC
   - RFC o documento de constitución
   - Credencial oficial del contacto
   - Comprobante de domicilio
3. **Verificación**: Admin revisará y actualizará el perfil
4. **Confirmación**: Recibirá email notificando verificación ✅

---

## 🔍 Búsqueda de Candidatos

**Requisito Previo**: Empresa verificada (`is_verified = true`)

### Endpoint

`GET /api/v1/companies/{company_id}/search-students`

### Parámetros de Búsqueda (Opcionales)

| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| `skills` | List[str] | Habilidades requeridas | `["Python", "SQL", "React"]` |
| `location` | str | Ubicación del estudiante | `"Rosario"` |
| `program` | str | Programa académico | `"Ingeniería en Sistemas"` |
| `experience_level` | str | Nivel de experiencia | `"junior"`, `"mid"`, `"senior"` |
| `soft_skills` | List[str] | Habilidades blandas | `["Liderazgo", "Comunicación"]` |
| `skip` | int | Paginación (resultados a saltar) | `0` (default) |
| `limit` | int | Resultados por página | `20` (default, max 100) |

### Ejemplo: Buscar Desarrolladores Python Junior

```bash
curl -X GET "http://localhost:8000/api/v1/companies/42/search-students?skills=Python&skills=SQL&experience_level=junior&limit=10" \
  -H "X-API-Key: your-api-key-here"
```

### Respuesta

```json
{
  "total": 15,
  "skip": 0,
  "limit": 10,
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
    },
    {
      "id": 102,
      "name": "María Rodríguez Pérez",
      "program": "Ingeniería en Informática",
      "skills": ["Python", "SQL", "FastAPI"],
      "soft_skills": ["Proactividad", "Adaptabilidad"],
      "location": "Rosario",
      "is_active": true,
      "created_at": "2025-08-20T09:15:00Z"
    }
  ]
}
```

### Interpretación de Resultados

**Campos Disponibles por Estudiante**:
- `id`: Identificador único
- `name`: Nombre completo
- `program`: Programa académico actual
- `skills`: Habilidades técnicas
- `soft_skills`: Habilidades blandas
- `location`: Ubicación
- `is_active`: Si está disponible
- `created_at`: Fecha de registro en plataforma

**⚠️ Información NO Disponible**:
- Email personal (protección LFPDPPP)
- Teléfono directo (protección de datos)
- Datos de contacto específicos (contactar a admin)
- Información académica sensible

---

## 🎯 Gestión del Perfil

### Actualizar Información de la Empresa

**Endpoint**: `PUT /api/v1/companies/{company_id}`

**Campos Actualizables**:
- `name`: Nombre de la empresa
- `industry`: Sector industrial
- `size`: Tamaño de empresa
- `location`: Ubicación

**Campos NO Actualizables** ❌:
- `email` (inmutable para auditoría)
- `is_verified` (solo admin puede cambiar)
- `is_active` (usar endpoint `/activate`)

### Ejemplo: Actualizar Información

```bash
curl -X PUT "http://localhost:8000/api/v1/companies/42" \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech Solutions México S.A.",
    "location": "Guadalajara, México"
  }'
```

### Desactivar Temporalmente

**Endpoint**: `PATCH /api/v1/companies/{company_id}/activate`

```bash
curl -X PATCH "http://localhost:8000/api/v1/companies/42/activate" \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false,
    "reason": "Temporalmente sin operaciones de reclutamiento"
  }'
```

**Efectos de Desactivación**:
- ✅ Empresa NO aparece en búsquedas
- ✅ Empresa NO puede buscar estudiantes
- ✅ Datos se mantienen protegidos
- ✅ Puede reactivarse enviando `is_active: true`

---

## 💡 Casos de Uso Comunes

### Caso 1: Buscar Desarrolladores Full-Stack

```bash
# Buscar estudiantes con múltiples habilidades
curl -X GET "http://localhost:8000/api/v1/companies/42/search-students" \
  -H "X-API-Key: your-api-key-here" \
  -G \
  --data-urlencode "skills=React" \
  --data-urlencode "skills=Node.js" \
  --data-urlencode "skills=MongoDB" \
  --data-urlencode "experience_level=mid" \
  --data-urlencode "limit=20"
```

### Caso 2: Buscar Candidatos por Ubicación

```bash
# Filtrar por ciudad específica
curl -X GET "http://localhost:8000/api/v1/companies/42/search-students?location=Rosario&limit=15" \
  -H "X-API-Key: your-api-key-here"
```

### Caso 3: Explorar Habilidades Blandas

```bash
# Buscar líderes y comunicadores
curl -X GET "http://localhost:8000/api/v1/companies/42/search-students" \
  -H "X-API-Key: your-api-key-here" \
  -G \
  --data-urlencode "soft_skills=Liderazgo" \
  --data-urlencode "soft_skills=Comunicación" \
  --data-urlencode "limit=25"
```

### Caso 4: Identificar Especialistas Data Science

```bash
# Buscar perfiles de data science
curl -X GET "http://localhost:8000/api/v1/companies/42/search-students" \
  -H "X-API-Key: your-api-key-here" \
  -G \
  --data-urlencode "skills=Python" \
  --data-urlencode "skills=SQL" \
  --data-urlencode "skills=Machine Learning" \
  --data-urlencode "skills=Data Visualization" \
  --data-urlencode "limit=10"
```

---

## 🔧 Troubleshooting

### Problema 1: "Error 403 Forbidden" al Buscar Estudiantes

**Causa**: La empresa no está verificada

**Solución**:
```bash
# Verificar estado de verificación
curl -X GET "http://localhost:8000/api/v1/companies/42" \
  -H "X-API-Key: your-api-key-here"

# Buscar campo "is_verified": false
# Contactar a: contacto@ing.unrc.edu.mx
```

**Enviar Documentación de Verificación**:
1. RFC (Registro Federal de Contribuyentes)
2. Comprobante de domicilio reciente
3. Identificación del contacto responsable
4. Esperar confirmación del administrador (48-72 horas)

---

### Problema 2: "Error 409 Conflict" - Email Duplicado

**Causa**: Ya existe una empresa con ese email

**Solución**:
```bash
# Verificar si existe previamente
curl -X GET "http://localhost:8000/api/v1/companies?search=tu-email@empresa.mx" \
  -H "X-API-Key: your-api-key-here"

# Si existe:
# 1. Usar ese perfil existente
# 2. O contactar a admin para fusionar perfiles
```

---

### Problema 3: No Aparecen Resultados en Búsqueda

**Causa Posible 1**: Estudiantes sin habilidades coincidentes

```bash
# Probar con búsqueda más amplia
curl -X GET "http://localhost:8000/api/v1/companies/42/search-students?limit=50" \
  -H "X-API-Key: your-api-key-here"
```

**Causa Posible 2**: Sin acceso a la búsqueda

```bash
# Verificar que:
# 1. API key es válida
# 2. Empresa_id es correcto
# 3. Empresa está verificada
```

---

### Problema 4: "Error 401 Unauthorized"

**Causa**: API key inválida, expirada o no enviada

**Solución**:
```bash
# Verificar que el header está presente:
# -H "X-API-Key: YOUR-API-KEY-HERE"

# Si key está expirada:
# Contactar a administrador para renovar
```

---

### Problema 5: Respuesta Lenta en Búsquedas

**Optimizaciones**:

```bash
# 1. Reducir el límite (traer menos resultados)
curl -X GET "http://localhost:8000/api/v1/companies/42/search-students?limit=10" \
  -H "X-API-Key: your-api-key-here"

# 2. Usar filtros más específicos
curl -X GET "http://localhost:8000/api/v1/companies/42/search-students?skills=Python&skills=React&limit=20" \
  -H "X-API-Key: your-api-key-here"

# 3. Usar paginación (skip/limit)
curl -X GET "http://localhost:8000/api/v1/companies/42/search-students?skip=0&limit=20" \
  -H "X-API-Key: your-api-key-here"
```

---

## ❓ FAQ

### P: ¿Cuánto cuesta usar MoirAI?
**R**: La plataforma es gratuita para empresas colaboradoras de UNRC. Contactar a: contacto@ing.unrc.edu.mx

### P: ¿Cómo contacto a un estudiante?
**R**: A través de la plataforma en proceso (futuro). Por ahora, contactar a admin UNRC quien facilitará la conexión.

### P: ¿Cuáles son los requisitos de verificación?
**R**: 
- RFC o documento de constitución
- Identificación del contacto
- Comprobante de domicilio
- Tiempo de procesamiento: 48-72 horas

### P: ¿Puedo modificar mi email?
**R**: No, el email es inmutable por razones de auditoría. Si necesita cambiar, contactar a admin UNRC.

### P: ¿Qué datos de estudiantes puedo ver?
**R**: Solo información pública verificada:
- Nombre, ubicación, programa académico
- Habilidades técnicas y blandas
- Proyectos completados

❌ **NO DISPONIBLE**: Email personal, teléfono, dirección, notas académicas.

### P: ¿Hay límite de búsquedas?
**R**: Rate limiting de acuerdo a plan. Contactar a admin para planes enterprise.

### P: ¿Puedo descargar la lista de estudiantes?
**R**: Por seguridad (LFPDPPP), solo búsquedas y navegación en plataforma. Para reporting especial, contactar a admin.

### P: ¿Qué sucede si mi empresa se desactiva?
**R**: 
- Temporalmente: Es reversible, activa nuevamente enviando `is_active: true`
- Permanentemente: Solo admin UNRC puede hacer hard delete

### P: ¿Cómo reporto problemas o solicito features?
**R**: Crear issue en: https://github.com/HenrySpark369/MoirAI/issues

### P: ¿Hay SLA garantizado?
**R**: SLA 99.5% en horas de negocio. Para SLA custom, contactar a: contacto@ing.unrc.edu.mx

---

## 📞 Soporte

**Email**: contacto@ing.unrc.edu.mx  
**Documentación**: https://github.com/HenrySpark369/MoirAI  
**Issues**: https://github.com/HenrySpark369/MoirAI/issues  

---

**Última Actualización**: 4 de noviembre de 2025
