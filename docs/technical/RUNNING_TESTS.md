# 🏃 Ejecutar Tests - Guía Completa

## ⚡ Quick Start

```bash
# Activar entorno virtual
source .venv/bin/activate

# Ejecutar todos los tests
./run_nlp_tests.sh all

# O solo tests interactivos
./run_nlp_tests.sh interactive
```

---

## 📋 Opciones CLI

```bash
./run_nlp_tests.sh [OPCIÓN]
```

### Opciones Disponibles

| Opción | Descripción | Tiempo | Reportes |
|--------|-------------|--------|----------|
| `all` | Todos los tests (default) | ~5-10 min | 3 reportes |
| `unit` | Tests unitarios (pytest) | ~30 s | tests/ |
| `interactive` | 48 tests funcionales | ~2 min | nlp_service_test_report.json |
| `benchmark` | 5 benchmarks + stress | ~2 min | nlp_service_benchmark_report.json |
| `lint` | Code quality (flake8, black) | ~15 s | Consola |
| `reports` | Mostrar reportes JSON | ~5 s | Consola |
| `help` | Mostrar ayuda | ~1 s | - |

---

## 📝 Ejemplos de Uso

### Ejemplo 1: Tests Interactivos (Más Usado)

```bash
./run_nlp_tests.sh interactive
```

**Qué hace**:
- Ejecuta 48 tests funcionales
- Valida correctitud de cálculos
- Genera `nlp_service_test_report.json`
- Muestra resultados en consola con emojis

**Output esperado**:
```
================================================================================
TEST 1: NORMALIZACIÓN DE TEXTO (_clean_text)
================================================================================

📝 Minúsculas básicas
   Input:  'Python'
   Output: 'python'

📝 Lenguaje C++
   Input:  'C++'
   Output: 'cpp'

... (12 tests totales para _clean_text)

... (7 tests para _list_to_text)
... (9 tests para _tfidf_cosine)
... (7 tests para _matching_items)
... (7 tests para calculate_match_score)
... (6 tests de seguridad)

================================================================================
REPORTE DE PRUEBAS
================================================================================

Resumen de pruebas ejecutadas:
  ✓ clean_text: 12 casos
  ✓ list_to_text: 7 casos
  ✓ tfidf_cosine: 9 casos
  ✓ matching_items: 7 casos
  ✓ calculate_match_score: 7 casos
  ✓ security_edge_cases: 6 casos

📄 Reporte detallado guardado en: /Users/sparkmachine/MoirAI/nlp_service_test_report.json

✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ 
TODAS LAS PRUEBAS COMPLETADAS
✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨ ✨
```

**Reportes generados**:
- `nlp_service_test_report.json` (16 KB)
  - Resumen: 6 grupos, 48 casos
  - Resultados detallados con inputs/outputs
  - Status de cada test

---

### Ejemplo 2: Benchmarks (Validar Performance)

```bash
./run_nlp_tests.sh benchmark
```

**Qué hace**:
- Ejecuta 5 benchmarks de rendimiento
- Stress test con 1000 llamadas
- Genera `nlp_service_benchmark_report.json`
- Valida cumplimiento de RFC 3.0 y RNF

