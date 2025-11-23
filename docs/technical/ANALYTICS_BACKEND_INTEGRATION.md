# Integración Backend - Guía de Implementación

## 📋 Visión General

Esta guía proporciona instrucciones paso a paso para conectar el dashboard analytics con datos reales del backend FastAPI y PostgreSQL.

---

## 🏗️ Arquitectura de Backend

### Stack Tecnológico

```
┌─────────────────────────────────┐
│     Frontend (HTML/JS)          │
│   /static/js/charts.js          │
└─────────────┬───────────────────┘
              │
              │ HTTP GET
              │
┌─────────────↓───────────────────┐
│    FastAPI Backend              │
│  app/api/endpoints/analytics.py │
└─────────────┬───────────────────┘
              │
              │ Query SQL
              │
┌─────────────↓───────────────────┐
│   PostgreSQL Database           │
│   - analytics_visits table      │
│   - page_views table            │
│   - user_sessions table         │
└─────────────────────────────────┘
```

---

## 📊 Esquema de Base de Datos

### Tabla: analytics_visits

```sql
CREATE TABLE analytics_visits (
    id SERIAL PRIMARY KEY,
    visit_date TIMESTAMP NOT NULL,
    visits_count INTEGER NOT NULL,
    unique_visitors INTEGER,
    page_views INTEGER,
    session_duration FLOAT,
    bounce_rate FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices para optimización
CREATE INDEX idx_visit_date ON analytics_visits(visit_date);
CREATE INDEX idx_visit_date_range ON analytics_visits(visit_date DESC);
```

### Tabla: page_analytics

```sql
CREATE TABLE page_analytics (
    id SERIAL PRIMARY KEY,
    page_url VARCHAR(255) NOT NULL,
    page_name VARCHAR(255) NOT NULL,
    page_category VARCHAR(100),
    view_count INTEGER NOT NULL,
    unique_views INTEGER,
    average_time_on_page FLOAT,
    bounce_rate FLOAT,
    date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_page_url ON page_analytics(page_url);
CREATE INDEX idx_page_date ON page_analytics(date DESC);
```

### Tabla: user_activity

```sql
CREATE TABLE user_activity (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    event_type VARCHAR(50),  -- 'visit', 'click', 'signup', etc.
    page_url VARCHAR(255),
    timestamp TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_activity_date ON user_activity(timestamp DESC);
CREATE INDEX idx_event_type ON user_activity(event_type);
```

---

## 🔌 Endpoints de API

### 1. Analytics Visits Endpoint

**Ruta**: `/api/v1/analytics/visits`

**Método**: `GET`

**Parámetros**:
```python
{
    "timeframe": str,        # 'day', 'week', 'month'
    "start_date": str,       # YYYY-MM-DD
    "end_date": str,         # YYYY-MM-DD
    "aggregation": str       # 'hourly', 'daily' (default: 'daily')
}
```

**Respuesta Exitosa (200)**:
```json
{
    "status": "success",
    "timeframe": "week",
    "start_date": "2024-11-05",
    "end_date": "2024-11-11",
    "data": [
        {
            "label": "Lun 05",
            "date": "2024-11-05",
            "visits": 1450,
            "unique_visitors": 842,
            "page_views": 2156,
            "bounce_rate": 35.2
        },
        {
            "label": "Mar 06",
            "date": "2024-11-06",
            "visits": 1680,
            "unique_visitors": 956,
            "page_views": 2841,
            "bounce_rate": 32.1
        }
    ],
    "summary": {
        "total_visits": 10847,
        "total_unique_visitors": 6234,
        "total_page_views": 18456,
        "average_daily_visits": 1550,
        "average_bounce_rate": 33.5,
        "growth_rate": 3.5
    }
}
```

### 2. Top Pages Endpoint

**Ruta**: `/api/v1/analytics/top-pages`

**Método**: `GET`

**Parámetros**:
```python
{
    "limit": int,            # Default: 5
    "start_date": str,       # YYYY-MM-DD (optional)
    "end_date": str,         # YYYY-MM-DD (optional)
}
```

