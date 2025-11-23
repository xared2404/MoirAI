# 📚 Guía de Caché Bilíngue de Modelos spaCy - MoirAI

## Resumen Ejecutivo

MoirAI ahora soporta **extracción de CVs bilingüe** (Spanish 🇪🇸 + English 🇬🇧) con caché inteligente para máxima performance:

- ✅ **Ambos modelos precargados**: `es_core_news_md` + `en_core_web_md`
- ✅ **Detección automática de idioma**: Detecta Spanish/English basado en contenido
- ✅ **Caché optimizado**: Primera carga ~2s, posteriores <100ms
- ✅ **Reducción de carga al servidor**: Modelos en RAM, sin descargas innecesarias
- ✅ **Contexto máximo**: Extrae información en ambos idiomas

## 🚀 Instalación Rápida

### Opción 1: Setup Automatizado (Recomendado)

```bash
cd /Users/sparkmachine/MoirAI
./setup_secure.sh
```

El script:
1. ✅ Crea entorno virtual
2. ✅ Instala dependencias (incluyendo `psutil` para monitoreo)
3. ✅ **Descarga AMBOS modelos spaCy** (Spanish + English)
4. ✅ Genera `.env` con claves seguras
5. ✅ Verifica integridad de modelos

### Opción 2: Instalación Manual

```bash
# 1. Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Descargar AMBOS modelos
python -m spacy download es_core_news_md
python -m spacy download en_core_web_md

# 4. Verificar caché
python verify_spacy_cache.py
```

## 📊 Gestión de Caché

### Verificar Estado de Modelos

```bash
python manage_spacy_models.py verify
```

Salida esperada:
```
✅ Modelo es_core_news_md: Instalado (3.7.0)
  Tamaño: 45.32 MB
  Idioma: es
  
✅ Modelo en_core_web_md: Instalado (3.7.0)
  Tamaño: 42.15 MB
  Idioma: en
```

### Listar Modelos Instalados

```bash
python manage_spacy_models.py list
```

### Precalentar Caché (recomendado antes de producción)

```bash
python manage_spacy_models.py warmup
```

Este comando:
- Carga ambos modelos en RAM
- Procesa textos de prueba para inicializar estructuras internas
- Reduce latencia en las primeras requests reales

### Ver Estadísticas y Requisitos

```bash
python manage_spacy_models.py stats
```

Muestra:
- Modelos instalados
- Uso total de disco (~90MB)
- Requisitos de RAM (2GB mínimo, 4GB recomendado)
- Tiempos de carga esperados

### Ejecutar Todas las Verificaciones

```bash
python manage_spacy_models.py all
```

## 🔍 Verificación de Caché Completa

```bash
python verify_spacy_cache.py
```

Este script ejecuta:
1. **Verificación de Memoria**: Valida que hay suficiente RAM
2. **Carga de Modelos**: Precalienta ambos modelos
3. **Simulación de Requests**: Procesa textos en ambos idiomas
4. **Información de Caché**: Muestra detalles de ubicación y tamaño

Salida esperada:
```
✅ Memoria Total: 16.00 GB
✅ Memoria Disponible: 12.50 GB
✅ Uso Actual: 21.9%

✅ es_core_news_md precargado en 0.850s
✅ en_core_web_md precargado en 0.920s

Tiempos de Carga:
  es_core_news_md: 0.850s
  en_core_web_md: 0.920s
Tiempo total de precarga: 1.770s

✅ Tiempo promedio (Spanish): 12.34ms
✅ Tiempo promedio (English): 11.87ms

✅ Sistema listo para servir requests bilíngues
✅ Modelos cacheados en memoria para máxima performance
✅ Latencia esperada: <100ms para extracción de CVs
```

## 🧪 Prueba de Extracción Bilíngue

### Script de Demostración

```bash
python test_bilingual_extraction.py
```

Prueba:
- CVs en inglés ✅
- CVs en español ✅
- CVs mixtos (ambos idiomas) ✅

### Verificación Rápida

```bash
python verify_bilingual_support.py
```

Valida:
- ✅ Diccionarios de keywords (English + Spanish)
- ✅ Métodos de extracción disponibles
- ✅ Detección automática de idioma
- ✅ Combinación de keywords bilíngues

## 🏗️ Arquitectura de Caché

### Estructura de Modelos

```
spaCy Models Cache
├── es_core_news_md (~45 MB)
│   ├── vocab/
│   ├── vectors/
│   ├── models/
│   └── ... (entrenado para Spanish)
│
└── en_core_web_md (~42 MB)
    ├── vocab/
    ├── vectors/
    ├── models/
    └── ... (entrenado para English)
```

### Flujo de Carga en Servidor

