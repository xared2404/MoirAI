# Guía de Uso: calculate_match_score()

## 🎯 Propósito

La función `calculate_match_score()` del servicio NLP calcula un score de compatibilidad (0.0 a 1.0) entre:
- **Perfil del Estudiante** (habilidades + proyectos)
- **Ofertas de Empleo** (descripción + requisitos)

---

## 📚 Tabla de Contenidos

1. [Firma de la Función](#firma)
2. [Parámetros de Entrada](#parámetros)
3. [Ejemplos de Uso](#ejemplos)
4. [Casos de Uso Reales](#casos-reales)
5. [Manejo de Errores](#manejo-errores)
6. [Troubleshooting](#troubleshooting)

---

## Firma de la Función {#firma}

```python
from app.services.nlp_service import nlp_service

score, details = nlp_service.calculate_match_score(
    student_skills: List[str],
    student_projects: List[str],
    job_description: str,
    weights: Dict[str, float] = None
) -> Tuple[float, Dict]
```

---

## Parámetros de Entrada {#parámetros}

### 1. `student_skills: List[str]` (Obligatorio)

Lista de habilidades técnicas del estudiante.

**Tipo**: `List[str]`
**Máx elementos**: Sin límite (cada elemento truncado a 200 chars)
**Valores nulos**: Automáticamente convertidos a `[]`

**Ejemplos válidos**:
```python
# ✅ Correcto
student_skills = ["Python", "JavaScript", "PostgreSQL"]
student_skills = ["Python", "C++", "Node.js", "React", "Docker"]
student_skills = []  # Vacío es permitido

# ❌ Incorrecto (se convertirá automáticamente)
student_skills = None  # → []
student_skills = "Python"  # → Error tipo (use lista)
```

### 2. `student_projects: List[str]` (Obligatorio)

Lista de proyectos completados o descripciones de experiencia del estudiante.

**Tipo**: `List[str]`
**Máx longitud por proyecto**: 2000 caracteres
**Valores nulos**: Automáticamente convertidos a `[]`

**Ejemplos válidos**:
```python
# ✅ Correcto
student_projects = [
    "API REST con FastAPI y PostgreSQL",
    "Dashboard de análisis de datos con React",
    "Sistema de gestión de biblioteca en Python"
]

# ✅ Proyectos con mucho detalle
student_projects = [
    "Desarrollé una API REST con FastAPI que procesa millones de registros. "
    "Implementé optimizaciones de base de datos con PostgreSQL y caching con Redis. "
    "El sistema maneja 10,000 requests por segundo."
]

# ✅ Vacío es permitido
student_projects = []
```

### 3. `job_description: str` (Obligatorio)

Descripción de la oferta de empleo combinada (título + descripción + requisitos).

**Tipo**: `str`
**Máx longitud**: 50,000 caracteres
**Valores nulos**: Automáticamente convertidos a `""`

**Cómo combinarlo desde JobItem**:
```python
# Opción 1: Title + Description (recomendado)
job_description = f"{job_item.title} {job_item.description or ''}"

# Opción 2: Title + Description + Requirements (más informativo)
job_description = f"{job_item.title} {job_item.description} {job_item.requirements or ''}"

# Opción 3: Desde JobPosition
from app.models import JobPosition
job_description = f"{job_position.title} {job_position.description}"
```

**Ejemplos**:
```python
# ✅ Correcto
job_description = "Desarrollador Backend Junior Se busca desarrollador con experiencia en Python..."

# ✅ Vacío es permitido (pero retornará score 0)
job_description = ""

# ✅ Automáticamente truncado a 50,000 chars
job_description = "Descripción muy larga" * 10000  # → truncado
```

### 4. `weights: Dict[str, float]` (Opcional)

Ponderación para dar más importancia a skills o projects.

**Tipo**: `Dict[str, float]`
**Claves válidas**: `"skills"`, `"projects"`
**Valores**: Números positivos (se normalizan automáticamente)
**Default**: `{"skills": 0.35, "projects": 0.65}`

**Ejemplos**:
```python
# ✅ Usar default (65% projects, 35% skills)
score, details = nlp_service.calculate_match_score(
    student_skills,
    student_projects,
    job_description
    # weights no especificado → usa default
)

# ✅ Priorizar habilidades
weights = {"skills": 0.7, "projects": 0.3}
score, details = nlp_service.calculate_match_score(
    student_skills,
    student_projects,
    job_description,
    weights=weights
)

# ✅ Priorizar proyectos
weights = {"skills": 0.2, "projects": 0.8}
score, details = nlp_service.calculate_match_score(
    student_skills,
    student_projects,
    job_description,
    weights=weights
)

# ✅ Valores sin normalizar (se normalizan automáticamente)
weights = {"skills": 1, "projects": 2}  # → {"skills": 0.33, "projects": 0.67}
```

---

## Salida {#salida}

Retorna una tupla:

```python
Tuple[float, Dict]
```

### Score (float)

Número entre 0.0 y 1.0 representando la compatibilidad.

- **1.0**: Match perfecto
- **0.75-0.99**: Excelente match
- **0.5-0.74**: Buen match
- **0.25-0.49**: Match regular
- **0.0-0.24**: Bajo match / No compatible

### Details (Dict)

```python
{
    "skill_similarity": 0.85,              # TF-IDF similarity [0.0, 1.0]
    "project_similarity": 0.78,            # TF-IDF similarity [0.0, 1.0]
    "weights_used": {                      # Pesos normalizados usados
        "skills": 0.35,
        "projects": 0.65
    },
    "matching_skills": [                   # Skills que coinciden
        "Python",
        "PostgreSQL"
    ],
    "matching_projects": [                 # Proyectos que coinciden
        "API REST para e-commerce - FastAPI + PostgreSQL"
    ]
}
```

---

## Ejemplos de Uso {#ejemplos}

### Ejemplo 1: Uso Básico

```python
from app.services.nlp_service import nlp_service

# Datos del estudiante
student_skills = ["Python", "JavaScript", "PostgreSQL"]
student_projects = [
    "Sistema de gestión de biblioteca - Python",
    "Dashboard de análisis - JavaScript y React"
]

# Oferta de empleo
job_description = "Desarrollador Backend Junior Se busca experiencia en Python y bases de datos"

# Calcular matching
score, details = nlp_service.calculate_match_score(
    student_skills,
    student_projects,
    job_description
)

print(f"Score: {score:.3f}")
print(f"Matching skills: {details['matching_skills']}")
print(f"Matching projects: {details['matching_projects']}")

# Output:
# Score: 0.815
# Matching skills: ['Python', 'PostgreSQL']
# Matching projects: ['Sistema de gestión de biblioteca - Python']
```

### Ejemplo 2: Con Pesos Personalizados

```python
# Queremos dar más peso a las habilidades (menos a experiencia)
weights = {"skills": 0.6, "projects": 0.4}

score, details = nlp_service.calculate_match_score(
    student_skills,
    student_projects,
    job_description,
    weights=weights
)

print(f"Score con custom weights: {score:.3f}")
# Output: Score con custom weights: 0.782
```

### Ejemplo 3: Desde Base de Datos

```python
import json
from sqlmodel import Session
from app.models import Student, JobPosition
from app.services.nlp_service import nlp_service
from app.core.database import engine

# Obtener estudiante
with Session(engine) as session:
    student = session.get(Student, 1)
    job = session.get(JobPosition, 1)
    
    # Parse JSON strings
    skills = json.loads(student.skills or "[]")
    projects = json.loads(student.projects or "[]")
    
    # Combinar descripción
    job_description = f"{job.title} {job.description}"
    
    # Calcular
    score, details = nlp_service.calculate_match_score(
        skills,
        projects,
        job_description
    )
    
    print(f"Estudiante {student.name} → Job {job.title}: {score:.3f}")
```

### Ejemplo 4: En Bulk (Múltiples Matches)

```python
import json
from app.services.nlp_service import nlp_service
from app.models import Student
from sqlmodel import Session
from app.core.database import engine

# Calcular matching para un estudiante contra múltiples trabajos
with Session(engine) as session:
    student = session.get(Student, 1)
    student_skills = json.loads(student.skills or "[]")
    student_projects = json.loads(student.projects or "[]")
    
    jobs = [
        {"title": "Backend Dev", "desc": "Python FastAPI..."},
        {"title": "Frontend Dev", "desc": "React JavaScript..."},
        {"title": "DevOps", "desc": "Docker Kubernetes..."}
    ]
    
    results = []
    for job in jobs:
        job_desc = f"{job['title']} {job['desc']}"
        score, details = nlp_service.calculate_match_score(
            student_skills,
            student_projects,
            job_desc
        )
        results.append({
            "job": job['title'],
            "score": score,
            "matched_skills": details['matching_skills']
        })
    
    # Ordenar por score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    for result in results:
        print(f"{result['job']}: {result['score']:.3f} - Skills: {result['matched_skills']}")
```

---

## Casos de Uso Reales {#casos-reales}

### Caso 1: Matching Automático (matching_service.py - YA IMPLEMENTADO)

```python
# En: app/services/matching_service.py
def _calculate_job_match_score(self, student: Student, job: JobItem) -> Tuple[float, Dict]:
    # Parse del estudiante
    student_skills = json.loads(student.skills or "[]")
    student_projects = json.loads(student.projects or "[]")
    
    # Definir pesos dinámicos
    weights = {"skills": 0.35, "projects": 0.65}
    if len(student_projects) >= 3:
        weights["projects"] += 0.10
        weights["skills"] -= 0.10
    
    # Normalizar
    total_w = weights["skills"] + weights["projects"]
    if total_w > 0:
        weights["skills"] /= total_w
        weights["projects"] /= total_w
    
    # Combinar job description
    job_description = f"{job.title} {job.description or ''}"
    
    # Calcular matching
    base_score, match_details = nlp_service.calculate_match_score(
        student_skills,
        student_projects,
        job_description,
        weights=weights
    )
    
    # Aplicar boosts y retornar
    total_boost = 0.0
    if (job.location and "Córdoba" in job.location):
        total_boost += 0.1
    
    final_score = min(base_score + total_boost, 1.0)
    
    return final_score, {
        **match_details,
        "base_score": base_score,
        "boost_applied": total_boost,
        "final_score": final_score
    }
```

### Caso 2: Endpoint de Matching Personalizado

```python
from fastapi import APIRouter, Depends
from app.schemas import MatchingCriteria, MatchResult

router = APIRouter()

@router.post("/api/v1/match/calculate")
async def calculate_match(
    student_id: int,
    job_id: int,
    weights: Dict[str, float] = None
):
    """Endpoint para calcular matching personalizado"""
    
    with Session(engine) as session:
        student = session.get(Student, student_id)
        job = session.get(JobPosition, job_id)
        
        if not student or not job:
            return {"error": "Not found"}
        
        student_skills = json.loads(student.skills or "[]")
        student_projects = json.loads(student.projects or "[]")
        job_description = f"{job.title} {job.description}"
        
        score, details = nlp_service.calculate_match_score(
            student_skills,
            student_projects,
            job_description,
            weights=weights
        )
        
        return {
            "score": round(score, 3),
            "details": details,
            "student_name": student.name,
            "job_title": job.title
        }
```

### Caso 3: Recomendaciones por Similitud

```python
def get_top_N_matches(
    student_id: int,
    all_jobs: List[JobPosition],
    top_n: int = 10
) -> List[Tuple[JobPosition, float]]:
    """Obtener top N matches para un estudiante"""
    
    with Session(engine) as session:
        student = session.get(Student, student_id)
        
        student_skills = json.loads(student.skills or "[]")
        student_projects = json.loads(student.projects or "[]")
        
        matches = []
        for job in all_jobs:
            job_description = f"{job.title} {job.description}"
            
            score, _ = nlp_service.calculate_match_score(
                student_skills,
                student_projects,
                job_description
            )
            
            if score > 0.5:  # Filtro mínimo
                matches.append((job, score))
        
        # Ordenar y retornar top N
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:top_n]
```

---

## Manejo de Errores {#manejo-errores}

### Error Tipo 1: Argumentos con tipo incorrecto

```python
# ❌ Incorrecto
score, details = nlp_service.calculate_match_score(
    student_skills="Python JavaScript",  # ← String, no List[str]
    student_projects=["Proyecto 1"],
    job_description="Backend dev job"
)

# ✅ Correcto
student_skills = ["Python", "JavaScript"]
score, details = nlp_service.calculate_match_score(
    student_skills,
    student_projects=["Proyecto 1"],
    job_description="Backend dev job"
)
```

### Error Tipo 2: JSON Parsing

```python
# ❌ Incorrecto - falla al parsear
import json
student = session.get(Student, 1)
skills = json.loads(student.skills)  # Puede fallar si es None o inválido

# ✅ Correcto - manejar None
skills = json.loads(student.skills or "[]")  # Seguro si es None

# ✅ Correcto - con try/except
try:
    skills = json.loads(student.skills)
except (json.JSONDecodeError, TypeError):
    skills = []
```

### Error Tipo 3: Pesos inválidos

```python
# ❌ Incorrecto
weights = {"skills": "0.5", "projects": "0.5"}  # Strings en lugar de float

# ✅ Correcto - se convierten automáticamente
weights = {"skills": 0.5, "projects": 0.5}

# ✅ Correcto - se manejan errores internamente
weights = {"skills": "invalid"}  # → La función ignora y usa default
```

---

## Troubleshooting {#troubleshooting}

### Problema: Score siempre 0

```python
# Causa probable: job_description vacío o skills/projects vacíos
student_skills = []
student_projects = []
job_description = ""

score, details = nlp_service.calculate_match_score(...)
# → score = 0.0 (esperado, sin datos)

# Solución: Verificar que haya datos
if not student_skills and not student_projects:
    print("Estudiante sin perfil")
```

### Problema: Importación falla

```python
# ❌ Incorrecto
from app.services.nlp_service import calculate_match_score

# ✅ Correcto - importar la instancia singleton
from app.services.nlp_service import nlp_service

score, details = nlp_service.calculate_match_score(...)
```

### Problema: Unicode/Acentos

```python
# La función maneja automáticamente:
student_skills = ["Programación", "Diseño Gráfico", "Inglés"]  # Con acentos
score, details = nlp_service.calculate_match_score(
    student_skills,
    [],
    "Se busca programador con excelente inglés"
)
# → Funciona correctamente, normaliza acentos
```

### Problema: Inputs demasiado largos

```python
# La función trunca automáticamente
huge_skill = "Python" * 1000  # 6000 caracteres
student_skills = [huge_skill]

score, details = nlp_service.calculate_match_score(
    student_skills,
    [],
    "Python job"
)
# → Trunca skill a 200 caracteres automáticamente
# → No hay error, proceso continúa
```

---

## Performance

### Complejidad

- **Time**: O(n*m) donde n=# skills, m=# tokens en job_description
- **Space**: O(n+m) para vocabulario TF-IDF
- **Típico**: < 100ms para inputs normales

### Benchmarks

| Caso | Tiempo |
|------|--------|
| 5 skills, 3 projects, 500 char job_desc | ~10-20ms |
| 20 skills, 10 projects, 2000 char job_desc | ~30-50ms |
| Max inputs (limits) | ~100ms |

---

## Resumen Rápido

```python
# Importar
from app.services.nlp_service import nlp_service

# Usar
score, details = nlp_service.calculate_match_score(
    student_skills=["Python", "React"],
    student_projects=["API project"],
    job_description="Backend Python developer wanted",
    weights={"skills": 0.35, "projects": 0.65}  # opcional
)

# Resultado
print(f"Score: {score}")                    # 0.75
print(f"Skills matched: {details['matching_skills']}")  # ['Python']
print(f"Projects matched: {details['matching_projects']}")
```

---

**Última actualización**: 2024-11-02  
**Versión**: 1.0  
**Estado**: ✅ Aprobado para uso en producción

