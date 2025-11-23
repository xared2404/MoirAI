# Guía Visual de Sub-Sitios 🎨

## 🌐 Flujo de Navegación

```
Página de Inicio (/)
    ├── Enlaces de Navbar
    │   ├── [Características] → Página de inicio
    │   ├── [Cómo Funciona] → Página de inicio
    │   ├── [Para Quién] → Página de inicio
    │   ├── [🆕 Oportunidades] → /oportunidades
    │   ├── [🆕 Empresas] → /empresas
    │   ├── [🆕 Estudiantes] → /estudiantes
    │   └── [Contacto] → Página de inicio
    │
    └── Panel de Admin
        └── [Panel Admin] → /admin
```

---

## 📱 Diseños de Página

### Página de Oportunidades (`/oportunidades`)

```
┌─────────────────────────────────────────────┐
│  MoirAI  [Inicio] [Oportunidades*] ...      │
├─────────────────────────────────────────────┤
│       Oportunidades de Empleo               │
│   Encuentra las mejores oportunidades       │
│  ┌─────────────────────────────────────┐   │
│  │ 🔍 Busca por título, empresa...     │   │
│  └─────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│ ┌──────────┐  ┌────────────────────────┐   │
│ │ FILTROS  │  │  12 Empleos (12-24)    │   │
│ │          │  │  Ordenar: Reciente  ▼  │   │
│ │ 📍 Ub.   │  │                        │   │
│ │ ├─ Córdoba│  ├─ [Job Card 1]        │   │
│ │ ├─ CABA  │  │   Desarrollo Python   │   │
│ │ └─ Remote│  │   TechCorp, Remoto    │   │
│ │          │  │   95% Match | Postular│   │
│ │ 🏢 Mod. │  ├─ [Job Card 2]        │   │
│ │ ☐ Presan│  │   Frontend React       │   │
│ │ ☐ Híbrid│  │   WebSol, Híbrido     │   │
│ │ ☐ Remote│  │   88% Match | Postular│   │
│ │          │  └─ ...                  │   │
│ │ 🏭 Sector│  │                        │   │
│ │ ├─ Tecno │  └────────────────────────┘   │
│ │ ├─ Finan │  ┌ Pag: [1] 2 3 ... 5 › ┐    │
│ │ └─ Otros │  └───────────────────────┘    │
│ │          │                                │
│ │ [Limpiar]│                                │
│ └──────────┘                                │
└─────────────────────────────────────────────┘
│ Footer with Links                           │
└─────────────────────────────────────────────┘
```

### Empresas Page (`/empresas`)

```
┌─────────────────────────────────────────────┐
│  MoirAI  [Inicio] ... [Empresas*] ...        │
├─────────────────────────────────────────────┤
│         Empresas Colaboradoras              │
│   Descubre las empresas que buscan talento  │
│  ┌─────────────────────────────────────┐   │
│  │ 🔍 Busca una empresa...             │   │
│  └─────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│ ┌──────────┐  ┌────────────────────────┐   │
│ │ FILTROS  │  │  8 Empresas            │   │
│ │          │  │  [Grid] [List]         │   │
│ │ 🏭 Sector│  │                        │   │
│ │ [Todos]▼ │  ├─ ┌──────┐ [Co 1]      │   │
│ │          │  │  │ TEC  │ TechCorp   │   │
│ │ 👥 Tamaño│  │  └──────┘ Tech, 500+  │   │
│ │ ☐ Startup│  │  12 jobs - Top Empre. │   │
│ │ ☐ PyME  │  ├─ ┌──────┐ [Co 2]      │   │
│ │ ☐ Grande│  │  │ WEB  │ WebSol     │   │
│ │          │  │  └──────┘ Tech, 45+   │   │
│ │ 📍 Ubic. │  │  5 jobs - Verif.      │   │
│ │ [Todos]▼ │  └─ ...                  │   │
│ │          │  │                        │   │
│ │ ✅ Acred.│  └────────────────────────┘   │
│ │ ☐ Verif. │  ┌ [› Siguiente]          ┐  │
│ │ ☐ ISO    │  └──────────────────────────┘ │
│ │          │                                │
│ │ [Limpiar]│                                │
│ └──────────┘                                │
└─────────────────────────────────────────────┘
│ Footer with Links                           │
└─────────────────────────────────────────────┘
```

