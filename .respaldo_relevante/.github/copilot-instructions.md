#   Casos de Uso (Use Cases) del MVP

-   Registro y Perfilado Inteligente del Estudiante
    -   El Estudiante centraliza su perfil académico y proyectos (RF 1.0). La API ingesta el currículum o perfil, y los modelos de NLP (Integración de modelos NLP, Tarea S3) analizan e infieren sus habilidades blandas y técnicas (RF 2.0), almacenando el perfil estructurado.

-   Búsqueda y Matchmaking Automatizado
    -   El Reclutador de la empresa sube o introduce los requisitos de una vacante (o aplica filtros avanzados, RF 4.0). La API ejecuta el Algoritmo de Matchmaking (Modelo de clasificación, Tarea S4) para identificar y rankear a los estudiantes cuyos perfiles (incluyendo habilidades blandas inferidas) son más compatibles con la vacante (RF 3.0).

-   Gestión Segura de la Información
    -   El Administrador gestiona el acceso y los permisos de nuevos usuarios (Empresas o Tutores) (RF 8.0). La API aplica protocolos de autenticación (OAuth 2.0) y asegura que toda la información sensible del alumnado (historiales académicos, perfiles) esté protegida mediante cifrado en tránsito (TLS 1.3) (RNF 3.0).

#   Historias de Usuario Esenciales del MVP

-   Empresa Colaboradora
    -   COMO un líder de equipo, QUIERO que la API utilice modelos de procesamiento de lenguaje natural (NLP) para analizar currículums e inferir competencias blandas, PARA encontrar candidatos con potencial de colaboración y adaptabilidad.
    -   COMO un reclutador, QUIERO filtrar perfiles por habilidades técnicas específicas y proyectos prototípicos completados, PARA identificar rápidamente a los candidatos más alineados.

-   Estudiante UNRC
    -   COMO un estudiante, QUIERO centralizar mi perfil académico, proyectos prototípicos y habilidades blandas en un solo repositorio, PARA presentar una candidatura completa y dinámica.
    -   COMO un estudiante, QUIERO recibir notificaciones de coincidencias entre mi perfil y las oportunidades laborales, PARA agilizar mi proceso de inserción laboral.

-   Administrador UNRC
    -   COMO el administrador, QUIERO gestionar roles y permisos de acceso para empresas y estudiantes, PARA asegurar el cumplimiento de las políticas de seguridad y la protección de los datos.
    -   COMO el administrador, quiero visualizar métricas de KPI's sobre el porcentaje de coincidencias y la tasa de colocación de nuestros egresados, PARA evaluar el impacto de la API en la empleabilidad y alinear nuestros planes curriculares con las demandas del mercado

#   Especificaciones Funcionales para el MVP

-   Gestión de Perfil Centralizado
    -   El sistema deberá exponer un endpoint seguro para la ingesta y actualización de datos estructurados (académicos y extracurriculares) y archivos de currículum del estudiante.

-   Análisis de Currículums (NLP)
    -   La API deberá procesar el texto de los currículums utilizando modelos NLP y redes neuronales para extraer y categorizar habilidades técnicas explícitas e inferir competencias blandas.

-   Algoritmo de Matchmaking
    -   El módulo de clasificación deberá generar un puntaje de compatibilidad (matchmaking) entre un perfil de estudiante y una vacante, basado en las habilidades inferidas y los requisitos empresariales.

-   Filtros Avanzados (API)
    -  La API deberá permitir consultas mediante filtros booleanos y de texto sobre habilidades técnicas, proyectos prototípicos y nivel de experiencia (para alimentar Búsqueda y Matchmaking Automatizado).

-   Notificaciones de Coincidencia
    -   El sistema deberá generar y enviar notificaciones automáticas al estudiante cuando se detecte una coincidencia de alta relevancia (matchmaking).

-   Gestión de Roles y Permisos
    -   El sistema deberá autenticar a los usuarios (Estudiante, Empresa, Administrador) y aplicar control de acceso por roles para proteger la información sensible, implementado mediante protocolos de OAuth 2.0.

#   Especificaciones No Funcionales (RNF) Críticas para el MVP

-   Arquitectura y Tecnología
    -   La API debe construirse sobre FastAPI en Python, utilizando PostgresSQL como base de datos, y librerías clave de IA (sklearn, hugging face) así como de visualización (Streamlit).

-   Rendimiento
    -   Los tiempos de respuesta del algoritmo de matchmaking (RF 3.0) deben ser óptimos, justificando la selección de herramientas de Cómputo de Alto Rendimiento (HPC).

