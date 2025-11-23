# 🧪 Checklist de Testing Frontend - MoirAI MVP

**Rama**: `feature/frontend-mvp`  
**Commit Base**: `b31fb3f39df1d97792bd041c519bffb143b21c74`  
**Fecha**: 15 de noviembre de 2025  
**Estado**: ✅ LISTO PARA TESTING

---

## 📋 Índice

1. [Autenticación](#autenticación)
2. [Validación de Formularios](#validación-de-formularios)
3. [Dashboard](#dashboard)
4. [Perfil de Usuario](#perfil-de-usuario)
5. [Gestión de Empleos](#gestión-de-empleos)
6. [Almacenamiento Local](#almacenamiento-local)
7. [Responsividad](#responsividad)
8. [Seguridad](#seguridad)
9. [Performance](#performance)
10. [Accesibilidad](#accesibilidad)

---

## 🔐 Autenticación

### Login - Credenciales Válidas
- [ ] Email válido acepta entrada
- [ ] Contraseña se oculta (eye toggle funciona)
- [ ] Botón submit se deshabilita mientras se envía
- [ ] POST /api/v1/auth/login se ejecuta
- [ ] Token JWT se guarda en localStorage
- [ ] Redirección a /dashboard ocurre
- [ ] Notificación "¡Bienvenido!" aparece

**Pasos**:
1. Ir a `/login`
2. Ingresar email: `test@example.com`
3. Ingresar password: `Test123456`
4. Hacer clic en "Iniciar Sesión"
5. Esperar redirección

**Resultado Esperado**: Redirigido a dashboard con usuario cargado

---

### Login - Credenciales Inválidas
- [ ] Email inválido muestra error
- [ ] Contraseña en blanco muestra error
- [ ] POST falla con 401
- [ ] Notificación "Email o contraseña incorrectos"
- [ ] Usuario permanece en login
- [ ] Token NO se guarda

**Pasos**:
1. Ir a `/login`
2. Ingresar email: `invalid@test.com`
3. Ingresar password: `wrongpass`
4. Hacer clic en "Iniciar Sesión"

**Resultado Esperado**: Mensaje de error, sin redirección

---

### Registro - Datos Válidos
- [ ] Rol se puede seleccionar (Estudiante/Empresa)
- [ ] Nombre y apellido se aceptan
- [ ] Email válido se valida
- [ ] Contraseña requiere: 8+ chars, mayúscula, minúscula, número
- [ ] Confirmación de contraseña coincide
- [ ] Términos checkbox funciona
- [ ] POST /api/v1/auth/register se ejecuta
- [ ] Nuevo usuario se crea
- [ ] Auto-login después de registro
- [ ] Redirección a /dashboard

**Pasos**:
1. Ir a `/login`
2. Hacer clic en tab "Registrarse"
3. Seleccionar rol: "Estudiante"
4. Ingresar nombre: "Juan"
5. Ingresar apellido: "Pérez"
6. Ingresar email: `juan@test.com`
7. Ingresar password: `Password123`
8. Confirmar password
9. Aceptar términos
10. Hacer clic en "Crear Cuenta"

**Resultado Esperado**: Cuenta creada, login automático, redirección a dashboard

---

### Remember Me
- [ ] Checkbox se marca/desmarca
- [ ] Email se guarda en localStorage si está marcado
- [ ] Email se carga en siguiente visita
- [ ] Email se borra si no está marcado

**Pasos**:
1. En login, marcar "Recuérdame"
2. Ingresar email: `test@example.com`
3. Cerrar sesión
4. Volver a `/login`
5. Email debe estar precargado

---

### Forgot Password
- [ ] Link "¿Olvidaste contraseña?" visible
- [ ] Prompts para email
- [ ] Validación de email
- [ ] POST /auth/forgot-password se ejecuta
- [ ] Notificación de éxito aparece

---

### Logout
- [ ] Botón de logout visible en navbar
- [ ] Click limpia localStorage (token)
- [ ] Redirección a home (`/`)
- [ ] Vuelve a requerir login

---

## ✅ Validación de Formularios

### Email
- [ ] Acepta: `user@example.com` ✓
- [ ] Rechaza: `invalid-email` ✗
- [ ] Rechaza: `@example.com` ✗
- [ ] Rechaza: `user@` ✗
- [ ] Error message aparece en tiempo real

---

### Contraseña
- [ ] Mínimo 8 caracteres (muestra error si < 8)
- [ ] Requiere mayúscula (muestra error si no tiene)
- [ ] Requiere minúscula (muestra error si no tiene)
- [ ] Requiere número (muestra error si no tiene)
- [ ] Eye toggle muestra/oculta password

---

### Confirmación de Contraseña
- [ ] Debe coincidir con contraseña
- [ ] Error si no coinciden
- [ ] Sin error si coinciden

---

### Campos de Texto
- [ ] No acepta valores vacíos
- [ ] Valida en blur (salir del campo)
- [ ] Valida en tiempo real si hay error
- [ ] Verde checkmark si es válido

---

### Teléfono
- [ ] Acepta: `+56 9 1234 5678` ✓
- [ ] Rechaza: `12345` ✗ (muy corto)
- [ ] Acepta números variados

---

## 📊 Dashboard

### Carga de Dashboard
- [ ] Si NO autenticado: redirige a `/login`
- [ ] Si autenticado: carga contenido
- [ ] "Cargando dashboard..." aparece
- [ ] Se oculta cuando termina de cargar
- [ ] Error si falla: muestra notificación

---

### Información del Usuario
- [ ] Nombre aparece en welcome section
- [ ] Subtítulo según rol (Estudiante/Empresa)
- [ ] Email visible en navbar
- [ ] Foto de perfil (avatar)

---

### Tarjetas de Estadísticas
- [ ] **Aplicaciones**: Muestra número correcto
  - [ ] GET /applications/my-applications funciona
  - [ ] Cuenta coincide con tabla

- [ ] **Score Match**: Muestra porcentaje
  - [ ] GET /matching/student/{id}/matching-score funciona
  - [ ] Formato: "0%" - "100%"

- [ ] **Recomendaciones**: Muestra número
  - [ ] POST /matching/recommendations funciona
  - [ ] Número coincide con cards

- [ ] **CV Actualizado**: Muestra "Sí" o "No"
  - [ ] Refleja estado real del perfil

---

### Empleos Recomendados
- [ ] Grid de tarjetas aparece
- [ ] Cada tarjeta muestra:
  - [ ] Título del empleo
  - [ ] Nombre de empresa
  - [ ] Ubicación
  - [ ] Modalidad (Presencial/Híbrido/Remoto)
  - [ ] **Match Score** (ej: 95% Match)

- [ ] Botones funcionan:
  - [ ] "Ver" abre modal con detalles
  - [ ] "Aplicar" envía aplicación

- [ ] Si no hay recomendaciones:
  - [ ] Muestra "Sin recomendaciones"
  - [ ] Botón "Completar perfil"

---

### Tabla de Aplicaciones
- [ ] Muestra columnas: Empleo, Empresa, Estado, Fecha, Acciones
- [ ] Estados mostrados correctamente:
  - [ ] pending = "Pendiente" (amarillo)
  - [ ] accepted = "Aceptada" (verde)
  - [ ] rejected = "Rechazada" (rojo)
  - [ ] interview = "Entrevista" (naranja)

- [ ] Fecha formateada en español
- [ ] Botón "Ver" funciona para cada fila
- [ ] Si no hay aplicaciones: muestra empty state

---

### Modal de Detalles del Empleo
- [ ] Se abre al hacer clic en "Ver"
- [ ] Muestra:
  - [ ] Título
  - [ ] Empresa
  - [ ] Ubicación
  - [ ] Modalidad
  - [ ] Descripción
  - [ ] Salario (rango)
  - [ ] Requisitos (lista)

- [ ] Botón "Aplicar Ahora" funciona
- [ ] Se puede cerrar con X o Escape
- [ ] Click fuera cierra modal

---

### Refresh de Dashboard
- [ ] Función `refreshDashboard()` recarga datos
- [ ] Loading appears mientras se actualiza
- [ ] Notificación de éxito después

---

## 👤 Perfil de Usuario

### Información Personal
- [ ] Campos se cargan con datos actuales
- [ ] Nombre editable y guardable
- [ ] Apellido editable y guardable
- [ ] Email NO es editable (gris)
- [ ] Teléfono editable
- [ ] Biografía editable (textarea)

---

### Upload de CV
- [ ] Drag & drop funciona
- [ ] Click abre file picker
- [ ] Acepta: `.pdf`, `.docx`
- [ ] Rechaza otros tipos
- [ ] Valida tamaño máximo (5MB)
- [ ] Progress bar muestra durante upload
- [ ] POST /students/{id}/upload-resume funciona

---

### CV Status
- [ ] Muestra status después de upload:
  - [ ] Nombre del archivo
  - [ ] Fecha de carga
  - [ ] Botón "Descargar"
  - [ ] Botón "Eliminar"

- [ ] Download funciona (descarga archivo)
- [ ] Delete elimina y pide confirmación

---

### Habilidades Inferidas (NLP)
- [ ] Se cargan después de upload de CV
- [ ] Cada habilidad muestra:
  - [ ] Nombre
  - [ ] Porcentaje de confianza (ej: 95%)
  - [ ] Color según tipo (técnica/blanda)
  - [ ] Botón X para remover

- [ ] Al remover habilidad: se elimina de vista
- [ ] Si no hay habilidades: muestra empty state

---

### Información Académica (Solo Estudiantes)
- [ ] Visible solo si rol = estudiante
- [ ] Carrera seleccionable (dropdown)
- [ ] Año seleccionable (1-5)
- [ ] Se guardan al hacer submit

---

### Seguridad
- [ ] Botón "Cambiar Contraseña" abre prompt
- [ ] Pide contraseña actual
- [ ] Pide nueva contraseña
- [ ] Pide confirmación
- [ ] Valida nueva contraseña
- [ ] POST /auth/change-password funciona

---

### Zona de Peligro
- [ ] "Eliminar Cuenta" visible pero deshabilitado (fase 2)
- [ ] Texto de advertencia presente

---

### Sidebar
- [ ] Avatar con iniciales
- [ ] Nombre mostrado
- [ ] Rol mostrado
- [ ] Botón "Cambiar Foto" (fase 2)
- [ ] Progress bar de perfil completado
- [ ] Links de ayuda funcionan

---

## 💼 Gestión de Empleos

### Página Oportunidades (/oportunidades)
- [ ] Conecta con /jobs/search API
- [ ] Search funciona en tiempo real
- [ ] Filtros aplican correctamente:
  - [ ] Ubicación
  - [ ] Modalidad
  - [ ] Sector
  - [ ] Nivel

- [ ] Resultados se actualizan
- [ ] Paginación funciona (si existe)

---

## 💾 Almacenamiento Local

### StorageManager
- [ ] `StorageManager.set(key, value)` funciona
- [ ] `StorageManager.get(key)` retorna valor guardado
- [ ] `StorageManager.remove(key)` borra dato
- [ ] `StorageManager.clear()` limpia todo
- [ ] Expiración automática funciona
- [ ] Prefijo "moirai_" se agrega correctamente

---

### localStorage
- [ ] Token JWT se guarda
- [ ] Token persiste entre page refreshes
- [ ] Token se limpia en logout
- [ ] Otros datos se guardan correctamente
- [ ] No hay corrupción de datos

---

### FormValidator
- [ ] `validate(type, value)` retorna objeto correcto
- [ ] `validateForm(form)` valida todos los campos
- [ ] `showError(field, message)` muestra error
- [ ] `clearError(field)` limpia error
- [ ] `setupRealtimeValidation(form)` activa validación en blur

---

## 📱 Responsividad

### Desktop (1200px+)
- [ ] Layout completo visible
- [ ] Navbar con todos los items
- [ ] Grid de 2 columnas en profile
- [ ] Sin scroll horizontal
- [ ] Botones con iconos y texto

---

### Tablet (768px - 1200px)
- [ ] Navbar se adapta
- [ ] Menú sigue visible
- [ ] Grid se ajusta (1-2 columnas)
- [ ] Elementos se reescalan
- [ ] Botones mantienen tamaño adecuado

---

### Mobile (480px - 768px)
- [ ] Navbar con hamburger menu
- [ ] Una columna de contenido
- [ ] Tablas se hacen scrollables
- [ ] Modales se adaptan
- [ ] Inputs con tamaño adecuado (16px+)

---

### Small Mobile (<480px)
- [ ] Navbar colapsado
- [ ] Texto legible
- [ ] Botones clickeables (48px mínimo)
- [ ] Sin texto cortado
- [ ] Modales a pantalla completa

---

### Dispositivos Específicos
- [ ] iPhone 12 (390x844): ✓
- [ ] iPhone SE (375x667): ✓
- [ ] Samsung Galaxy S20 (360x800): ✓
- [ ] iPad (768x1024): ✓
- [ ] iPad Pro (1024x1366): ✓

---

## 🔒 Seguridad

### Protección de Rutas
- [ ] `/login` accesible sin autenticación
- [ ] `/register` accesible sin autenticación
- [ ] `/dashboard` redirige a login si no autenticado
- [ ] `/profile` redirige a login si no autenticado

---

### Token Management
- [ ] Token se guarda en localStorage (NO en cookie por ahora)
- [ ] Token se envía en header `Authorization: Bearer {token}`
- [ ] Token expirado causa logout automático
- [ ] Refresh token funciona (si existe)

---

### CSRF Protection
- [ ] No hay vulnerabilidad CSRF visible
- [ ] Headers CORS correctos

---

### XSS Prevention
- [ ] No hay ejecución de scripts en inputs
- [ ] HTML user input está escapado
- [ ] Contenido dinámico sanitizado

---

### Contraseña
- [ ] Se transmite por HTTPS
- [ ] Validación de fortaleza en cliente
- [ ] No se muestra en HTML (type="password")

---

## ⚡ Performance

### Carga de Página
- [ ] Home (`/`): < 2s
- [ ] Login (`/login`): < 1.5s
- [ ] Dashboard (`/dashboard`): < 2s
- [ ] Profile (`/profile`): < 2s

---

### Bundle Size
- [ ] api-client.js: ~425 líneas
- [ ] auth-manager.js: ~285 líneas
- [ ] notification-manager.js: ~405 líneas
- [ ] Total JS core: < 150KB (minified)
- [ ] CSS total: < 100KB (minified)

---

### Lazy Loading
- [ ] Imágenes lazy load (si existen)
- [ ] Modales se cargan on-demand

---

### Caché
- [ ] StorageManager cachea datos
- [ ] Datos reusables no se re-fetchean
- [ ] Cache se invalida cuando es necesario

---

### Network
- [ ] Requests se comprimen (gzip)
- [ ] Responses son JSON válido
- [ ] No hay waterfall requests innecesarios

---

## ♿ Accesibilidad

### Keyboard Navigation
- [ ] Tab navega entre elementos
- [ ] Enter activa botones
- [ ] Escape cierra modales
- [ ] Focus visible en todos lados

---

### Screen Readers
- [ ] Labels asociados con inputs
- [ ] Aria-labels en iconos
- [ ] Estructura semántica correcta
- [ ] Error messages anunciados

---

### Color Contrast
- [ ] Texto vs fondo: ratio 4.5:1 mínimo
- [ ] Botones vs fondo: contrastables
- [ ] Verificar con WCAG guidelines

---

### Forma
- [ ] No dependencia solo en color
- [ ] Iconos con texto
- [ ] Errores con descripción de texto

---

## 🐛 Testing Manual Workflow

### Antes de cada test:
```bash
# 1. Limpiar localStorage
localStorage.clear()

# 2. Cerrar devtools
F12

# 3. Recargar página
Ctrl+R o Cmd+R

# 4. Notar cualquier error en console
F12 > Console
```

### Tests Prioritarios (Orden de Ejecución):
1. ✓ Autenticación (Login/Register)
2. ✓ Dashboard Load
3. ✓ Profile Editing
4. ✓ CV Upload
5. ✓ Validación de Formularios
6. ✓ Responsividad en mobile
7. ✓ Seguridad (protección de rutas)

---

## 📊 Testing Results Template

```
Date: _______________
Tester: _______________
Browser: Chrome/Firefox/Safari
Device: Desktop/Tablet/Mobile

## Autenticación
- [ ] Login: _____ (PASS/FAIL)
- [ ] Register: _____ (PASS/FAIL)
- [ ] Logout: _____ (PASS/FAIL)

## Dashboard
- [ ] Load: _____ (PASS/FAIL)
- [ ] Stats: _____ (PASS/FAIL)
- [ ] Recommendations: _____ (PASS/FAIL)

## Perfil
- [ ] Edit Info: _____ (PASS/FAIL)
- [ ] CV Upload: _____ (PASS/FAIL)
- [ ] Skills: _____ (PASS/FAIL)

## General
- [ ] Responsividad: _____ (PASS/FAIL)
- [ ] Performance: _____ (PASS/FAIL)

Issues Found:
_________________________________
```

---

## 🔍 Debugging Tips

### Console Errors
```javascript
// Ver estado de autenticación
authManager.isAuthenticated()

// Ver usuario actual
authManager.getCurrentUser()

// Ver token
localStorage.getItem('moirai_token')

// Ver todos los datos guardados
StorageManager.getAll()
```

### Network Tab
```
- Ver todas las requests a /api/v1/
- Verificar headers (Authorization, Content-Type)
- Revisar responses (status codes)
```

### Local Storage
```
DevTools > Application > Local Storage
Buscar keys con prefijo "moirai_"
```

---

## ✅ Final Checklist (Pre-Production)

- [ ] Todos los tests PASS completados
- [ ] No hay errores en console
- [ ] No hay warnings en console
- [ ] Funciona en Chrome
- [ ] Funciona en Firefox
- [ ] Funciona en Safari
- [ ] Mobile responsive confirmado
- [ ] Performance acceptable
- [ ] Seguridad verificada
- [ ] Ready para merge a main

---

**Total de test cases**: 150+  
**Tiempo estimado de testing**: 2-3 horas  
**Próxima revisión**: Después de implementar Phase 2

---

Generated: 15 de noviembre de 2025  
Version: 1.0