### Estudiantes Page (`/estudiantes`)

```
┌─────────────────────────────────────────────┐
│  MoirAI  [Inicio] ... [Estudiantes*] ...     │
├─────────────────────────────────────────────┤
│         Directorio de Estudiantes           │
│     Explora el talento de UNRC              │
│  ┌─────────────────────────────────────┐   │
│  │ 🔍 Busca por nombre, skill, carrera │   │
│  └─────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│ ┌──────────┐  ┌────────────────────────┐   │
│ │ FILTROS  │  │  15 Estudiantes        │   │
│ │          │  │  [Grid] [List]         │   │
│ │ 🎓 Carrera│  │                        │   │
│ │ [Todas]▼ │  ├─ ┌────┐ [Est. 1]      │   │
│ │          │  │  │ JG │ Juan García   │   │
│ │ 📚 Año   │  │  └────┘ Ing. Sistemas │   │
│ │ ☐ 1er    │  │  4to año • Python...  │   │
│ │ ☐ 2do    │  │  Ver perfil            │   │
│ │ ☐ 3er    │  ├─ ┌────┐ [Est. 2]      │   │
│ │ ☐ 4to    │  │  │ ML │ María López   │   │
│ │          │  │  └────┘ Administración│   │
│ │ 📅 Avail.│  │  3er año • Gestión... │   │
│ │ ☐ Inmed. │  │  Ver perfil            │   │
│ │ ☐ Semana │  │                        │   │
│ │ ☐ Vacc.  │  └─ ...                  │   │
│ │          │  │                        │   │
│ │ [Limpiar]│  └────────────────────────┘   │
│ └──────────┘  ┌ [‹ Anterior] [1] 2 3 › ┐  │
│               └──────────────────────────┘  │
└─────────────────────────────────────────────┘
│ Footer with Links                           │
└─────────────────────────────────────────────┘
```

---

## 🎨 Color Scheme Applied

### Primary Colors
```
┌─────────────────────────────┐
│ ■ #730f33 (Deep Burgundy)   │  Used for: Titles, Links, Badges
│ ■ #5a0a27 (Darker variant)  │  Used for: Hover states, Depth
└─────────────────────────────┘

┌─────────────────────────────┐
│ ■ #235b4e (Teal Green)      │  Used for: Buttons, Active states
│ ■ #1a4639 (Darker variant)  │  Used for: Button hover
└─────────────────────────────┘

┌─────────────────────────────┐
│ ■ #bc935b (Warm Gold)       │  Used for: Accents, Highlights
│ ■ #a67d4a (Darker variant)  │  Used for: Hover effects
└─────────────────────────────┘
```

### Card Examples

**Job Card** (Oportunidades)
```
┌─────────────────────────────────────┐
│ Desarrollador Python Senior  95% ✓  │
│ 🏢 TechCorp                         │
│ 📍 Córdoba | 💻 Remoto | 2h ago   │
│                                     │
│ Buscamos desarrollador experien...  │
│                                     │
│ [Python] [FastAPI] [PostgreSQL] ... │
│                                     │
│ $150,000-$200,000    [Postularse]  │
└─────────────────────────────────────┘
```

**Company Card** (Empresas)
```
┌─────────────────────────────────────┐
│ [TEC] TechCorp                       │
│      💼 Tecnología                   │
│ 12 vacantes | 500+ empleados        │
│                                     │
│ Empresa líder en soluciones...      │
│                                     │
│ [✓ Verificada] [⭐ Top Empleadora] │
│                                     │
│ 12 oportunidades  [Ver detalles]   │
└─────────────────────────────────────┘
```

**Student Card** (Estudiantes)
```
┌─────────────────────────────────────┐
│ [JG] Juan García                     │
│      📚 Ingeniería en Sistemas       │
│                                     │
│ Apasionado por full-stack e IA...  │
│                                     │
│ [Python] [React] [JavaScript] ...  │
│                                     │
│ Año 4°          [Ver perfil]        │
└─────────────────────────────────────┘
```

---

## 📊 Filter Badge States

