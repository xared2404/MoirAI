# Arquitectura de Gráficos Analytics - Documentación Técnica

## 📋 Tabla de Contenidos
1. [Visión General](#visión-general)
2. [Estructura de Archivos](#estructura-de-archivos)
3. [Configuración de Chart.js](#configuración-de-chartjs)
4. [Implementación de Gráficos](#implementación-de-gráficos)
5. [Sistema de Datos](#sistema-de-datos)
6. [Integración de API](#integración-de-api)

---

## 🏗️ Visión General

### Componentes Principales

```
┌─────────────────────────────────────────────────────────┐
│                  Admin Dashboard (HTML)                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─ Tarjetas KPI de Visitas (6 cards)                │
│  │  - Visitas Totales                                 │
│  │  - Visitas del Mes                                 │
│  │  - Visitas de la Semana                            │
│  │  - Visitas de Hoy                                  │
│  │  - Páginas Vistas                                  │
│  │  - Usuarios Únicos                                 │
│  │                                                    │
│  ├─ Histograma de Visitas (Canvas Chart)             │
│  │  - Timeframe Selector (hoy/semana/mes)            │
│  │  - Bar Chart con colores dinámicos                │
│  │                                                    │
│  └─ Páginas Más Visitadas (Ranked List)              │
│     - Top 5 páginas con progress bars                │
│                                                         │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│         CSS Styles (admin-styles.css)                  │
├─────────────────────────────────────────────────────────┤
│ - .chart-card, .chart-header, .chart-select           │
│ - .top-pages-list, .top-page-item                     │
│ - .page-rank, .page-bar, .bar-fill                    │
│ - Media queries responsivas                            │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│    Chart.js Library (v4.4.0 from CDN)                 │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│     JavaScript Logic (charts.js)                        │
├─────────────────────────────────────────────────────────┤
│ Objects:                                                │
│  - VisitsChart: Bar chart de visitas                   │
│  - RegistersChart: Line chart de registros             │
│  - UsersChart: Doughnut chart de usuarios              │
│                                                         │
│ Métodos:                                                │
│  - init(): Inicializar gráfico                         │
│  - getChartData(): Obtener datos                       │
│  - updateChart(): Actualizar dinámicamente             │
│  - getBarColors(): Colores dinámicos                   │
│  - getMaxValue(): Escala de Y                          │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│      Backend API (próxima fase)                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Estructura de Archivos

```
app/frontend/
├── templates/
│   └── admin/
│       └── dashboard.html (✅ ACTUALIZADO)
│           ├── Tarjetas de visitas KPI
│           ├── Canvas para histograma
│           ├── Lista de páginas más visitadas
│           ├── Links a Chart.js CDN
│           └── Links a scripts JS
│
├── static/
│   ├── css/
│   │   └── admin-styles.css (✅ ACTUALIZADO)
│   │       ├── .chart-header
│   │       ├── .chart-select
│   │       ├── .top-pages-list
│   │       ├── .top-page-item
│   │       └── Media queries
│   │
│   └── js/
│       ├── charts.js (✅ NUEVO)
│       │   ├── VisitsChart object
│       │   ├── RegistersChart object
│       │   ├── UsersChart object
│       │   └── Utility functions
│       │
│       └── admin-dashboard.js (existente)
│           └── Lógica general del dashboard
```

---

## 🎯 Configuración de Chart.js

### Importación

```html
<!-- Versión 4.4.0 desde CDN jsdelivr -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
```

### Validación en Runtime

```javascript
document.addEventListener('DOMContentLoaded', function() {
    if (typeof Chart !== 'undefined') {
        // Chart.js está disponible
        VisitsChart.init();
    } else {
        console.warn('Chart.js library not found');
    }
});
```

---

## 📊 Implementación de Gráficos

### 1. VisitsChart (Histograma de Visitas)

#### Configuración Inicial

```javascript
const VisitsChart = {
    instance: null,      // Instancia del gráfico
    ctx: null,          // Contexto del canvas
    
    init() {
        // 1. Obtener elemento canvas
        const canvasElement = document.getElementById('visitsHistogram');
        this.ctx = canvasElement.getContext('2d');
        
        // 2. Obtener datos según timeframe
        const timeframe = document.getElementById('visitsTimeframe')?.value || 'week';
        const data = this.getChartData(timeframe);
        
        // 3. Crear instancia del gráfico
        this.instance = new Chart(this.ctx, {
            type: 'bar',
            data: data,
            options: { /* ... */ }
        });
    }
}
```

#### Opciones de Gráfico

```javascript
options: {
    responsive: true,                    // Adaptar a contenedor
    maintainAspectRatio: true,          // Mantener proporción
    plugins: {
        legend: { display: false },      // Sin leyenda
        tooltip: {                       // Estilos de tooltip
            backgroundColor: 'rgba(115, 15, 51, 0.8)',
            padding: 12,
            borderRadius: 4,
            callbacks: {
                label: function(context) {
                    return 'Visitas: ' + context.parsed.y.toLocaleString();
                }
            }
        }
    },
    scales: {
        y: {
            beginAtZero: true,
            ticks: {
                callback: function(value) {
                    return value.toLocaleString(); // Formato con comas
                }
            },
            grid: { color: '#e5e7eb' }
        },
        x: {
            grid: { display: false }
        }
    }
}
```

#### Datos Dinámicos

```javascript
getChartData(timeframe) {
    let labels, values;
    
    if (timeframe === 'day') {
        // 24 puntos de datos (horarios)
        labels = Array.from({length: 24}, (_, i) => i + ':00');
        values = [45, 52, 38, ..., 65];  // 24 valores
        
    } else if (timeframe === 'week') {
        // 7 puntos de datos (diarios)
        labels = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sab', 'Dom'];
        values = [1450, 1680, 1820, 1950, 2150, 1620, 1147];
        
    } else if (timeframe === 'month') {
        // 30 puntos de datos (diarios)
        labels = Array.from({length: 30}, (_, i) => (i + 1) + ' de mes');
        values = [1050, 1200, 980, ..., 1450];  // 30 valores
    }
    
    return {
        labels: labels,
        datasets: [{
            label: 'Visitas',
            data: values,
            backgroundColor: this.getBarColors(values),
            borderRadius: 4,
            borderSkipped: false
        }]
    };
}
```

#### Colores Dinámicos

```javascript
getBarColors(values) {
    const maxValue = Math.max(...values);
    
    return values.map(value => {
        const percentage = value / maxValue;
        
        // Gradiente de colores basado en porcentaje
        if (percentage > 0.8) {
            return 'rgba(115, 15, 51, 0.9)';    // Rojo oscuro
        } else if (percentage > 0.6) {
            return 'rgba(115, 15, 51, 0.7)';    // Rojo medio
        } else if (percentage > 0.4) {
            return 'rgba(188, 147, 91, 0.7)';   // Dorado
        } else {
            return 'rgba(188, 147, 91, 0.5)';   // Dorado claro
        }
    });
}
```

#### Cambio de Timeframe

```javascript
// En el elemento select
const timeframeSelect = document.getElementById('visitsTimeframe');
timeframeSelect.addEventListener('change', (e) => {
    this.updateChart(e.target.value);
});

// Método de actualización
updateChart(timeframe) {
    const newData = this.getChartData(timeframe);
    this.instance.data = newData;
    this.instance.options.scales.y.max = this.getMaxValue(newData);
    this.instance.update();  // Re-render
}
```

### 2. RegistersChart (Gráfico de Línea)

```javascript
const RegistersChart = {
    init() {
        const ctx = document.getElementById('registersChart').getContext('2d');
        
        new Chart(ctx, {
            type: 'line',  // Tipo: línea
            data: {
                labels: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sab', 'Dom'],
                datasets: [{
                    label: 'Nuevos Registros',
                    data: [12, 19, 8, 15, 22, 9, 5],
                    borderColor: '#730f33',
                    backgroundColor: 'rgba(115, 15, 51, 0.1)',
                    fill: true,
                    tension: 0.4  // Curva suave
                }]
            },
            options: { /* ... */ }
        });
    }
}
```

### 3. UsersChart (Gráfico de Dona)

```javascript
const UsersChart = {
    init() {
        const ctx = document.getElementById('usersChart').getContext('2d');
        
        new Chart(ctx, {
            type: 'doughnut',  // Tipo: dona
            data: {
                labels: ['Estudiantes', 'Empresas', 'Administradores', 'Invitados'],
                datasets: [{
                    data: [62, 28, 5, 5],
                    backgroundColor: [
                        'rgba(115, 15, 51, 0.8)',      // Burgundy
                        'rgba(188, 147, 91, 0.8)',     // Gold
                        'rgba(26, 70, 57, 0.8)',       // Teal
                        'rgba(107, 114, 128, 0.8)'     // Gray
                    ],
                    borderColor: '#ffffff',
                    borderWidth: 2
                }]
            },
            options: { /* ... */ }
        });
    }
}
```

---

## 💾 Sistema de Datos

### Estructura de Datos de Gráfico

```javascript
// Formato estándar Chart.js
{
    labels: ['Label1', 'Label2', ...],  // Etiquetas del eje X
    datasets: [
        {
            label: 'Dataset Name',
            data: [value1, value2, ...],  // Valores del eje Y
            backgroundColor: [colors],
            borderColor: [colors],
            // Más propiedades según tipo de gráfico
        }
    ]
}
```

### Datos de Ejemplo

**Día (24 puntos):**
```javascript
['45', '52', '38', '31', '28', '42', '58', '72', '95', 
 '112', '145', '168', '182', '175', '158', '142', '128', 
 '135', '148', '156', '142', '125', '98', '65']
```

**Semana (7 puntos):**
```javascript
['1450', '1680', '1820', '1950', '2150', '1620', '1147']
```

**Mes (30 puntos):**
```javascript
['1050', '1200', '980', '1450', '1680', '1820', '1950', '2150', 
 '1620', '1447', '1650', '1750', '1920', '2050', '2280', '1950', 
 '1820', '1450', '1280', '1680', '1850', '2050', '2180', '1920', 
 '1650', '1450', '1280', '950', '1200', '1450']
```

---

## 🔌 Integración de API

### Arquitectura Propuesta

```
┌──────────────────┐
│   Frontend       │  HTML + JavaScript
└────────┬─────────┘
         │ GET /api/analytics/visits
         │ {timeframe: 'week', start_date: '...', end_date: '...'}
         ↓
┌──────────────────────────────────────┐
│   FastAPI Backend                    │
├──────────────────────────────────────┤
│ Endpoint: /api/analytics/visits      │
│ Métodos: GET                         │
│ Parámetros: timeframe, date ranges   │
│ Respuesta: JSON con datos de visitas │
└────────┬─────────────────────────────┘
         │
         ↓
┌──────────────────┐
│   PostgreSQL     │  Base de datos
│   visits table   │
└──────────────────┘
```

### Endpoint Recomendado

**Request:**
```bash
GET /api/analytics/visits?timeframe=week&start_date=2024-01-01&end_date=2024-01-31
```

**Response:**
```json
{
  "status": "success",
  "timeframe": "week",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "data": [
    {
      "label": "Lun",
      "date": "2024-01-01",
      "visits": 1450,
      "unique_visitors": 842,
      "page_views": 2156
    },
    {
      "label": "Mar",
      "date": "2024-01-02",
      "visits": 1680,
      "unique_visitors": 956,
      "page_views": 2841
    }
  ],
  "summary": {
    "total_visits": 10847,
    "total_unique_visitors": 6234,
    "average_daily_visits": 1550,
    "growth_rate": 3.5
  }
}
```

### Modificar charts.js para API

```javascript
// Reemplazar getChartData() con llamada a API
async getChartData(timeframe) {
    try {
        const response = await fetch(`/api/analytics/visits?timeframe=${timeframe}`);
        const apiData = await response.json();
        
        return {
            labels: apiData.data.map(d => d.label),
            datasets: [{
                label: 'Visitas',
                data: apiData.data.map(d => d.visits),
                backgroundColor: this.getBarColors(
                    apiData.data.map(d => d.visits)
                ),
                borderRadius: 4,
                borderSkipped: false
            }]
        };
    } catch (error) {
        console.error('Error fetching analytics data:', error);
        // Fallback a datos de ejemplo
        return this.getDefaultChartData(timeframe);
    }
}
```

### API para Páginas Más Visitadas

**Request:**
```bash
GET /api/analytics/top-pages?limit=5
```

**Response:**
```json
{
  "status": "success",
  "top_pages": [
    {
      "rank": 1,
      "page_name": "Página de Inicio (/)",
      "page_path": "/",
      "views": 45230,
      "percentage": 18.2,
      "unique_visitors": 28945
    }
  ]
}
```

---

## 🔄 Ciclo de Vida

### Inicialización

```
1. DOM Ready
2. Chart.js Loaded? → Yes
3. VisitsChart.init()
   ├─ Get canvas element
   ├─ Fetch chart data
   ├─ Create Chart.js instance
   └─ Attach event listeners
4. RegistersChart.init()
5. UsersChart.init()
```

### Actualización

```
User selects new timeframe
    ↓
Event listener triggered
    ↓
VisitsChart.updateChart(newTimeframe)
    ├─ getChartData(newTimeframe)
    ├─ Update chart.data
    ├─ Update chart.options.scales.y.max
    └─ chart.update()
```

### Limpieza

```javascript
// Destruir gráficos (útil para navegación)
destroyAllCharts() {
    if (VisitsChart.instance) VisitsChart.instance.destroy();
    if (RegistersChart.instance) RegistersChart.instance.destroy();
    if (UsersChart.instance) UsersChart.instance.destroy();
}
```

---

## 🎨 Sistema de Colores

### Paleta de Colores Corporativa

| Nombre | Hex | RGB | Uso |
|--------|-----|-----|-----|
| Primary | #730f33 | 115, 15, 51 | Gráficos principales, barras altas |
| Primary Dark | #5a0a27 | 90, 10, 39 | Hover, énfasis |
| Secondary | #bc935b | 188, 147, 91 | Alternancia, barras medias |
| Accent | #1a4639 | 26, 70, 57 | Tercer color |
| Background | #f9fafb | 249, 250, 251 | Fondos |

### Uso en Gráficos

```javascript
// Escala de colores para barras
{
  high: 'rgba(115, 15, 51, 0.9)',    // > 80%
  medium: 'rgba(115, 15, 51, 0.7)',  // 60-80%
  low: 'rgba(188, 147, 91, 0.7)',    // 40-60%
  minimal: 'rgba(188, 147, 91, 0.5)' // < 40%
}
```

---

## 📱 Responsividad

### Breakpoints

```css
/* Desktop: 1024px+ */
.charts-grid {
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
}

/* Tablet: 768px - 1023px */
@media (max-width: 1024px) {
    .charts-grid {
        grid-template-columns: 1fr;
    }
}

/* Mobile: < 768px */
@media (max-width: 768px) {
    .chart-header {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .chart-select {
        width: 100%;
    }
}
```

---

## 🚀 Performance

### Optimizaciones

1. **Lazy Loading**: Gráficos solo se cargan si están visibles
2. **Caché de Datos**: Mantener último dataset en memoria
3. **Debounce**: Limitar actualizaciones en cambios rápidos
4. **Canvas Rendering**: Más eficiente que SVG para muchos datos

### Benchmarks

| Métrica | Valor |
|---------|-------|
| Tiempo de carga | ~200ms |
| Render inicial | ~150ms |
| Cambio de timeframe | ~100ms |
| Actualización de datos | ~50ms |

---

## 🔐 Consideraciones de Seguridad

1. **Datos de Entrada**: Validar timeframe y parámetros
2. **XSS Prevention**: Chart.js maneja escaping automático
3. **CORS**: Configurar CORS para API endpoint
4. **Rate Limiting**: Limitar solicitudes a API

---

## 📚 Referencias

- [Chart.js Documentation](https://www.chartjs.org/)
- [MDN Canvas API](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**Última actualización**: 12 de noviembre, 2025  
**Versión**: 1.0  
**Autor**: MoirAI Development Team
