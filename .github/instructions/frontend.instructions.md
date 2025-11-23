---
applyTo: "app/frontend/**"
---
# Estándares de Frontend (Vanilla Agent)

## Stack Tecnológico
- **Vanilla JS (ES6+):** `const`, `let`, `async/await`, Modules.
- **HTML5/CSS3:** Semántico y Moderno.
- **PROHIBIDO:** React, Vue, Streamlit, jQuery, Jinja2 templates.

## Reglas de Implementación
1. **Arquitectura:**
   - El Backend NO devuelve HTML, solo JSON.
   - Tú renderizas el UI manipulando el DOM.
2. **Comunicación:**
   - Usa `fetch()` nativo para consumir la API.
   - Maneja errores de red con `try/catch` y muestra feedback visual al usuario.
3. **Estructura:**
   - Mantén separado: Estructura (`.html`), Estilo (`.css`), Lógica (`.js`).
   - No mezcles lógica de negocio compleja en el frontend; si es cálculo, mándalo al backend.