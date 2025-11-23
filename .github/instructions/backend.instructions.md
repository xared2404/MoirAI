---
applyTo: "**/*.py"
---
# Estándares de Backend (Python Agent)

## Stack Tecnológico
- Lenguaje: Python 3.11 (Uso estricto de Type Hints).
- Framework: FastAPI (Arquitectura "Thin Router", lógica en Services).
- DB: SQLAlchemy 2.0+, PostgresSQL & Pydantic V2.

## Reglas de Implementación
1. **Ubicación:**
   - Endpoints -> `app/api/`
   - Lógica NLP/Match -> `app/services/`
   - Modelos DB -> `app/models/`
2. **Seguridad:**
   - Nunca uses `print()`, usa `logging`.
   - Nunca loggees PII (Emails, Teléfonos).
   - Sanitiza inputs en los Schemas de Pydantic.
3. **Testing:**
   - Usa `pytest`.
   - Crea los tests en `tests/unit` o `tests/integration`.
   - Usa `conftest.py` para fixtures.

### Estructura de Datos (Inferencia de CV)
1.  **Mapeo de Schemas:** Al definir los modelos Pydantic (`app/schemas/`) para el perfil del estudiante, asegúrate de que los campos coincidan con las **secciones canónicas del formato Harvard** (Educación, Proyectos, Habilidades).
2.  **Lógica NLP:** El servicio NLP (`app/services/nlp_service.py`) debe incluir lógica para identificar y clasificar el texto del CV en estas secciones estándar, incluso si el CV original usa títulos diferentes. Por ejemplo, "Seminarios" debe mapearse a "Educación".
3.  **Tipado Estricto:** Asegura que las secciones de "Habilidades Técnicas" y "Habilidades Blandas Inferidas" se manejen como arreglos o listas fuertemente tipadas para facilitar el Matchmaking considerando su relevancia de cada una de las encontradas y analizadas.

## Comportamiento Específico (NLP)
- Al trabajar con `app/services/nlp_service.py`, prioriza librerías ligeras (scikit-learn) sobre modelos pesados si es posible.
- Evita bloquear el Event Loop principal con cálculos de CPU intensivos.