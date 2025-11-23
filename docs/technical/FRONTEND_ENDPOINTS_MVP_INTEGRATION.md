# 📱 Frontend Endpoints MVP - Guía de Integración

**Rama**: `feature/frontend-integration-mvp`  
**Versión**: 1.0.0  
**Última actualización**: 15 de noviembre de 2025

---

## 🎯 Resumen de Endpoints Disponibles

Todos los endpoints requieren el header `Authorization: Bearer {token}` excepto los de autenticación.

---

## 🔐 AUTENTICACIÓN

### Registro
```javascript
// POST /auth/register
const response = await apiClient.post('/auth/register', {
  email: 'user@example.com',
  password: 'secure_password',
  first_name: 'Juan',
  last_name: 'Pérez',
  user_type: 'student' // o 'company', 'admin'
})

// Response
{
  token: "eyJhbGciOiJIUzI1NiIs...",
  user: {
    id: 1,
    email: 'user@example.com',
    first_name: 'Juan',
    user_type: 'student'
  }
}
```

### Login
```javascript
// POST /auth/login
const response = await apiClient.post('/auth/login', {
  email: 'user@example.com',
  password: 'secure_password'
})

// Response
{
  token: "eyJhbGciOiJIUzI1NiIs...",
  user: { id: 1, email: '...', user_type: 'student' }
}
```

### Obtener Usuario Actual
```javascript
// GET /auth/me
const user = await apiClient.get('/auth/me')

// Response
{
  id: 1,
  email: 'user@example.com',
  first_name: 'Juan',
  last_name: 'Pérez',
  user_type: 'student'
}
```

### Logout
```javascript
// POST /auth/logout
await apiClient.post('/auth/logout')
```

---

## 👨‍🎓 ESTUDIANTES

### Obtener Perfil
```javascript
// GET /students/{student_id}
const profile = await apiClient.get(`/students/1`)

// Response
{
  id: 1,
  user_id: 1,
  email: 'student@example.com',
  phone: '5551234567',
  location: 'Ciudad de México',
  bio: 'Estudiante de Ingeniería en Sistemas',
  technical_skills: ['Python', 'JavaScript', 'React'],
  soft_skills: ['Liderazgo', 'Comunicación'],
  projects: [
    {
      name: 'Proyecto 1',
      description: 'Descripción del proyecto',
      technologies: ['Python', 'Flask']
    }
  ],
  resume_uploaded: true,
  created_at: '2025-01-15T10:30:00'
}
```

### Actualizar Perfil
```javascript
// PUT /students/{student_id}
const updated = await apiClient.put(`/students/1`, {
  phone: '5559876543',
  location: 'Guadalajara',
  bio: 'Nuevo bio',
  technical_skills: ['Python', 'JavaScript', 'React', 'Django'],
  soft_skills: ['Liderazgo', 'Comunicación', 'Trabajo en equipo']
})
```

### Upload de CV
```javascript
// POST /students/{student_id}/upload-resume
const file = document.getElementById('resume-input').files[0]

const result = await apiClient.uploadFile(
  `/students/1/upload-resume`,
  file
)

// Response
{
  success: true,
  filename: 'juan_perez_cv.pdf',
  size: 245000,
  extracted_skills: {
    technical: ['Python', 'JavaScript', 'React'],
    soft: ['Liderazgo', 'Comunicación'],
    projects: ['Proyecto AI', 'Proyecto Web']
  }
}
```

---

## 💼 OPORTUNIDADES / JOBS

### Buscar Empleos
```javascript
// GET /jobs/search?keyword=Python&location=Mexico City&limit=20&skip=0
const jobs = await apiClient.get(
  '/jobs/search?keyword=Python&location=Mexico%20City&limit=20'
)

// Response
{
  total: 150,
  jobs: [
    {
      id: 1,
      external_job_id: 'OCC123456',
      title: 'Senior Python Developer',
      company: 'TechCorp',
      location: 'Mexico City',
      description: 'Descripción breve del puesto...',
      salary_min: 50000,
      salary_max: 80000,
      currency: 'MXN',
      work_mode: 'hybrid',
      job_type: 'full_time',
      skills: ['Python', 'Django', 'PostgreSQL'],
      source: 'occ.com.mx',
      published_at: '2025-01-15T10:00:00'
    },
    // ... más empleos
  ],
  query_used: 'Python'
}
```

### Obtener Detalles del Empleo
```javascript
// GET /jobs/{job_id}
const jobDetail = await apiClient.get('/jobs/1')

// Response
{
  id: 1,
  external_job_id: 'OCC123456',
  title: 'Senior Python Developer',
  company: 'TechCorp',
  location: 'Mexico City',
  description: 'Descripción completa del puesto...',
  requirements: '...',
  salary_min: 50000,
  salary_max: 80000,
  currency: 'MXN',
  work_mode: 'hybrid',
  job_type: 'full_time',
  skills: ['Python', 'Django', 'PostgreSQL', 'AWS'],
  benefits: ['Health Insurance', 'Remote Work', 'Flexible Hours'],
  source: 'occ.com.mx',
  published_at: '2025-01-15T10:00:00',
  url: 'https://occ.com.mx/...'
}
```