**Respuesta Exitosa (200)**:
```json
{
    "status": "success",
    "data": [
        {
            "rank": 1,
            "page_url": "/",
            "page_name": "Página de Inicio",
            "views": 45230,
            "unique_views": 28945,
            "percentage": 18.2,
            "average_time_on_page": 120,
            "bounce_rate": 28.5
        },
        {
            "rank": 2,
            "page_url": "/oportunidades",
            "page_name": "Oportunidades",
            "views": 38145,
            "unique_views": 22156,
            "percentage": 15.3,
            "average_time_on_page": 245,
            "bounce_rate": 31.2
        }
    ],
    "summary": {
        "total_views": 248567,
        "pages_tracked": 47
    }
}
```

### 3. Visit Metrics Endpoint

**Ruta**: `/api/v1/analytics/metrics`

**Método**: `GET`

**Parámetros**:
```python
{
    "metric_type": str       # 'total', 'today', 'week', 'month'
}
```

**Respuesta Exitosa (200)**:
```json
{
    "status": "success",
    "metrics": {
        "total_visits": {
            "value": 248567,
            "avg_daily": 8285,
            "trend": 15.8,
            "trend_direction": "up"
        },
        "monthly_visits": {
            "value": 45230,
            "avg_daily": 1508,
            "trend": 8.2,
            "trend_direction": "up"
        },
        "weekly_visits": {
            "value": 10847,
            "avg_daily": 1550,
            "trend": 3.5,
            "trend_direction": "up"
        },
        "today_visits": {
            "value": 1642,
            "last_2_hours": 428,
            "trend": 12.3,
            "trend_direction": "up"
        },
        "page_views": {
            "value": 542891,
            "avg_per_visit": 2.18,
            "trend": 22.1,
            "trend_direction": "up"
        },
        "unique_users": {
            "value": 89423,
            "new_this_week": 2341,
            "trend": 9.7,
            "trend_direction": "up"
        }
    }
}
```

---

## 🐍 Implementación FastAPI

### Archivo: `app/api/endpoints/analytics.py`

