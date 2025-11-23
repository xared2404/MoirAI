# 🗺️ MoirAI - Roadmap de Desarrollo

**Última actualización:** 21 de noviembre de 2025  
**Estado general:** MVP Funcional ✅ → Fase de Optimización ⏳

---

## 📋 Tabla de Contenidos

1. [Estado Actual](#estado-actual)
2. [Próximas Iteraciones](#próximas-iteraciones)
3. [Áreas de Oportunidad](#áreas-de-oportunidad)
4. [Deuda Técnica](#deuda-técnica)
5. [Timeline Estimado](#timeline-estimado)

---

## 🎯 Estado Actual

### ✅ Completado (MVP)

| Componente | Estado | Detalles |
|-----------|--------|---------|
| **Backend FastAPI** | ✅ Producción | Async, PostgreSQL, JWT auth |
| **Extracción de CV** | ✅ Producción | spaCy NER v2 con soporte bilingual (es/en) |
| **Matchmaking** | ✅ MVP | Scoring basado en competencias |
| **Frontend** | ✅ MVP | React-like vanilla JS con responsive design |
| **Auditoría** | ✅ Implementado | Logging de acciones con actor context |
| **Seguridad** | ✅ Base | JWT, bcrypt, input sanitization |
| **BD** | ✅ Producción | PostgreSQL async con SQLAlchemy 2.0 |
| **NLP** | ✅ Producción | spaCy con caching, bilingual (es+en) |

### ⏳ En Progreso

| Componente | Estimado | Notas |
|-----------|----------|-------|
| **Performance Optimization** | 2 semanas | Indexación DB, caché Redis |
| **Admin Dashboard** | 1 semana | KPIs y analytics |
| **Notificaciones** | 1.5 semanas | Email + in-app |

### 🔄 Por Iniciar

| Componente | Prioridad | Estimado |
|-----------|-----------|----------|
| **Mobile App** | Media | 4-6 semanas |
| **ML Ranking** | Alta | 2-3 semanas |
| **API v2** | Media | 1.5 semanas |

---

## 📈 Próximas Iteraciones

### Iteración 1: Performance & Scaling (Semana 1-2)

**Objetivos:**
- [ ] Implementar Redis para caché de búsquedas
- [ ] Agregar índices DB para queries lentos
- [ ] Profiling de API endpoints
- [ ] CDN para assets estáticos

**Tareas técnicas:**
```
Backend:
  - Caché layer para matching results
  - Connection pooling optimization
  - Query indexing analysis
  - Load testing con 1000 usuarios

Frontend:
  - Minification de JS/CSS
  - Lazy loading de componentes
  - Service Worker para offline
  - Image optimization
```

**KPIs de éxito:**
- API response time < 200ms (p99)
- Frontend load time < 2s (3G)
- DB queries < 100ms (p99)

---

### Iteración 2: Admin Dashboard & Analytics (Semana 3)

**Objetivos:**
- [ ] Dashboard admin con KPIs reales
- [ ] Reportes de matching
- [ ] User management interface
- [ ] System health monitoring

**Tareas técnicas:**
```
Backend:
  - Endpoints de reportes
  - Aggregation queries
  - Export a PDF/Excel

Frontend:
  - Charts with Chart.js
  - Real-time data refresh
  - Role-based views
```

---

### Iteración 3: Notificaciones (Semana 4)

**Objetivos:**
- [ ] Sistema de notificaciones in-app
- [ ] Email notifications
- [ ] SMS (optional)
- [ ] Notification preferences

**Integraciones:**
- SendGrid o Mailgun (email)
- Twilio (SMS opcional)

---

## 🎪 Áreas de Oportunidad

### 1. **Inteligencia Artificial - Ranking Mejorado** 🤖

**Descripción:**  
El actual sistema de matching es determinístico (scoring basado en reglas). Necesitamos ML para:
- Ranking dinámico basado en histórico
- Predicción de tasa de éxito
- Detección de anomalías

**Implementación:**
```python
# app/services/ml_ranking_service.py (NUEVO)
class MLRankingService:
    """Ranking ML-based con histórico de matches exitosos"""
    - train_model() # Re-entrena con histórico
    - predict_compatibility() # Score ML vs regex
    - feedback_loop() # Aprende de user actions
```

**Stack:** scikit-learn, XGBoost, o TensorFlow Lite  
**Timeframe:** 2-3 semanas  
**Impacto:** +30% en matching accuracy

---

### 2. **Integraciones Externas** 🔗

**Universidades:**
- LinkedIn API (importar CV desde LinkedIn)
- APIs de universidades (verificar títulos)

**Empleadores:**
- Indeed, LinkedIn integrations
- Job board aggregation

**Implementación:**
```
app/services/integrations/
├── linkedin_service.py
├── indeed_service.py
├── university_service.py
└── job_board_service.py
```

**Timeframe:** 3-4 semanas  
**Esfuerzo:** Medio-Alto

---

### 3. **Mobile App** 📱

**Plataformas:** iOS + Android  
**Stack:** React Native o Flutter

**Features MVP:**
- Profile viewing
- Job search & apply
- Notifications
- Application tracking

**Timeframe:** 4-6 semanas  
**Equipo:** 2 desarrolladores

---

### 4. **Reporte & Compliance** 📋

**Funcionalidades:**
- Reports de placement rates
- Compliance audits
- GDPR compliance tools
- Data export/anonymization

**Implementación:**
```
app/services/reports/
├── placement_report.py
├── compliance_report.py
└── data_export.py
```

**Timeframe:** 1.5 semanas  
**Criticidad:** Alta

---

### 5. **Search & Filters Avanzados** 🔍

**Actual:** Search simple por keywords  
**Propuesto:** Faceted search con filtros

**Features:**
- Filtros por skill, location, salary
- Saved searches
- Alerts por criteria
- Advanced query DSL

**Implementación:**
- Backend: Elasticsearch o PostgreSQL full-text
- Frontend: Advanced filter UI

**Timeframe:** 2 semanas

---

### 6. **Soft Skills Inference Mejorada** 🧠

**Objetivo:** Detectar soft skills más precisamente

**Mejoras:**
- Entrenamiento con dataset más grande
- Fine-tuning de modelo spaCy
- NLP con transformers (BERT español)

**Stack:** Hugging Face transformers + spaCy

**Timeframe:** 2-3 semanas  
**Impacto:** +25% en precisión

---

## ⚙️ Deuda Técnica

### Crítica 🔴

| Ítem | Descripción | Esfuerzo | Impacto |
|------|-----------|----------|--------|
| Deprecar unsupervised_cv_extractor.py | Mantener legacy si spaCy falla | 4h | Alto |
| Validación input exhaustiva | XSS, SQL injection protection | 2 días | Crítico |
| Rate limiting en API | Prevenir abuso | 1 día | Alto |

### Media 🟡

| Ítem | Descripción | Esfuerzo | Impacto |
|------|-----------|----------|--------|
| Refactor tests | Consolidar 50+ test files | 1 semana | Medio |
| Cleanup documentación | Eliminar archivos obsoletos | 1 día | Bajo |
| CI/CD setup | GitHub Actions | 2 días | Medio |
| Docker compose | Ambiente local easier | 1 día | Medio |

### Baja 🟢

| Ítem | Descripción | Esfuerzo | Impacto |
|------|-----------|----------|--------|
| Code formatting | Black, isort consistency | 4h | Bajo |
| Docstrings | Completar documentación código | 3 días | Bajo |
| Pre-commit hooks | Automated linting | 2h | Bajo |

---

## 🗺️ Timeline Estimado

```
Noviembre 2025:
  ✅ W1: MVP Production-ready (COMPLETADO)
  ⏳ W4: Admin Dashboard + Performance Baseline

Diciembre 2025:
  W1: Performance Optimization Sprint
  W2-W3: Notificaciones
  W4: Holiday freeze

Enero 2026:
  W1-W2: ML Ranking v1
  W3: Mobile app kickoff
  W4: Integraciones externas (fase 1)

Q1 2026 (Ahead):
  - Elasticsearch for advanced search
  - Compliance suite
  - API v2 design
```

---

## 🎯 Métricas de Éxito

### Para Usuario Final

| Métrica | Target | Método |
|---------|--------|--------|
| Placement rate | > 70% | Seguimiento histórico |
| Time to job | < 30 días | Analytics |
| Job quality | > 4/5 ⭐ | User feedback |
| Mobile usage | > 40% | Analytics |

### Para Desarrollo

| Métrica | Target | Método |
|---------|--------|--------|
| Test coverage | > 80% | pytest coverage |
| API uptime | > 99.9% | Monitoring |
| API response time (p99) | < 200ms | APM |
| Deployment frequency | Daily | CI/CD |

---

## 📞 Próximos Pasos Inmediatos

### Semana 1 (Nov 21-27)

1. [ ] Merge de rama feature/frontend-mvp a main
2. [ ] Setup CI/CD básico (GitHub Actions)
3. [ ] Profiling de endpoints más lentos
4. [ ] Reunión con stakeholders sobre prioridades

### Semana 2 (Nov 28 - Dec 4)

1. [ ] Implementar Redis caching
2. [ ] Agregar índices DB
3. [ ] Load testing con k6 o Locust
4. [ ] Documentar architecture decisions

---

## 🔧 Stack Tecnológico Actual

**Backend:**
- Python 3.11, FastAPI 0.104+, PostgreSQL 15
- SQLAlchemy 2.0, asyncpg, Pydantic v2
- spaCy 3.7.0+ (NLP), Redis (cache)

**Frontend:**
- Vanilla JS (HTML5, CSS Grid, ES6+)
- No frameworks (mantenibilidad)

**DevOps:**
- Docker + Docker Compose
- GitHub (git)
- (En progreso: GitHub Actions)

---

## 📚 Documentación Relacionada

- [Guía de Setup](docs/technical/EXECUTION_GUIDE.md)
- [Database Schema](docs/technical/DATABASE_SETUP.md)
- [NLP Services](docs/technical/SPACY_CACHE_GUIDE.md)
- [Architecture Decisions](docs/technical/PERFORMANCE_ANALYSIS.md)

---

**Autor:** AI Assistant  
**Contacto:** henryspark@moirai.dev  
**Licencia:** MIT