### Modality Badges (Jobs)
- **🔴 Presencial** - `background: rgba(115, 15, 51, 0.1); color: #730f33`
- **🟢 Híbrido** - `background: rgba(35, 91, 78, 0.1); color: #235b4e`
- **🟡 Remoto** - `background: rgba(188, 147, 91, 0.1); color: #bc935b`

### Company Badges
- **✓ Verificada** - Green badge with check mark
- **⭐ Top Empleadora** - Gold badge with star
- **📋 Certificada ISO** - Blue badge

### Skill Badges
- Gray background by default
- Changes to Secondary color on hover
- Applied to job, company, and student skills

---

## 🔄 Interactive States

### Buttons
- **Default**: White background, border, secondary text
- **Hover**: Secondary color background, white text, slight scale
- **Active**: Secondary dark color (darker shade)

### Filter Checkboxes
- **Unchecked**: Empty box
- **Checked**: Filled with secondary color checkmark
- **Hover**: Light secondary highlight

### Search Inputs
- **Default**: Transparent with light border
- **Focus**: Border color changes to secondary
- **Has text**: Icon appears on right

### Pagination
- **Current page**: Secondary background, white text
- **Other pages**: White background, gray text
- **Hover**: Light secondary background
- **Disabled**: Grayed out, no cursor

---

## 📱 Mobile Responsive Behavior

### Desktop (1024px+)
```
┌────────────────────────────────┐
│ Sidebar    │    Main Content   │
│ (280px)    │    (100% - 280px) │
└────────────────────────────────┘
```

### Tablet (768px - 1023px)
```
┌────────────────────────────────┐
│ Sidebar (Horizontal Filters)   │
├────────────────────────────────┤
│      Main Content              │
│    (1 column cards)            │
└────────────────────────────────┘
```

### Mobile (<768px)
```
┌────────────────┐
│ [☰] Menu       │
├────────────────┤
│ Filters        │
│ (Stacked)      │
├────────────────┤
│  Cards         │
│  (100% width)  │
├────────────────┤
│  Pagination    │
│  (Wrapped)     │
└────────────────┘
```

---

## 🔍 Search Examples

### Oportunidades
- Search: "Python" → Results: Jobs requiring Python
- Search: "TechCorp" → Results: All TechCorp jobs
- Search: "React" → Results: Frontend React jobs

### Empresas
- Search: "Tech" → Results: All tech companies
- Search: "Startup" → Results: Startup companies
- Search: "Buenos" → Results: Companies in Buenos Aires

### Estudiantes
- Search: "García" → Results: Juan García (by name)
- Search: "Systems" → Results: Systems engineering students
- Search: "Python" → Results: Students with Python skill

---

## 📊 Statistics Displayed

### On Each Page
- **Results Counter**: "X empresas encontradas"
- **Sort Options**: Dropdown for sorting
- **View Toggle**: Grid/List buttons (Companies & Students)
- **Pagination**: Current page info and navigation

### Mock Data Stats
| Page | Records | Filters | Default Visible |
|------|---------|---------|-----------------|
| Oportunidades | 24 jobs | 6 | 6 per page |
| Empresas | 8 companies | 5 | 6 per page |
| Estudiantes | 8 students | 5 | 6 per page |

---

## 🚀 URL Structure

```
/                 → Landing page with hero and features
/oportunidades    → Jobs listing with advanced filters
/empresas         → Companies directory with view toggle
/estudiantes      → Student profiles with view toggle
/admin            → Admin dashboard (separate area)
/landing          → Alias for landing page
/admin/dashboard  → Alias for admin panel
```

---

## 📞 Quick Reference

**To test a page:**
1. Go to `http://localhost:8000/[page-name]`
2. Try searching in the search bar
3. Click filter checkboxes
4. Change dropdown selections
5. Click action buttons
6. Navigate pages
7. Test responsive by resizing browser

**Files to modify for real data:**
- `app/frontend/static/js/listings.js` (lines 1-80 have mock data)
- Replace with API calls to `/api/v1/jobs`, `/api/v1/companies`, `/api/v1/students`

---

**Last Updated**: November 12, 2025
**Status**: ✅ All features working with mock data