```python
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from sqlalchemy import func
from app.core.database import db_session
from app.models.analytics import AnalyticsVisit, PageAnalytics

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["analytics"],
    responses={404: {"description": "Not found"}},
)

@router.get("/visits")
async def get_visits(
    timeframe: str = Query("week", regex="^(day|week|month)$"),
    start_date: str = Query(None),
    end_date: str = Query(None),
):
    """
    Obtener datos de visitas agregados por timeframe
    """
    try:
        # Validar y parsear fechas
        if not end_date:
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        
        if not start_date:
            if timeframe == "day":
                start_date = end_date - timedelta(hours=24)
            elif timeframe == "week":
                start_date = end_date - timedelta(days=7)
            else:  # month
                start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        
        # Consultar base de datos
        query = db_session.query(
            AnalyticsVisit.visit_date,
            func.sum(AnalyticsVisit.visits_count).label("visits"),
            func.sum(AnalyticsVisit.unique_visitors).label("unique_visitors"),
            func.sum(AnalyticsVisit.page_views).label("page_views")
        ).filter(
            AnalyticsVisit.visit_date >= start_date,
            AnalyticsVisit.visit_date <= end_date
        )
        
        # Agrupar según timeframe
        if timeframe == "day":
            # Agrupar por hora
            query = query.group_by(func.date_trunc('hour', AnalyticsVisit.visit_date))
        else:
            # Agrupar por día
            query = query.group_by(func.date_trunc('day', AnalyticsVisit.visit_date))
        
        results = query.order_by(AnalyticsVisit.visit_date).all()
        
        # Formatear respuesta
        data = []
        for row in results:
            date_obj = row.visit_date
            
            if timeframe == "day":
                label = date_obj.strftime("%H:00")
            else:
                label = date_obj.strftime("%a %d").replace("Mon", "Lun").replace("Tue", "Mar")
            
            data.append({
                "label": label,
                "date": date_obj.isoformat(),
                "visits": row.visits or 0,
                "unique_visitors": row.unique_visitors or 0,
                "page_views": row.page_views or 0
            })
        
        # Calcular resumen
        total_visits = sum(d["visits"] for d in data)
        total_unique = sum(d["unique_visitors"] for d in data)
        days = len(data)
        
        return {
            "status": "success",
            "timeframe": timeframe,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "data": data,
            "summary": {
                "total_visits": total_visits,
                "total_unique_visitors": total_unique,
                "average_daily_visits": total_visits // days if days > 0 else 0,
                "growth_rate": 3.5  # Calcular si tienes datos previos
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-pages")
async def get_top_pages(
    limit: int = Query(5, ge=1, le=20),
    start_date: str = Query(None),
    end_date: str = Query(None)
):
    """
    Obtener páginas más visitadas
    """
    try:
        # Validar fechas (similar a visits endpoint)
        if not end_date:
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        
        # Consultar páginas más visitadas
        query = db_session.query(
            PageAnalytics.page_url,
            PageAnalytics.page_name,
            func.sum(PageAnalytics.view_count).label("views"),
            func.sum(PageAnalytics.unique_views).label("unique_views")
        ).filter(
            PageAnalytics.date >= start_date,
            PageAnalytics.date <= end_date
        ).group_by(
            PageAnalytics.page_url,
            PageAnalytics.page_name
        ).order_by(
            func.sum(PageAnalytics.view_count).desc()
        ).limit(limit)
        
        results = query.all()
        
        # Calcular total de vistas
        total_views = sum(r.views for r in results)
        
        # Formatear respuesta
        data = []
        for rank, row in enumerate(results, 1):
            percentage = (row.views / total_views * 100) if total_views > 0 else 0
            
            data.append({
                "rank": rank,
                "page_url": row.page_url,
                "page_name": row.page_name,
                "views": row.views or 0,
                "unique_views": row.unique_views or 0,
                "percentage": round(percentage, 1)
            })
        
        return {
            "status": "success",
            "data": data,
            "summary": {
                "total_views": total_views,
                "pages_tracked": len(results)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_metrics(metric_type: str = Query("total")):
    """
    Obtener métricas agregadas de visitas
    """
    try:
        now = datetime.now()
        
        metrics = {}
        
        # Total de visitas
        total = db_session.query(func.sum(AnalyticsVisit.visits_count)).scalar() or 0
        metrics["total_visits"] = {
            "value": total,
            "trend": 15.8,
            "trend_direction": "up"
        }
        
        # Visitas del mes
        month_ago = now - timedelta(days=30)
        monthly = db_session.query(
            func.sum(AnalyticsVisit.visits_count)
        ).filter(
            AnalyticsVisit.visit_date >= month_ago
        ).scalar() or 0
        metrics["monthly_visits"] = {
            "value": monthly,
            "trend": 8.2,
            "trend_direction": "up"
        }
        
        # Visitas de la semana
        week_ago = now - timedelta(days=7)
        weekly = db_session.query(
            func.sum(AnalyticsVisit.visits_count)
        ).filter(
            AnalyticsVisit.visit_date >= week_ago
        ).scalar() or 0
        metrics["weekly_visits"] = {
            "value": weekly,
            "trend": 3.5,
            "trend_direction": "up"
        }
        
        # Visitas de hoy
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        daily = db_session.query(
            func.sum(AnalyticsVisit.visits_count)
        ).filter(
            AnalyticsVisit.visit_date >= today
        ).scalar() or 0
        metrics["today_visits"] = {
            "value": daily,
            "trend": 12.3,
            "trend_direction": "up"
        }
        
        return {
            "status": "success",
            "metrics": metrics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Registrar el router en main.py

```python
from app.api.endpoints import analytics

app.include_router(analytics.router)
```

---

## 📝 Modelos SQLAlchemy

### Archivo: `app/models/analytics.py`

```python
from app.core.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from datetime import datetime

class AnalyticsVisit(Base):
    __tablename__ = "analytics_visits"
    
    id = Column(Integer, primary_key=True)
    visit_date = Column(DateTime, nullable=False, index=True)
    visits_count = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    page_views = Column(Integer, default=0)
    session_duration = Column(Float, default=0)
    bounce_rate = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PageAnalytics(Base):
    __tablename__ = "page_analytics"
    
    id = Column(Integer, primary_key=True)
    page_url = Column(String(255), nullable=False, index=True)
    page_name = Column(String(255), nullable=False)
    page_category = Column(String(100))
    view_count = Column(Integer, default=0)
    unique_views = Column(Integer, default=0)
    average_time_on_page = Column(Float, default=0)
    bounce_rate = Column(Float, default=0)
    date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 🔄 Actualizar Frontend (charts.js)

### Método 1: Fetch Real-time

