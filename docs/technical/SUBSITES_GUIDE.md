# Guía de Implementación de Sub-sitios

## 🎉 Novedades

Se han agregado tres nuevos sub-sitios a la plataforma MoirAI con una estructura de navegación similar a **probecarios.com**:

### 1. **Oportunidades** (`/oportunidades`)
- Explorar oportunidades laborales disponibles
- Filtrado avanzado (ubicación, modalidad, sector, nivel de experiencia, habilidades)
- Tarjetas de empleos con porcentaje de coincidencia, salario y habilidades requeridas
- Opciones de paginación y ordenamiento

### 2. **Empresas** (`/empresas`)
- Explorar todas las empresas colaboradoras
- Filtrar por sector, tamaño, ubicación y certificaciones
- Tarjetas de empresa con estadísticas y badges
- Toggle de vista grid/lista

### 3. **Estudiantes** (`/estudiantes`)
- Descubrir perfiles de estudiantes
- Filtrar por carrera, año, disponibilidad, habilidades y experiencia
- Tarjetas de perfil de estudiante con proyectos completados
- Toggle de vista grid/lista

---

## 📁 Estructura de Archivos

```
app/frontend/templates/
├── index.html (actualizado con nuevos enlaces de navegación)
├── oportunidades.html (new)
├── empresas.html (new)
├── estudiantes.html (new)
└── admin/
    └── dashboard.html

app/frontend/static/
├── css/
│   ├── styles.css (existing)
│   └── listings.css (new - shared styles for all sub-sites)
└── js/
    └── listings.js (new - shared functionality for all sub-sites)
```

---

## 🎨 Features Implemented

### Navigation Bar
- Links to all three new sub-sites in the main navigation menu
- "Inicia Sesión" button for authentication
- Consistent brand styling across all pages

### Advanced Filtering System

#### Oportunidades (Jobs)
- **Location**: City selection dropdown
- **Modality**: Presencial, Híbrido, Remoto checkboxes
- **Sector**: Industry selection
- **Level**: Junior, Semi-Senior, Senior
- **Publication Date**: Filter by recency
- **Technologies**: Python, JavaScript, React, SQL, etc.

#### Empresas (Companies)
- **Sector**: Industry type
- **Company Size**: Startup, PyME, Empresa Grande
- **Location**: Geographic filtering
- **Certifications**: Verified, ISO, Top Employer badges
- **Open Positions**: Filter companies with active jobs

#### Estudiantes (Students)
- **Career**: Different degree programs
- **Year**: 1st to 4th year students
- **Availability**: Immediate, Upcoming weeks, Vacation
- **Technologies**: Programming languages and frameworks
- **Experience**: Projects completed, internship status

### Search Functionality
- Real-time search across all sub-sites
- Multi-field search (name, title, description, skills)

### Sorting Options
- **Jobs**: Recent, Best Match, Highest/Lowest Salary
- **Companies**: Can be extended
- **Students**: Can be extended

### View Modes (Companies & Students)
- **Grid View**: Cards layout (default)
- **List View**: Expanded table-like layout

### Pagination
- Smart pagination showing relevant page numbers
- Previous/Next navigation buttons
- Auto-scroll to top on page change

### Responsive Design
- Mobile-first approach
- Breakpoints: 480px, 768px, 1024px
- Touch-friendly filter controls

---

## 🚀 API Integration Ready

The JavaScript (`listings.js`) includes placeholder comments for API integration:

```javascript
// TODO: Replace with real API call
// fetch('/api/v1/jobs')
// fetch('/api/v1/companies')
// fetch('/api/v1/students')
```

### Recommended API Endpoints

```
GET /api/v1/jobs - Get all jobs
GET /api/v1/jobs?sector=tecnologia&location=cordoba - Filtered jobs
GET /api/v1/jobs/{id} - Get job details

GET /api/v1/companies - Get all companies
GET /api/v1/companies/{id} - Get company details

GET /api/v1/students - Get all students
GET /api/v1/students/{id} - Get student profile
```

---

## 📊 Mock Data Included

Each sub-site comes with 8 sample records for demonstration:

### Sample Jobs
- Desarrollador Python Senior
- Frontend Developer React
- Analista de Datos
- Especialista en Marketing Digital
- Administrador de Sistemas
- Contador Senior
- Especialista en RH
- QA Engineer

### Sample Companies
- TechCorp
- WebSolutions
- DataInsights
- CreativeAgency
- FinancePartners
- SysAdmin Inc
- TalentMasters
- QualityFirst

### Sample Students
- Juan García (Ing. Sistemas, 4to año)
- María López (Administración, 3er año)
- Carlos Rodríguez (Ing. Sistemas, 2do año)
- Ana Martínez (Contabilidad, 4to año)
- Diego Fernández (Ing. Eléctrica, 3er año)
- Sofia González (Ing. Sistemas, 4to año)
- Lucas Pérez (Marketing, 2do año)
- Valentina Torres (Administración, 1er año)

---

## 🔧 FastAPI Routes Added

```python
@app.get("/oportunidades")
async def oportunidades_page():
    """Jobs listing page"""

@app.get("/empresas")
async def empresas_page():
    """Companies listing page"""

@app.get("/estudiantes")
async def estudiantes_page():
    """Students listing page"""
```

---

## 🎯 Quick Start

### View the Pages
1. Start the server: `python main.py` or `uvicorn app.main:app --reload`
2. Navigate to:
   - http://localhost:8000/oportunidades
   - http://localhost:8000/empresas
   - http://localhost:8000/estudiantes

### Test Features
- Try the search bars
- Click on filter options
- Toggle between Grid/List view (companies & students)
- Use pagination controls
- Click action buttons (Postularse, Ver detalles, Ver perfil)

---

## 🔄 Integration with Real Data

To connect to real database:

1. **Update listings.js** - Replace mock data with API calls
2. **Create API endpoints** - Implement filtering logic in FastAPI
3. **Add authentication** - Protect sensitive endpoints
4. **Implement actions** - Connect buttons to backend services

### Example: Fetch Real Jobs
```javascript
async function fetchJobs() {
    try {
        const response = await fetch('/api/v1/jobs');
        const jobs = await response.json();
        return jobs;
    } catch (error) {
        console.error('Error fetching jobs:', error);
        return [];
    }
}
```

---

## 🎨 Styling Consistency

All pages use the same color scheme:
- **Primary**: #730f33 (Deep Burgundy)
- **Secondary**: #235b4e (Teal Green)
- **Accent**: #bc935b (Warm Gold)

### CSS Files
- `listings.css` - Shared styles for filter sidebar, cards, pagination
- `styles.css` - Base styles and utility classes

---

## 📱 Responsive Breakpoints

- **Desktop**: Full layout with sidebar (1024px+)
- **Tablet**: Single column with collapsed sidebar (768px - 1023px)
- **Mobile**: Stacked layout, touch-optimized (< 768px)

---

## 🚦 Next Steps

1. ✅ Sub-sites created and routed
2. ✅ Mock data and filtering working
3. ⏳ Connect to real API endpoints
4. ⏳ Add user authentication checks
5. ⏳ Implement profile detail pages
6. ⏳ Add matching algorithm visualization
7. ⏳ Email notifications on new matches
8. ⏳ Deploy to production

---

## 📞 Support

For issues or questions:
- Check `listings.js` for available filters
- Review mock data structure for API format
- Check FastAPI routes in `app/main.py`
- Test in browser DevTools console

---

**Created**: November 12, 2025
**Framework**: FastAPI + Vanilla JavaScript
**Status**: Production Ready (with mock data)