**Output esperado**:
```
🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 �� 🔥 🔥 🔥 
INICIANDO BENCHMARKING DEL NLPService
🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 🔥 �� 🔥 🔥 🔥 🔥 🔥 🔥 

================================================================================
BENCHMARK: _clean_text (1000 iteraciones)
================================================================================

📝 'Python'
   Promedio:  0.0009 ms
   Min/Max:   0.0007 / 0.0234 ms
   Mediana:   0.0008 ms

📝 'C++ Developer con experiencia en Node.js y C#'
   Promedio:  0.0022 ms
   Min/Max:   0.0018 / 0.0456 ms
   Mediana:   0.0021 ms

================================================================================
BENCHMARK: _tfidf_cosine (100 iteraciones)
================================================================================

🔍 'Python... vs Python...'
   Promedio:  0.3900 ms
   Min/Max:   0.2100 / 0.8000 ms

================================================================================
BENCHMARK: _matching_items (500 iteraciones)
================================================================================

✓ Pequeña lista (3 items)
   Promedio:      0.0077 ms
   Num items:     3
   Text length:   68

✓ Lista mediana (7 items)
   Promedio:      0.0155 ms
   Num items:     7
   Text length:   115

✓ Lista grande (50 items)
   Promedio:      0.0870 ms
   Num items:     50
   Text length:   142

================================================================================
BENCHMARK: calculate_match_score (50 iteraciones)
================================================================================

🎯 Caso simple (2 skills, 1 project)
   Promedio:       0.8200 ms
   Min/Max:        0.7500 / 1.1000 ms
   Num skills:     2
   Num projects:   1

🎯 Caso intermedio (5 skills, 3 projects)
   Promedio:       1.0030 ms
   Min/Max:        0.9200 / 1.3400 ms
   Num skills:     5
   Num projects:   3

🎯 Caso complejo (15 skills, 10 projects)
   Promedio:       1.2300 ms
   Min/Max:        1.1500 / 1.4500 ms
   Num skills:     15
   Num projects:   10

================================================================================
STRESS TEST: 1000 llamadas secuenciales
================================================================================

✓ 1000 llamadas completadas
  Tiempo total:     0.8100 s
  Tiempo promedio:  0.8100 ms por llamada
  Llamadas/segundo: 1232

================================================================================
REPORTE DE BENCHMARKING
================================================================================

📄 Reporte detallado guardado en: /Users/sparkmachine/MoirAI/nlp_service_benchmark_report.json

📊 RESUMEN DE BENCHMARKS:

clean_text:
  Tiempo promedio: 0.0014 ms

tfidf_cosine:
  Tiempo promedio: 0.3900 ms

calculate_match_score:
  Tiempo promedio: 1.0230 ms

stress_test:
  Tiempo total: 0.8100 s
  Llamadas/segundo: 1232

⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ 
BENCHMARKING COMPLETADO
⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡ ⚡
```

**Reportes generados**:
- `nlp_service_benchmark_report.json` (4.6 KB)
  - 5 benchmarks con métricas (avg, min, max, median, stdev)
  - Stress test results (1232 calls/s)
  - Validación de RFC 3.0 y RNF

---

### Ejemplo 3: Todos los Tests

```bash
./run_nlp_tests.sh all
```

**Qué hace** (en orden):
1. Tests unitarios (pytest) — ~30s
2. Tests interactivos (48 casos) — ~2 min
3. Benchmarks (5 + stress) — ~2 min
4. Linting (flake8, black) — ~15s
5. Muestra reportes — ~5s

**Tiempo total**: ~5-10 minutos

---

### Ejemplo 4: Solo Linting

```bash
./run_nlp_tests.sh lint
```

**Qué valida**:
- `flake8`: Estilo PEP8, imports, etc.
- `black --check`: Formato de código

**Output esperado**:
```
================================================================================
LINTING
================================================================================

🔍 Ejecutando flake8 en app/services/nlp_service.py...
All right.

🔍 Ejecutando black en app/services/nlp_service.py...
would reformat some code
error: cannot format: INTERNAL ERROR: ...
```

Si no hay errores, procede al siguiente paso.

---

### Ejemplo 5: Ver Reportes Generados

```bash
./run_nlp_tests.sh reports
```

**Qué muestra**:
1. Resumen de `nlp_service_test_report.json`
2. Resumen de `nlp_service_benchmark_report.json`

**Output**:
```
================================================================================
REPORTES DISPONIBLES
================================================================================

📄 Test Report: /Users/sparkmachine/MoirAI/nlp_service_test_report.json (16 KB)
📄 Benchmark Report: /Users/sparkmachine/MoirAI/nlp_service_benchmark_report.json (4.6 KB)

================================================================================
TEST REPORT SUMMARY
================================================================================

Total test groups: 6
- clean_text: 12 casos
- list_to_text: 7 casos
- tfidf_cosine: 9 casos
- matching_items: 7 casos
- calculate_match_score: 7 casos
- security_edge_cases: 6 casos

Total: 48 casos ✅

================================================================================
BENCHMARK REPORT SUMMARY
================================================================================

5 Benchmarks + Stress Test Completed

Key Metrics:
- _clean_text: 0.0014 ms avg (1000 iters)
- _tfidf_cosine: 0.39 ms avg (100 iters)
- _matching_items: 0.0077-0.087 ms (500 iters)
- calculate_match_score: 0.82-1.23 ms (50 iters)
- Stress Test: 1232 calls/s (1000 calls)

Compliance:
✅ RFC 3.0 (<50ms): PASS (1.23ms actual)
✅ RNF (>10 calls/s): PASS (1232 calls/s actual)
```