```
Request de Extracción de CV
         ↓
┌────────────────────────────────────────┐
│ SpacyNLPService (Singleton)            │
│ ├─ Carga modelos UNA VEZ (startup)    │
│ ├─ Caché en RAM                        │
│ └─ Reutiliza para todas las requests   │
└────────────────────────────────────────┘
         ↓
┌────────────────────────────────────────┐
│ cv_extractor_v2_spacy                  │
│ ├─ Detecta idioma del CV              │
│ ├─ Selecciona modelo (es o en)        │
│ └─ Extrae campos (Education, etc)     │
└────────────────────────────────────────┘
         ↓
Response: CVProfile completo
```

### Rendimiento Esperado

| Métrica | Valor |
|---------|-------|
| **Startup (carga modelos)** | ~2s |
| **Primera extracción** | ~50-100ms |
| **Extracciones posteriores** | <20ms |
| **Overhead de detección idioma** | ~5ms |
| **Memory per modelo** | ~150-200MB en RAM |
| **Total RAM con caché** | ~400-500MB |

## 🔧 Configuración en `.env`

```bash
# NLP Configuration
SPACY_LANGUAGE=auto          # 'auto' = detección automática
                             # 'es' = usar es_core_news_md
                             # 'en' = usar en_core_web_md

# Para debugging
DEBUG_NLP=False              # Set True para ver logs de NLP
```

## 🚨 Solución de Problemas

### "Modelo no encontrado" error

```bash
# Verificar instalación
python -m spacy download es_core_news_md
python -m spacy download en_core_web_md

# Limpiar y reinstalar
pip uninstall spacy -y
pip install spacy>=3.7.0
python -m spacy download es_core_news_md
python -m spacy download en_core_web_md
```

### Memoria insuficiente

```bash
# Verificar memoria disponible
python verify_spacy_cache.py

# Si <2GB disponible:
# Opción 1: Usar solo un modelo (no recomendado)
# Opción 2: Aumentar RAM del servidor
# Opción 3: Usar versión ligera (tac_core_es/en en lugar de news/web)
```

### Lentitud en extracción

```bash
# Precalentar caché
python manage_spacy_models.py warmup

# Verificar que está usando caché (primera llamada >50ms OK, posteriores <20ms)
python verify_spacy_cache.py
```

### Idioma detectado incorrectamente

Los modelos bilingües usan detección automática basada en palabras clave. Si un CV es mixto:
- Usará el idioma con mayor puntuación
- Puede procesar ambos si hay muchas palabras clave

Solución: Usar parámetro `primary_lang` en `get_nlp_service('es')` o `('en')`

## 📈 Monitoreo en Producción

```bash
# Monitorear uso de memoria
watch -n 1 'python -c "import psutil; print(f\"Memory: {psutil.virtual_memory().percent}%\")"'

# Logs de extracción (requiere DEBUG=True en .env)
tail -f logs/extraction.log

# Estadísticas del servidor
python manage_spacy_models.py stats
```

## 📚 Referencias

### Archivos Involucrados

```
/Users/sparkmachine/MoirAI/
├── setup_secure.sh                    # Setup automático con ambos modelos
├── manage_spacy_models.py             # Gestión de caché
├── verify_spacy_cache.py              # Verificación completa
├── verify_bilingual_support.py        # Verificación de soporte bilíngue
├── test_bilingual_extraction.py       # Pruebas de extracción
├── app/services/
│   ├── spacy_nlp_service.py          # NLP Service (bilingual)
│   └── cv_extractor_v2_spacy.py      # CV Extractor (bilingual)
├── requirements.txt                   # Incluyendo psutil
└── .env                               # Config (generado por setup_secure.sh)
```

### Métodos Bilíngues Disponibles

```python
# Crear servicio NLP
nlp = get_nlp_service(primary_lang='auto')  # Detección automática

# Métodos disponibles
nlp.extract_entities(text)      # Extrae entidades (Spanish + English)
nlp.tokenize(text)              # Tokenización bilíngue
nlp.analyze(text)               # Análisis completo bilíngue
nlp.similarity(text1, text2)    # Similitud entre textos

# CV Extractor
extractor = CVExtractorV2()
profile = extractor.extract(cv_text)  # Detección automática de idioma
```

## 🎯 Próximos Pasos

1. **Ejecutar setup**:
   ```bash
   ./setup_secure.sh
   ```

2. **Verificar caché**:
   ```bash
   python verify_spacy_cache.py
   ```

3. **Probar extracción bilíngue**:
   ```bash
   python test_bilingual_extraction.py
   ```

4. **Iniciar servidor**:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

5. **Precalentar antes de producción**:
   ```bash
   python manage_spacy_models.py warmup
   ```

---

**Última actualización**: 21 de noviembre 2025
**Soporte**: Para problemas, ejecutar `python verify_spacy_cache.py` o `python manage_spacy_models.py all`
