# Guía de Uso - Analytics Dashboard

## 📊 Análisis de Visitas y Páginas Vistas

### Ubicación
Admin Dashboard → Sección "Análisis de Visitas y Páginas Vistas" (después de los KPI cards principales)

---

## 🔢 Tarjetas de Métricas (KPI Cards)

### 6 Métricas Disponibles:

| Métrica | Valor | Descripción |
|---------|-------|------------|
| **Visitas Totales** | 248,567 | Total histórico de visitas (promedio 8,285/día) |
| **Visitas del Mes** | 45,230 | Visitas en el mes actual (promedio 1,508/día) |
| **Visitas de la Semana** | 10,847 | Visitas en la semana actual (promedio 1,550/día) |
| **Visitas de Hoy** | 1,642 | Visitas en el día actual (428 en últimas 2h) |
| **Páginas Vistas** | 542,891 | Total de páginas vistas (2.18 promedio/visita) |
| **Usuarios Únicos** | 89,423 | Usuarios únicos (2,341 nuevos esta semana) |

**Características:**
- ✅ Iconos descriptivos para cada métrica
- ✅ Indicadores de tendencia (% de cambio)
- ✅ Estadísticas contextuales
- ✅ Hover effects con animaciones

---

## 📈 Histograma de Visitas por Hora

### Controles:

```
┌─────────────────────────────────────────────┐
│ Histograma de Visitas por Hora    [Dropdown]│
│                                             │
│   ┌─ Hoy (seleccionar)                    │
│   ├─ Esta Semana (default)                │
│   └─ Este Mes                             │
└─────────────────────────────────────────────┘
```

### Tres Vistas Disponibles:

#### 1️⃣ **Hoy** (24 datos horarios)
- Datos: Cada hora del día (0:00 - 23:00)
- Rango: 28 - 182 visitas/hora
- Uso: Ver patrones de actividad diaria

#### 2️⃣ **Esta Semana** (7 datos diarios)
- Datos: Lunes a Domingo
- Rango: 1,147 - 2,150 visitas/día
- Uso: Analizar tendencias semanales

#### 3️⃣ **Este Mes** (30 datos diarios)
- Datos: Primer al último día del mes
- Rango: 950 - 2,280 visitas/día
- Uso: Evaluar el desempeño mensual

### Características del Gráfico:

