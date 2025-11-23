# Sistema Dinámico de API Keys - MoirAI

## 🎯 **Descripción**

Hemos implementado un sistema avanzado de gestión de API Keys que reemplaza las claves estáticas hardcodeadas por un sistema dinámico, seguro y escalable.

## ✨ **Características Principales**

### 🔑 **Generación Automática**
- API keys únicas generadas automáticamente al registrarse
- Formato seguro: `keyid_secret` con hash SHA-256
- Prefijos por rol: `stu_`, `com_`, `adm_`

### 🛡️ **Seguridad Avanzada**
- Hash de claves en base de datos (nunca se almacenan en texto plano)
- Expiración configurable (hasta 365 días)
- Límite de uso y rate limiting
- Restricción por IP (opcional)
- Revocación instantánea

### 📊 **Auditoría Completa**
- Tracking de uso de cada clave
- Registro de última actividad
- Contadores de requests
- Logs de creación y revocación

## 🚀 **Nuevos Endpoints**

### Registro de Usuarios
```bash
POST /api/v1/auth/register
```
**Registra un nuevo usuario y genera automáticamente su API key**

**Ejemplo para Estudiante:**
```json
{
  "name": "Henry Spark",
  "email": "henry.spark@gmail.com",
  "role": "student",
  "program": "Ingeniería en Sistemas"
}
```

**Ejemplo para Empresa:**
```json
{
  "name": "CryptoCorp SA",
  "email": "contacto@cryptocorp.com",
  "role": "company",
  "industry": "Tecnología, Finanzas",
  "company_size": "mediana",
  "location": "Islas Caìman"
}
```

**Respuesta:**
```json
{
  "user_id": 123,
  "name": "María García",
  "email": "maria.garcia@estudiantes.unrc.edu.mx",
  "role": "student",
  "api_key": "p6iaDFfLV_dNswLfYN_cyA_vDA_7mo2kL-ngCQm6XmXHrVKpF7Q6tv_fGdcgI1P-XQ",
  "key_id": "p6iaDFfLV_dNswLfYN_cyA",
  "expires_at": "2026-10-15T10:30:00Z",
  "scopes": ["read:own_profile", "write:own_profile", "read:jobs"]
}
```

### Gestión de API Keys
```bash
# Crear nueva API key
POST /api/v1/auth/api-keys
Authorization: X-API-Key: [tu_api_key_actual]

# Listar mis API keys
GET /api/v1/auth/api-keys
Authorization: X-API-Key: [tu_api_key_actual]

# Revocar API key
DELETE /api/v1/auth/api-keys/{key_id}
Authorization: X-API-Key: [tu_api_key_actual]

# Ver mi información
GET /api/v1/auth/me
Authorization: X-API-Key: [tu_api_key_actual]
```

## 🔧 **Cómo Usar**

### 1. **Registro de Nuevo Usuario**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Juan Pérez",
    "email": "juan.perez@estudiantes.unrc.edu.mx", 
    "role": "student",
    "program": "Licenciatura en Informática"
  }'
```

### 2. **Usar la API Key Generada**
```bash
curl -X GET "http://localhost:8000/api/v1/students/stats" \
  -H "X-API-Key: p6iaDFfLV_dNswLfYN_cyA_vDA_7mo2kL-ngCQm6XmXHrVKpF7Q6tv_fGdcgI1P-XQ"
```

### 3. **Crear API Keys Adicionales**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/api-keys" \
  -H "X-API-Key: [tu_api_key_actual]" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Clave para aplicación móvil",
    "description": "API key para la app móvil del estudiante",
    "expires_days": 90,
    "rate_limit": 500
  }'
```

## 🔒 **Permisos por Rol**

### Estudiante (`student`)
- `read:own_profile` - Ver su propio perfil
- `write:own_profile` - Editar su propio perfil
- `read:jobs` - Buscar trabajos
- `read:public_students` - Ver perfiles públicos de otros estudiantes

### Empresa (`company`)
- `read:students` - Buscar y ver estudiantes
- `read:jobs` - Ver trabajos publicados
- `write:jobs` - Publicar y gestionar vacantes
- `read:own_profile` - Ver su propio perfil
- `write:own_profile` - Editar su propio perfil

### Administrador (`admin`)
- `read:all` - Acceso total de lectura
- `write:all` - Acceso total de escritura
- `admin:all` - Funciones administrativas
- `manage:users` - Gestión de usuarios
- `manage:api_keys` - Gestión de claves

## 📈 **Ventajas del Nuevo Sistema**

### ✅ **Vs Sistema Anterior**
| Aspecto | Sistema Anterior | Sistema Nuevo |
|---------|------------------|---------------|
| **Generación** | Manual/Hardcoded | Automática |
| **Seguridad** | Texto plano en .env | Hash SHA-256 en BD |
| **Gestión** | Editar archivos | API endpoints |
| **Expiración** | No | Configurable |
| **Auditoría** | Básica | Completa |
| **Revocación** | Reiniciar servidor | Instantánea |
| **Escalabilidad** | Limitada | Ilimitada |

### 🚀 **Beneficios**
- **Seguridad**: Claves nunca almacenadas en texto plano
- **Usabilidad**: Registro automático de usuarios 
- **Gestión**: Interface web para administrar claves
- **Monitoreo**: Métricas detalladas de uso
- **Compliance**: Auditoría completa para LFPDPPP
- **Escalabilidad**: Soporte para miles de usuarios

## 🔄 **Compatibilidad**

El nuevo sistema mantiene **compatibilidad completa** con las API keys estáticas del `.env`:
- `admin-key-123-change-me`
- `student-key-789-change-me` 
- `company-key-456-change-me`

Estas claves siguen funcionando para pruebas y desarrollo.

## 🏃‍♂️ **Migración Completada**

- ✅ Base de datos actualizada con nuevas tablas
- ✅ Usuarios existentes migrados automáticamente
- ✅ API keys generadas para todos los usuarios
- ✅ Sistema de autenticación híbrido funcionando
- ✅ Endpoints de gestión disponibles en `/docs`

## 📚 **Próximos Pasos**

1. **Entregar claves** a usuarios existentes
2. **Configurar notificaciones** para expiración
3. **Implementar dashboard** de gestión de claves
4. **Migrar completamente** desde claves estáticas
5. **Agregar 2FA** para administradores

¡El sistema está listo para usar! 🎉