-   Protección de Datos
    -   Implementación obligatoria de cifrado en tránsito (TLS 1.3) para proteger el historial académico y la información sensible del alumnado

-   Cumplimiento Regulatorio (Adherencia)
    -   La arquitectura y los procesos deben adherirse a la LFPDPPP y los estándares ISO/IEC 27001.

#	Secciones CV estilo Harvard

-	Información de Contacto: Nombre completo, número de teléfono, dirección de correo electrónico y, opcionalmente, perfil de LinkedIn.
-	Resumen Profesional (Opcional, pero recomendado): Una breve descripción que resalta las habilidades y experiencia más relevantes para el puesto al que se aplica. Es especialmente útil para candidatos con más experiencia.
-	Formación Académica: Se detalla la historia educativa en orden cronológico inverso, incluyendo el nombre de la institución, título obtenido, fechas y cualquier honor o premio. En el ámbito académico, esta sección suele ser más prominente.
-	Experiencia Laboral: Listado de empleos anteriores en orden cronológico inverso, con fechas, nombre de la empresa, cargo y una descripción de responsabilidades y logros.
-	Habilidades/Competencias: Sección para destacar habilidades específicas relevantes para el puesto (idiomas, herramientas técnicas, software, etc.).
-	Secciones Adicionales (Opcionales): Dependiendo de la experiencia y el campo, se pueden incluir secciones como:
	-	Premios y reconocimientos.
	-	Publicaciones y presentaciones (crucial en CVs académicos).
	-	Proyectos de investigación.
	-	Liderazgo y actividades extracurriculares.
	-	Voluntariado o prácticas.
-	Referencias (Opcional): A menudo se omite, con una línea que indica "Referencias disponibles bajo petición" si es necesario. 


#	Ciberseguridad para la Anonimización de Datos
##	Evaluación y Clasificación de Datos
	-	Realizar inventario exhaustivo de activos de datos en la organización
	-	Clasificar información según sensibilidad: pública, interna, confidencial, crítica
	-	Identificar datos personales, financieros, médicos y comercialmente sensibles
	-	Mapear flujos de datos entre sistemas y procesos de negocio

##	Análisis de Riesgos de Reidentificación
	-	Evaluar cuasi-identificadores y su potencial combinatorio
	-	Realizar pruebas de vinculación con bases de datos públicas
	-	Calcular métricas de riesgo: k-anonimidad, l-diversidad, t-closeness
	-	Documentar vectores de ataque potenciales

##	Diseño de Estrategia de Anonimización
	-	Seleccionar técnicas apropiadas según tipo de dato y caso de uso
	-	Definir niveles de anonimización por rol y contexto de acceso
	-	Establecer políticas de retención y eliminación de datos
	-	Diseñar procesos de validación y prueba

##	Implementación y Automatización
	-	Configurar herramientas de enmascaramiento en entornos de prueba
	-	Integrar procesos de anonimización en pipelines de datos
	-	Establecer monitoreo y auditoría continua
	-	Crear procedimientos de respuesta ante incidentes

##	Validación y Certificación
	-	Ejecutar pruebas de reidentificación por terceros independientes
	-	Verificar cumplimiento con requisitos regulatorios específicos
	-	Validar que los datos mantienen utilidad analítica suficiente
	-	Obtener certificaciones de cumplimiento cuando sea aplicable

##	Mantenimiento y Mejora Continua
	-	Revisar periódicamente efectividad de técnicas aplicadas
	-	Actualizar estrategias según evolución de amenazas
	-	Capacitar continuamente al personal técnico
	-	Antes de querer crear reportes ejecutivos, consultar al usuario
	-	Verifica la documentación innecesaria para su eliminación


#	Buenas prácticas
	-	Actualizar INDEX.md cuando se agregue documentación
	-	Mantener clasificación de acceso (🔒 INTERNO vs 🌍 PÚBLICO)
	-	Antes de crear nuevos documentos, verificar si ya existen
	-	Procura actualizar documentos obsoletos y eliminar redundancias e innecesarios
	-	Crea unicamente documentación de usuario y técnica cuando sea necesario y evita reportes repetidos o más de 1 resumen.
	-	Revisa a detalle todo lo unstaged por si algo te puede ser útil antes de crear nuevos scripts, podrás refactorizarlos
	-	Evita el sobre desarrollo: prioriza MVPs simples y funcionales
	-	Usa checklist para organizar tareas y fases de desarrollo
	-	Antes de archivar o eliminar, verifica si el archivo puede ser útil en el futuro
	-	Realiza pruebas unitarias, de integración y de rendimiento
	-	Por último, cada que termines de implementar algo de la documentación, elimina aquella que ya no sea útil para evitar acumular docs