### Iniciar Scraping (Admin)
```javascript
// POST /jobs/scrape
// Requiere X-API-Key header con valor que empiece con 'admin_'
const result = await apiClient.post('/jobs/scrape', {
  keywords: ['Python', 'JavaScript'],
  location: 'Mexico City',
  limit: 100
})

// Response
{
  status: 'queued',
  job_id: 'scrape_12345',
  total_jobs_found: 150,
  message: 'Scraping iniciado en segundo plano'
}
```

---

## 🎯 MATCHING & RECOMENDACIONES

### Obtener Recomendaciones de Empleos
```javascript
// POST /matching/recommendations
const recommendations = await apiClient.post('/matching/recommendations', {
  student_id: 1,
  location: 'Mexico City',
  limit: 10
})

// Response
{
  student_id: 1,
  total_found: 45,
  jobs: [
    {
      id: 1,
      title: 'Senior Python Developer',
      company: 'TechCorp',
      matching_score: 0.92,
      matching_reason: 'Excelente coincidencia en Python y Django',
      salary_min: 50000,
      salary_max: 80000
    },
    // ... más empleos ordenados por score
  ],
  query_used: 'Extracción de CV'
}
```

### Calcular Score de Compatibilidad
```javascript
// GET /matching/student/{student_id}/matching-score?job_title=...&job_description=...
const score = await apiClient.get(
  `/matching/student/1/matching-score?job_title=Python%20Developer&job_description=...`
)

// Response
{
  matching_score: 0.87,
  base_score: 0.75,
  boost_applied: 0.12,
  matching_skills: ['Python', 'Django', 'PostgreSQL'],
  matching_projects: ['Proyecto AI'],
  boost_details: {
    resume_score: 0.95,
    location_match: true,
    experience_level_match: true
  }
}
```

### Filtrar Estudiantes por Criterios (Company/Admin)
```javascript
// POST /matching/filter-by-criteria
const students = await apiClient.post('/matching/filter-by-criteria', {
  skills: ['Python', 'JavaScript'],
  location: 'Mexico City',
  experience_level: 'junior',
  job_type: 'full_time'
})

// Response
{
  total: 25,
  students: [
    {
      id: 1,
      name: 'Juan Pérez',
      email: 'juan@example.com',
      location: 'Mexico City',
      matching_score: 0.89,
      matching_skills: ['Python', 'JavaScript'],
      matching_projects: [],
      bio: '...'
    },
    // ... más estudiantes
  ]
}
```

### Obtener Estudiantes Destacados (Company/Admin)
```javascript
// GET /matching/featured-students?limit=10
const featured = await apiClient.get('/matching/featured-students?limit=10')

// Response
{
  students: [
    {
      id: 1,
      name: 'Juan Pérez',
      email: 'juan@example.com',
      technical_skills: ['Python', 'JavaScript'],
      soft_skills: ['Liderazgo'],
      rating: 4.8,
      projects_count: 5
    },
    // ... más estudiantes
  ]
}
```

---

## 🏢 EMPRESAS

### Obtener Información de Empresa
```javascript
// GET /companies/{company_id}
const company = await apiClient.get('/companies/1')

// Response
{
  id: 1,
  name: 'TechCorp',
  email: 'hr@techcorp.com',
  phone: '5551234567',
  website: 'www.techcorp.com',
  industry: 'Technology',
  size: '500-1000',
  description: 'Descripción de la empresa...',
  location: 'Mexico City',
  verified: true
}
```

### Búsqueda de Estudiantes (Company)
```javascript
// GET /companies/search-students?skills=Python&location=Mexico%20City
const students = await apiClient.get(
  '/companies/search-students?skills=Python&location=Mexico%20City'
)

// Response
{
  total: 30,
  students: [
    {
      id: 1,
      name: 'Juan Pérez',
      email: 'juan@example.com',
      skills: ['Python', 'Django'],
      location: 'Mexico City',
      availability: 'available'
    },
    // ... más estudiantes
  ]
}
```

---

## 📊 APLICACIONES (Jobs Applications)

### Aplicar a un Empleo
```javascript
// POST /applications
const application = await apiClient.post('/applications', {
  student_id: 1,
  job_id: 1,
  cover_letter: 'Carta de presentación...'
})

// Response
{
  id: 1,
  student_id: 1,
  job_id: 1,
  status: 'applied',
  applied_at: '2025-01-15T10:30:00',
  message: 'Solicitud enviada exitosamente'
}
```