---

## 🔧 Configuración Avanzada

### Ejecutar desde directorio diferente

```bash
# Desde cualquier lado
cd /ruta/a/MoirAI
./run_nlp_tests.sh interactive
```

### Capturar output en archivo

```bash
./run_nlp_tests.sh interactive > test_output.log 2>&1
```

### Ejecutar test específico (necesita pytest)

```bash
# Ejemplo: solo test de _clean_text
pytest tests/test_nlp_service.py::test_clean_text -v
```

### Revisar archivos de salida

```bash
# Ver reporte de tests
cat nlp_service_test_report.json | jq .

# Ver reporte de benchmarks
cat nlp_service_benchmark_report.json | jq .

# Ver últimas líneas del reporte
tail -50 nlp_service_test_report.json
```

---

## 🐛 Troubleshooting

### Error: "Permission denied"

```bash
# Hacer ejecutable
chmod +x run_nlp_tests.sh

# Verificar
ls -la run_nlp_tests.sh
```

**Esperado**:
```
-rwxr-xr-x  run_nlp_tests.sh
```

---

### Error: "No module named 'app'"

**Causa**: No está en el directorio correcto

```bash
# Solución: ir a raíz del proyecto
cd /Users/sparkmachine/MoirAI
./run_nlp_tests.sh interactive
```

---

### Error: "python: command not found"

**Causa**: Entorno virtual no activado

```bash
# Activar
source .venv/bin/activate

# Verificar
python --version  # Debe mostrar Python 3.11.x

# Ejecutar tests
./run_nlp_tests.sh interactive
```

---

### Tests muy lentos

**Causa**: Posibles procesos en background

```bash
# Opción 1: Cerrar aplicaciones
# Opción 2: Ejecutar solo benchmarks (más rápido)
./run_nlp_tests.sh benchmark

# Opción 3: Revisar recursos
top  # Ver procesos
```

---

### Resultados inconsistentes en benchmarks

**Causa**: Variabilidad de sistema

```bash
# Ejecutar múltiples veces y promediar
for i in {1..3}; do 
  ./run_nlp_tests.sh benchmark | grep "Llamadas/segundo"
done
```

---

## 📊 Interpretación de Resultados

### Tests Interactivos

✅ **PASS**: Todos los 48 casos pasaron
```json
{
  "description": "Caso simple",
  "score": 0.8234,
  "status": "✅ OK"
}
```

❌ **FAIL**: Algún caso falló
```json
{
  "description": "Caso problemático",
  "error": "Descripción del error",
  "status": "❌ ERROR"
}
```

### Benchmarks

✅ **CUMPLE RFC 3.0**: `avg_per_call_ms < 50`
```
RFC 3.0 (<50ms): PASS (1.23ms actual)
```

✅ **CUMPLE RNF**: `calls_per_second > 10`
```
RNF (>10 calls/s): PASS (1232 calls/s actual)
```

---

## 🎯 Casos de Uso Comunes

### Antes de hacer commit

```bash
./run_nlp_tests.sh all
```

Asegurar que todo pasa antes de comprometer cambios.

---

### Validar cambios rápido

```bash
./run_nlp_tests.sh interactive
```

Solo tests funcionales (2 min vs 5-10 min)

---

### Validar rendimiento

```bash
./run_nlp_tests.sh benchmark
```

Asegurar que no hay degradación.

---

### Validar estilo de código

```bash
./run_nlp_tests.sh lint
```

Antes de commit para evitar CI/CD failures.

---

### Monitoreo continuo

```bash
# Cron job cada hora
0 * * * * cd /Users/sparkmachine/MoirAI && ./run_nlp_tests.sh benchmark >> benchmark.log 2>&1
```

---

## 🔗 Referencias

- [TESTING_NLP_SERVICE.md](./TESTING_NLP_SERVICE.md) - Detalles de tests
- [CALCULATE_MATCH_SCORE_USAGE_GUIDE.md](./CALCULATE_MATCH_SCORE_USAGE_GUIDE.md) - API
- [test_nlp_service_interactive.py](../test_nlp_service_interactive.py) - Código
- [test_nlp_service_benchmark.py](../test_nlp_service_benchmark.py) - Código
- [run_nlp_tests.sh](../run_nlp_tests.sh) - Script

---

**Última actualización**: 3 de noviembre 2025
**Versión**: 1.0 (MVP Release)
