# 📖 MoirAI - User Guide

**Plataforma de Vinculación Laboral Universitaria**

---

## 🎯 ¿Qué es MoirAI?

MoirAI es una plataforma inteligente que conecta estudiantes universitarios con oportunidades laborales utilizando:

- **Análisis semántico de CVs** - Detectamos competencias incluso sin mencionarlas explícitamente
- **Soft Skills inferidas** - Identificamos liderazgo, adaptabilidad, trabajo en equipo
- **Matching inteligente** - Basado en compatibilidad real, no solo palabras clave

---

## 👥 Roles de Usuario

### 1️⃣ Estudiante

**¿Quién?** Alumnos de universidades UNRC  
**¿Qué puedo hacer?**

- Crear perfil con CV (PDF o Word)
- Ver vacantes recomendadas basadas en mis habilidades
- Aplicar a posiciones
- Trackear mi progreso de búsqueda
- Ver feedback de empresas

**Flujo principal:**
```
Registrarse → Subir CV → Ver Recomendaciones → Aplicar → Seguimiento
```

### 2️⃣ Empresa

**¿Quién?** Departamento de RRHH  
**¿Qué puedo hacer?**

- Crear cuenta empresa verificada
- Publicar posiciones de trabajo
- Ver candidatos anónimos (hasta que apliquen)
- Filtrar por skills, experiencia, ubicación
- Entrevistar candidatos
- Dar feedback

**Flujo principal:**
```
Registrarse → Publicar Vacante → Ver Candidatos → Entrevista → Contratación
```

### 3️⃣ Administrador

**¿Quién?** Staff UNRC  
**¿Qué puedo hacer?**

- Dashboard de métricas
- Gestionar usuarios
- Ver reportes de placement
- Configurar sistema
- Audit logs

---

## 🚀 Quick Start

### Para Estudiantes

#### Paso 1: Registro
```
1. Ir a https://moirai.unrc.edu.ar
2. Click "Crear cuenta"
3. Ingresar email (@alumnos.unrc.edu.ar)
4. Confirmar email
5. Crear contraseña
```

#### Paso 2: Completar Perfil
```
1. Subir tu CV (PDF o Word)
   - El sistema analizará automáticamente:
     * Educación
     * Experiencia
     * Habilidades técnicas
     * Habilidades blandas (inferidas)
     * Idiomas
2. Revisar información extraída
3. Editar si es necesario
```

#### Paso 3: Explorar Vacantes
```
1. Dashboard → "Recomendaciones"
2. Ver vacantes sugeridas
3. Filtrar por:
   - Ubicación
   - Tipo de trabajo
   - Experiencia requerida
```

#### Paso 4: Aplicar
```
1. Click en vacante
2. Revisar detalles
3. Click "Aplicar"
4. Seguimiento automático
```

---

### Para Empresas

#### Paso 1: Registro
```
1. Click "Registrar Empresa"
2. Ingresar datos empresariales
3. Verificar dominio email
4. Esperar aprobación UNRC
```

#### Paso 2: Publicar Vacante
```
1. Dashboard → "Nueva Vacante"
2. Completar:
   - Título del puesto
   - Descripción
   - Requisitos (skills)
   - Ubicación
   - Salario (opcional)
   - Tipo (Full-time, Part-time, etc)
3. Publicar
```

#### Paso 3: Revisar Candidatos
```
1. Dashboard → "Mis Candidatos"
2. Ver lista de candidatos anónimos
3. Filtrar por:
   - Score de compatibilidad
   - Habilidades
   - Experiencia
4. Click en candidato → Ver CV anonimizado
5. Si interesa → Contactar
```

---

## 🔍 Entender el Matching

### ¿Cómo calcula MoirAI la compatibilidad?

**El Score (0-100)**

```
Score = (Habilidades Técnicas + Experiencia + Soft Skills) / 3

Ejemplo:
Vacante busca: Python, AWS, Liderazgo
Candidato tiene:
  - Python ✅ (90%)
  - AWS ❌ (0%)
  - Liderazgo ✅ (detectado en CV) (85%)
  
Score = (90 + 0 + 85) / 3 = 58%
```

### ¿Cómo detecta soft skills?

El sistema analiza tu CV en busca de indicadores:

