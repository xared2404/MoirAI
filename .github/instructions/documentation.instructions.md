---
applyTo: "**/*.md"
---
# Estándares de Documentación Estratégica (Librarian Agent)

## 1. Tipos de Documentación Aceptados (Restricción)
El propósito principal de este agente es **producir y mantener** la documentación esencial. **Solo se permite la creación/actualización de:**

1.  **Documentación de Usuario:** Guías de uso, tutoriales (enfocados en el "qué" y el "cómo" para el usuario final).
2.  **Documentación Técnica:** Arquitectura, diagramas de flujo, referencias de API (enfocados en el "por qué" y el "dónde" del código).
3.  **Archivos de Índice/Acceso:** `README.md` (root) y `index.md` (en `docs/`).

## 2. Pautas de Ubicación y Creación
-   **Ubicación:** Toda la documentación nueva (usuario/técnica) debe residir exclusivamente dentro de la carpeta `docs/`.
-   **Índices:** Asegúrate de que tanto el `README.md` de la raíz como el `docs/index.md` reflejen el contenido y estructura actual del proyecto.
-   **Prohibido:**
    -   Crear archivos de logs de sesión, reportes temporales o notas sueltas (`.md`) en la raíz o subcarpetas fuera de `docs/`.
    -   Crear cualquier otro tipo de archivo `.md` que no caiga en las 3 categorías anteriores.

## 3. Prioridad de Documentación
-   La **documentación técnica** debe priorizar los **Docstrings** y **Type Hints** en el código fuente. Solo crea un archivo `.md` técnico si se requiere un diagrama de alto nivel o una explicación extensa.
-   Si se realiza un cambio en un endpoint de la API, actualiza el `README.md` y/o la documentación técnica en `docs/` inmediatamente.