- **Tipo**: Gráfico de barras (Bar Chart)
- **Colores Dinámicos**:
  - Rojo oscuro (#730f33) = Alta actividad
  - Rojo claro = Actividad media
  - Dorado (#bc935b) = Baja actividad
- **Interactividad**:
  - Hover: Muestra tooltip con número exacto
  - Cambio de timeframe: Actualización automática
  - Responsivo: Se adapta a cualquier pantalla

---

## 🔝 Páginas Más Visitadas

### Ranking Top 5:

```
RANK | PÁGINA                  | VISTAS   | % TRÁFICO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 1   | Página de Inicio (/)    | 45,230   | 18.2%  ███████████████████
 2   | Oportunidades           | 38,145   | 15.3%  █████████████████
 3   | Empresas                | 32,456   | 13.1%  ███████████████
 4   | Estudiantes             | 28,934   | 11.6%  █████████████
 5   | Dashboard               | 21,567   | 8.7%   ██████████
```

### Información por Página:

Cada página muestra:
- 🏆 **Número de Rank** (con color código)
- 📄 **Nombre de la Página** + Ruta (/ruta)
- 👁️ **Número Total de Vistas**
- 📊 **Porcentaje del Tráfico Total**
- 📈 **Barra de Progreso Visual** (comparativa)

### Características Interactivas:

- ✨ Hover effect: Cambio de fondo
- 🎨 Gradiente en barras (proporcional al valor)
- 📱 Responsive: Se adapta a móviles
- ⚙️ Fácilmente actualizable con datos reales

---

## 💡 Casos de Uso

### 📌 Caso 1: Monitoreo de Actividad Diaria
1. Seleccionar **"Hoy"** en el dropdown
2. Observar patrones horarios (picos/valles)
3. Identificar horas pico de actividad

### 📌 Caso 2: Análisis de Tendencias Semanales
1. Seleccionar **"Esta Semana"**
2. Comparar visitas por día
3. Detectar días de mayor/menor actividad

### 📌 Caso 3: Evaluación de Desempeño Mensual
1. Seleccionar **"Este Mes"**
2. Ver evolución del mes completo
3. Calcular crecimiento o declive

### 📌 Caso 4: Optimización de Páginas
1. Revisar **"Páginas Más Visitadas"**
2. Identificar páginas con bajo tráfico
3. Priorizar mejoras en landing page (#1)

---

## ⚙️ Integración con Backend (Próximos Pasos)

### Endpoint Recomendado:

```bash
GET /api/analytics/visits?timeframe=week&start_date=2024-01-01&end_date=2024-01-31
```

### Respuesta JSON Esperada:

```json
{
  "timeframe": "week",
  "data": [
    {"label": "Lun", "visits": 1450},
    {"label": "Mar", "visits": 1680},
    {"label": "Mié", "visits": 1820},
    {"label": "Jue", "visits": 1950},
    {"label": "Vie", "visits": 2150},
    {"label": "Sab", "visits": 1620},
    {"label": "Dom", "visits": 1147}
  ],
  "total_visits": 10847,
  "average_daily": 1550
}
```

### Actualizar `charts.js`:

```javascript
// Reemplazar getChartData() con llamada a API
async getChartData(timeframe) {
    const response = await fetch(`/api/analytics/visits?timeframe=${timeframe}`);
    const data = await response.json();
    return {
        labels: data.data.map(d => d.label),
        datasets: [{...}]
    };
}
```

---

## 🎨 Personalización

### Cambiar Colores:

En `charts.js`:

```javascript
// Modificar getBarColors() para cambiar gradientes
backgroundColor: 'rgba(115, 15, 51, 0.9)' // Cambiar color RGB
```

### Cambiar Número de Datos:

En `getChartData()` método:

```javascript
// Para 15 días en lugar de 30
labels = Array.from({length: 15}, (_, i) => (i + 1) + ' de mes');
```

### Agregar Nuevas Métricas:

1. Crear nueva tarjeta KPI en `dashboard.html`
2. Copiar estructura existente
3. Actualizar estilos en `admin-styles.css`

---

## 🐛 Troubleshooting

### ❌ Gráfico no aparece

**Solución:**
- Verificar que Chart.js CDN esté cargado
- Abrir DevTools (F12) → Console
- Verificar que `typeof Chart !== 'undefined'`

### ❌ Dropdown de timeframe no funciona

**Solución:**
- Verificar que elemento `#visitsTimeframe` existe en HTML
- Verificar JavaScript console por errores
- Recargar página

### ❌ Datos de gráfico incorrectos

**Solución:**
- Editar datos en `charts.js`
- Método: `getChartData(timeframe)`
- Recargar página (Ctrl+F5)

---

## 📱 Responsive Behavior

### Desktop (1920px+)
- ✅ Todos los elementos a pantalla completa
- ✅ Gráfico con máximo ancho

### Tablet (768px - 1024px)
- ✅ Grid de 1 columna
- ✅ Dropdown en ancho completo
- ✅ Páginas más visitadas optimizadas

### Mobile (< 768px)
- ✅ Stack vertical de tarjetas
- ✅ Barra de progreso 100% ancho
- ✅ Rank badges más pequeños
- ✅ Gráfico responsivo

---

## 📋 Checklist de Funcionalidad

- [x] Histograma con timeframe selector
- [x] Tres vistas (hoy/semana/mes)
- [x] Páginas más visitadas ranking
- [x] Código de colores por rendimiento
- [x] Tooltips interactivos
- [x] Responsive design
- [x] Datos de ejemplo
- [x] Integración Chart.js

---

## 🔗 Recursos Relacionados

- **Archivo HTML**: `app/frontend/templates/admin/dashboard.html`
- **Estilos CSS**: `app/frontend/static/css/admin-styles.css`
- **Scripts JS**: `app/frontend/static/js/charts.js`
- **Documentación**: `docs/ANALYTICS_DASHBOARD_SUMMARY.md`

---

**Última actualización**: 12 de noviembre, 2025  
**Versión**: 1.0  
**Estado**: ✅ Completado