| Soft Skill | Indicadores |
|-----------|-----------|
| **Liderazgo** | "Líder equipo", "coordiné", "supervisé", "proyecto de X personas" |
| **Adaptabilidad** | "cambio de roles", "múltiples tecnologías", "ambiente dinámico" |
| **Trabajo en equipo** | "colaboré", "equipo", "proyecto grupal", "reuniones" |
| **Comunicación** | "presenté", "documenté", "capacité", "expuse" |

---

## ⚙️ Configuración

### Privacidad

**Mi información está protegida:**
- ✅ Encriptada en tránsito (HTTPS)
- ✅ Encriptada en reposo (PostgreSQL)
- ✅ Empresas ven datos anonimizados
- ✅ Solo nombre si aplicas

### Preferencias

**Para Estudiantes:**
- [ ] Email notifications para nuevas oportunidades
- [ ] Recibir feedback de empresas
- [ ] Visibilidad pública del perfil

**Para Empresas:**
- [ ] Notificaciones de nuevas aplicaciones
- [ ] Resúmenes semanales
- [ ] Alertas de top candidates

---

## ❓ Preguntas Frecuentes

### 📝 CV
**P: ¿Qué formatos de CV acepta?**  
R: PDF y Word (.docx). Máximo 5MB.

**P: ¿Por qué el CV no se procesa?**  
R: Verifica que tenga al menos 50 caracteres. Si persiste, contacta support.

### 🎯 Matching
**P: ¿Por qué no veo vacantes?**  
R: Peut ser:
- Tu CV tiene pocos datos (agregar más detalles)
- No hay vacantes que coincidan en tu ubicación
- Las empresas no están buscando tu perfil aún

**P: ¿Puedo mejorar mi score?**  
R: Sí:
- Agregar más detalles a tu CV
- Incluir proyectos relevantes
- Detallar habilidades técnicas
- Mencionar logros (números, impacto)

### 💼 Aplicaciones
**P: ¿Cuántas vacantes puedo aplicar?**  
R: Ilimitadas. Pero recomienda ser selectivo.

**P: ¿Qué pasa después de aplicar?**  
R: La empresa recibe tu candidatura y decide si entrevistarte.

### 🔐 Seguridad
**P: ¿Dónde ves mis datos?**  
R: Solo empleados autorizados de MoirAI. Nunca lo compartimos.

**P: ¿Puedo eliminar mis datos?**  
R: Sí. Dashboard → Configuración → "Eliminar cuenta"

---

## 📞 Soporte

### Recursos

- **Help Center:** https://help.moirai.unrc.edu.ar
- **Email:** support@moirai.unrc.edu.ar
- **WhatsApp:** +54 9 358 1234567
- **Chat en vivo:** Disponible de Lun-Vie 9-18

### Reportar Problemas

1. Click en tu avatar → Soporte
2. Seleccionar tipo de problema
3. Describir detalles
4. Adjuntar screenshot si aplica
5. Enviar

Respuesta esperada: < 24 horas

---

## 🎓 Tips para Estudiantes

### Para Mejorar tu Perfil

1. **Sé detallado:**
   - "Python" ❌
   - "Python (3 años, Django, FastAPI, testing)" ✅

2. **Incluye números:**
   - "Mejoré performance" ❌
   - "Mejoré performance 40% optimizando queries" ✅

3. **Menciona impacto:**
   - "Trabajé en proyecto web" ❌
   - "Desarrollé plataforma web usada por 1000+ usuarios" ✅

4. **Agrupa habilidades:**
   - Separa: Backend, Frontend, Data, DevOps
   - Prioriza por relevancia

### Para Acelerar Contratación

1. Aplicar dentro de 48h de que sale vacante
2. Personalizar cada aplicación
3. Responder rápido a empresas
4. Ser disponible para entrevistas

---

## 📊 Métricas de Mi Búsqueda

**Dashboard personal muestra:**
- Vacantes vistas: X
- Aplicaciones: Y
- Entrevistas conseguidas: Z
- Tasa de respuesta de empresas: A%
- Tiempo promedio a contratación: B días

---

## 🚨 Términos de Servicio

Al usar MoirAI aceptas:

- ✅ Datos personales procesados según GDPR
- ✅ Información académica verificada
- ✅ Privacidad de candidatos protegida
- ✅ Prohibido: Spam, datos falsos, fraude

---

**Última actualización:** 21 de Noviembre de 2025  
**Versión:** 1.0 MVP  
**Estado:** En desarrollo activo