### Obtener Mis Aplicaciones
```javascript
// GET /applications/my-applications
const myApplications = await apiClient.get('/applications/my-applications')

// Response
{
  total: 15,
  applications: [
    {
      id: 1,
      job: {
        id: 1,
        title: 'Senior Python Developer',
        company: 'TechCorp'
      },
      status: 'applied',
      applied_at: '2025-01-15T10:30:00',
      last_update: '2025-01-15T10:30:00'
    },
    // ... más aplicaciones
  ]
}
```

---

## 🔔 NOTIFICACIONES

### Obtener Notificaciones
```javascript
// GET /notifications?limit=20&unread_only=false
const notifications = await apiClient.get(
  '/notifications?limit=20&unread_only=false'
)

// Response
{
  total: 50,
  unread: 5,
  notifications: [
    {
      id: 1,
      type: 'job_recommendation',
      title: 'Nueva oportunidad: Senior Python Developer',
      message: '...',
      read: false,
      created_at: '2025-01-15T10:30:00',
      job_id: 1
    },
    // ... más notificaciones
  ]
}
```

### Marcar Notificación como Leída
```javascript
// PUT /notifications/{notification_id}/read
await apiClient.put('/notifications/1/read')
```

---

## 📋 EJEMPLOS DE IMPLEMENTACIÓN

### Ejemplo 1: Login y Cargar Perfil

```javascript
// 1. Login
try {
  const loginResponse = await authManager.login('user@example.com', 'password')
  notificationManager.success('¡Sesión iniciada!')
  
  // 2. Cargar perfil del estudiante
  const profile = await apiClient.get(`/students/${loginResponse.user.id}`)
  console.log('Perfil cargado:', profile)
  
  // 3. Mostrar datos en la UI
  document.getElementById('user-name').textContent = profile.bio
  
} catch (error) {
  notificationManager.error(`Error: ${error.message}`)
}
```

### Ejemplo 2: Búsqueda de Empleos con Filtros

```javascript
async function searchJobs() {
  const keyword = document.getElementById('search-keyword').value
  const location = document.getElementById('search-location').value
  
  notificationManager.loading('Buscando empleos...')
  
  try {
    const results = await apiClient.get(
      `/jobs/search?keyword=${keyword}&location=${location}&limit=20`
    )
    
    notificationManager.hideLoading()
    notificationManager.success(`Se encontraron ${results.total} empleos`)
    
    // Renderizar resultados
    displayJobs(results.jobs)
    
  } catch (error) {
    notificationManager.hideLoading()
    notificationManager.error(`Error en búsqueda: ${error.message}`)
  }
}
```

### Ejemplo 3: Upload de CV

```javascript
async function uploadResume() {
  const fileInput = document.getElementById('resume-input')
  const file = fileInput.files[0]
  
  if (!file) {
    notificationManager.warning('Selecciona un archivo')
    return
  }
  
  notificationManager.loading('Subiendo CV...')
  
  try {
    const userId = authManager.getUserId()
    const result = await apiClient.uploadFile(
      `/students/${userId}/upload-resume`,
      file
    )
    
    notificationManager.hideLoading()
    notificationManager.success('CV subido exitosamente')
    
    // Mostrar skills extraídas
    console.log('Skills técnicas:', result.extracted_skills.technical)
    console.log('Skills blandas:', result.extracted_skills.soft)
    
  } catch (error) {
    notificationManager.hideLoading()
    notificationManager.error(`Error al subir CV: ${error.message}`)
  }
}
```

### Ejemplo 4: Obtener Recomendaciones

```javascript
async function loadRecommendations() {
  const studentId = authManager.getUserId()
  
  try {
    const recommendations = await apiClient.post(
      '/matching/recommendations',
      {
        student_id: studentId,
        limit: 10
      }
    )
    
    notificationManager.info(
      `Tienes ${recommendations.total_found} empleos disponibles`
    )
    
    displayRecommendedJobs(recommendations.jobs)
    
  } catch (error) {
    notificationManager.error(`Error al cargar recomendaciones: ${error.message}`)
  }
}
```

---

## ✅ Checklist de Integración

- [ ] Incluir `api-client.js` en templates
- [ ] Incluir `auth-manager.js` en templates
- [ ] Incluir `notification-manager.js` en templates
- [ ] Incluir `notifications.css` en templates
- [ ] Configurar variable global `API_BASE_URL`
- [ ] Implementar página de login
- [ ] Implementar dashboard
- [ ] Implementar búsqueda de empleos
- [ ] Implementar perfil de usuario
- [ ] Implementar upload de CV
- [ ] Testing en todos los navegadores
- [ ] Deploy a producción

---

**Status**: 🎯 LISTO PARA USAR

Todos los endpoints están documentados y listos para integrar en el frontend.