```javascript
const VisitsChart = {
    instance: null,
    ctx: null,
    
    async init() {
        const canvasElement = document.getElementById('visitsHistogram');
        if (!canvasElement) return;
        
        this.ctx = canvasElement.getContext('2d');
        const timeframe = document.getElementById('visitsTimeframe')?.value || 'week';
        
        // Obtener datos del API
        const data = await this.fetchChartData(timeframe);
        
        this.instance = new Chart(this.ctx, {
            type: 'bar',
            data: data,
            options: { /* ... */ }
        });
        
        // Event listener para cambio de timeframe
        const timeframeSelect = document.getElementById('visitsTimeframe');
        if (timeframeSelect) {
            timeframeSelect.addEventListener('change', (e) => {
                this.updateChart(e.target.value);
            });
        }
    },
    
    async fetchChartData(timeframe) {
        try {
            const response = await fetch(`/api/v1/analytics/visits?timeframe=${timeframe}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const apiData = await response.json();
            
            if (apiData.status !== 'success') {
                throw new Error('API returned error status');
            }
            
            return {
                labels: apiData.data.map(d => d.label),
                datasets: [{
                    label: 'Visitas',
                    data: apiData.data.map(d => d.visits),
                    backgroundColor: this.getBarColors(
                        apiData.data.map(d => d.visits)
                    ),
                    borderRadius: 4,
                    borderSkipped: false,
                    hoverBackgroundColor: '#5a0a27'
                }]
            };
        } catch (error) {
            console.error('Error fetching chart data:', error);
            // Fallback a datos de ejemplo
            return this.getFallbackData(timeframe);
        }
    },
    
    async updateChart(timeframe) {
        const newData = await this.fetchChartData(timeframe);
        this.instance.data = newData;
        this.instance.options.scales.y.max = this.getMaxValue(newData);
        this.instance.update();
    },
    
    getBarColors(values) {
        const maxValue = Math.max(...values);
        return values.map(value => {
            const percentage = value / maxValue;
            if (percentage > 0.8) return 'rgba(115, 15, 51, 0.9)';
            else if (percentage > 0.6) return 'rgba(115, 15, 51, 0.7)';
            else if (percentage > 0.4) return 'rgba(188, 147, 91, 0.7)';
            else return 'rgba(188, 147, 91, 0.5)';
        });
    },
    
    getMaxValue(data) {
        const max = Math.max(...data.datasets[0].data);
        return Math.ceil(max * 1.1);
    },
    
    getFallbackData(timeframe) {
        // Datos de ejemplo si API falla
        // ... (datos de ejemplo existentes)
    }
};
```

---

## 🧪 Testing

### Test del Endpoint

```bash
# Prueba con curl
curl -X GET "http://localhost:8000/api/v1/analytics/visits?timeframe=week" \
     -H "Content-Type: application/json"

# Con parámetros personalizados
curl -X GET "http://localhost:8000/api/v1/analytics/visits?timeframe=month&start_date=2024-11-01&end_date=2024-11-30"
```

### Script de Prueba Python

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Probar endpoint de visitas
response = requests.get(f"{BASE_URL}/api/v1/analytics/visits", 
                       params={"timeframe": "week"})
print("Visits Response:")
print(json.dumps(response.json(), indent=2))

# Probar endpoint de páginas
response = requests.get(f"{BASE_URL}/api/v1/analytics/top-pages",
                       params={"limit": 5})
print("\nTop Pages Response:")
print(json.dumps(response.json(), indent=2))

# Probar endpoint de métricas
response = requests.get(f"{BASE_URL}/api/v1/analytics/metrics")
print("\nMetrics Response:")
print(json.dumps(response.json(), indent=2))
```

---

## 📋 Checklist de Implementación

- [ ] Crear tablas en PostgreSQL
- [ ] Crear modelos SQLAlchemy
- [ ] Implementar endpoints en FastAPI
- [ ] Registrar router en main.py
- [ ] Poblador datos de prueba (seed script)
- [ ] Actualizar charts.js con fetch real
- [ ] Probar endpoints con curl/Postman
- [ ] Agregar validación de datos
- [ ] Agregar autenticación si es necesario
- [ ] Agregar rate limiting
- [ ] Documentar en Swagger
- [ ] Pruebas unitarias
- [ ] Pruebas de carga

---

## 🚀 Próximos Pasos

1. **Implementar Endpoints** - Backend
2. **Conectar Frontend** - Actualizar charts.js
3. **Cargar Datos** - Poblar tabla con datos reales
4. **Agregar Autenticación** - Proteger endpoints
5. **Monitoreo** - Configurar logs y alertas

---

**Fecha**: 12 de noviembre, 2025  
**Versión**: 1.0
