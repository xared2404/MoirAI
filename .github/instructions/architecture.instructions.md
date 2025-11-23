---
applyTo: "**"
---
# MoirAI - Contexto Global y Arquitectura

## 1. Identidad y Objetivo del Proyecto
Estás construyendo **MoirAI**, una plataforma de vinculación laboral universitaria.
- **Misión:** Conectar Estudiantes con Empresas basándose en *competencias inferidas* y potencial a traves de su CV al estilo Harvard, no solo en palabras clave exactas.
- **Valor Diferencial:** El uso de NLP para detectar Soft Skills (liderazgo, adaptabilidad) en CVs que no las mencionan explícitamente.

## 2. Reglas de Negocio (Casos de Uso Críticos)
1.  **Matchmaking Inteligente:**
    - La compatibilidad no es binaria (Sí/No). Es un puntaje (Score 0-100%).
    - Prioriza la *semántica* sobre la *sintaxis* (ej: "Desarrollo Web" ≈ "Programación Frontend").
2.  **Perfilado del Estudiante:**
    - Un estudiante es más que su CV. Sus "Proyectos Prototípicos" tienen tanto peso como su experiencia laboral.
    - **Regla de Estructura:** El perfil final del estudiante, almacenado en la base de datos, DEBE estar estructurado en secciones canónicas que simulen el formato Harvard (ej: "Objetivo", "Educación", "Proyectos Clave", "Habilidades Técnicas", "Habilidades Blandas Inferidas").
    - La API debe mapear los datos ingestados del CV a esta estructura estándar.
3.  **Privacidad y Seguridad (Role-Based):**
    - **Estudiantes:** Solo ven sus propios datos y vacantes sugeridas.
    - **Empresas:** Solo ven candidatos anónimos hasta que hay un "Match" o aplicación explícita.
    - **Admin:** Visión total, pero sin exponer PII (Información Personal Identificable) en logs o reportes simples.

## 3. Integridad del Directorio (Reglas de Archivos)
- **PROHIBIDO escribir en ROOT:** El código vive en `app/`, los tests en `tests/`.
- **Mapa de la Verdad:**
  - `app/services`: Aquí reside la "inteligencia" (NLP, Matcher).
  - `app/api`: Solo transporte de datos (JSON).
  - `app/frontend`: Interfaz de Usuario (Vanilla JS).

## 4. Flujo de Trabajo
- **Refactorizar > Crear:** Antes de crear un script nuevo, verifica si `app/utils` o `app/services` ya tienen una función similar.
- **Simplicidad:** Evita sobreingeniería. Si un `if/else` resuelve el problema de negocio, no implementes una Red Neuronal compleja innecesariamente.

## 5. Filosofía de Desarrollo y Mantenimiento (CRÍTICO)
Para mantener el proyecto ordenado, sigue estrictamente este algoritmo antes de generar código:

1.  **Análisis Primero:**
    - *"Lee primero tu estructura de archivos y código existente."*
    - No asumas nada. Verifica qué servicios ya existen en `app/services` antes de proponer uno nuevo.
2.  **Refactorización > Creación:**
    - *"Evita crear nuevos scripts si puedes integrar en los existentes."*
    - Si una funcionalidad es similar a una existente, extiende la clase/función actual en lugar de crear `nuevo_script_v2.py`.
3.  **Limpieza Continua:**
    - *"Evita mantener código duplicado y deprecado."*
    - Si reescribes una función, borra la versión antigua o márcala claramente para eliminación. No dejes código comentado "por si acaso".
4.  **Documentación en Código:**
    - Prefiere Docstrings claros dentro del código (`.py`) sobre archivos `.md` externos y desconectados.