# 🚀 GUÍA DE VERIFICACIÓN Y EJECUCIÓN

## ✅ PRE-EJECUCIÓN: CHECKLIST

### 1. Verificar que el archivo compila
```bash
cd /Users/sparkmachine/MoirAI
python3 -m py_compile test_cv_matching_interactive.py
# Debería completar sin errores
```

### 2. Verificar imports correctos
```bash
grep "from app.services.text_vectorization_service" test_cv_matching_interactive.py
# Debería mostrar:
# from app.services.text_vectorization_service import text_vectorization_service, TextVectorizationService, NormalizationType
```

### 3. Verificar NO hay nlp_service imports
```bash
grep "from app.services.nlp_service" test_cv_matching_interactive.py
# Debería retornar: (sin resultados)
```

### 4. Verificar CV - Harvard.pdf existe
```bash
ls -lh CV\ -\ Harvard.pdf
# Debería mostrar el archivo con tamaño
```

### 5. Verificar servicios existentes
```bash
ls -la app/services/text_vectorization_service.py
ls -la app/utils/file_processing.py
ls -la app/schemas/__init__.py
# Todos deben existir
```

---

## 🏃 EJECUCIÓN

### Opción 1: Ejecución Simple
```bash
cd /Users/sparkmachine/MoirAI
python3 test_cv_matching_interactive.py
```

### Opción 2: Con Output a Archivo
```bash
cd /Users/sparkmachine/MoirAI
python3 test_cv_matching_interactive.py | tee test_output_$(date +%Y%m%d_%H%M%S).log
```

### Opción 3: Con Debugging
```bash
cd /Users/sparkmachine/MoirAI
python3 -u test_cv_matching_interactive.py 2>&1
```

---

## 📊 SALIDA ESPERADA

El test debería mostrar:

```
════════════════════════════════════════════════════════════════════════════════
        🎯 TEST INTERACTIVO: CV MATCHING - FLUJO COMPLETO MVP
════════════════════════════════════════════════════════════════════════════════

▶ PASO 1: CARGA Y ANÁLISIS DEL CV
   📥 Simulando: POST /api/v1/students/upload_resume
   ✅ Tamaño del archivo: XXX,XXX bytes
   ✅ Texto extraído: X,XXX caracteres
   ✅ Análisis completado
   
   📊 EXTRACCIÓN NLP:
      Confianza: 85%
      Habilidades técnicas: XX
      ...

▶ PASO 2: BÚSQUEDA DE VACANTES
   🔍 Simulando: GET /api/v1/job-scraping/search
   ✅ 5 vacantes encontradas

▶ PASO 3: CÁLCULO DE MATCHING
   ⚖️ Calculando scores con TextVectorizationService (TF-IDF robusto)...
   ✅ Matching completado
   
   🏆 TOP 3 MATCHES:
      1. [Job Title]: XX%
      2. [Job Title]: XX%
      3. [Job Title]: XX%

▶ PASO 4: RANKING Y ANÁLISIS DETALLADO
   [Tabla de ranking completo]

▶ PASO 5: RESUMEN EJECUTIVO
   📈 ESTADÍSTICAS:
      Excelentes: X
      Muy buenas: X
      Buenas: X
   ✅ RECOMENDACIÓN FINAL: ...

✨ VALIDACIONES:
   ✅ extract_text_from_upload_async() trabajando (app/utils/file_processing.py)
   ✅ text_vectorization_service.analyze_document() trabajando (ROBUSTO - 659 líneas) ⭐
   ✅ text_vectorization_service.get_similarity() trabajando (TF-IDF avanzado)
   ✅ StudentProfile schema compatible
   ✅ JobItem schema compatible
   ✅ MatchResult schema compatible

🔗 FLUJO REAL PROBADO:
   1. POST /api/v1/students/upload_resume (CV extraction + NLP analysis)
   2. GET /api/v1/job-scraping/search (Job search)
   3. POST /api/v1/matching/recommendations (Matching calculation)
   4. Ranking de candidatos por score

📝 SERVICIOS UTILIZADOS DIRECTAMENTE:
   • extract_text_from_upload_async() from app.utils.file_processing
   • text_vectorization_service.analyze_document() from app.services.text_vectorization_service ⭐
   • text_vectorization_service.get_similarity() from app.services.text_vectorization_service ⭐
   • CVFileValidator from app.utils.file_processing

🎯 ESQUEMAS VALIDADOS:
   ✅ StudentProfile
   ✅ JobItem
   ✅ MatchResult

════════════════════════════════════════════════════════════════════════════════
```

---

## 🔍 TROUBLESHOOTING

### Error: "ModuleNotFoundError: No module named 'app'"
**Solución**: Asegurarse de estar en el directorio raíz del proyecto
```bash
cd /Users/sparkmachine/MoirAI
python3 test_cv_matching_interactive.py
```

### Error: "FileNotFoundError: CV - Harvard.pdf"
**Solución**: Verificar que el archivo existe en la raíz
```bash
ls CV\ -\ Harvard.pdf
# Si no existe, necesita ser copiado al proyecto
```

### Error: "AttributeError: 'module' has no attribute 'analyze_document'"
**Solución**: Verificar que `text_vectorization_service.py` está actualizado
```bash
grep "def analyze_document" app/services/text_vectorization_service.py
# Debería encontrar la función
```

### Error: "ImportError: cannot import name 'TextVectorizationService'"
**Solución**: Verificar imports en el archivo
```bash
head -40 test_cv_matching_interactive.py | grep -A5 "from app.services"
# Debería mostrar las importaciones correctas
```

---

## 📝 LOGS Y DEBUGGING

### Ver solo errores
```bash
python3 test_cv_matching_interactive.py 2>&1 | grep -i error
```

### Ver timeline de ejecución
```bash
python3 -u test_cv_matching_interactive.py 2>&1 | tee execution.log
```

### Verificar servicios disponibles
```bash
python3 << 'EOF'
try:
    from app.services.text_vectorization_service import text_vectorization_service
    print("✅ text_vectorization_service disponible")
except Exception as e:
    print(f"❌ Error: {e}")
EOF
```

---

## 🎯 VALIDACIONES POST-EJECUCIÓN

Si el test completa exitosamente, debería haber:

✅ **Generado archivos**:
   - El test no crea archivos nuevos (es en-memory)

✅ **Salida a stdout**:
   - Todo el output visible en terminal

✅ **Schemas validados**:
   - StudentProfile creado correctamente
   - JobItem schemas compatibles
   - MatchResult schemas compatibles

✅ **Servicios comprobados**:
   - extract_text_from_upload_async() funcionando
   - text_vectorization_service.analyze_document() funcionando
   - text_vectorization_service.get_similarity() funcionando
   - CVFileValidator funcionando

✅ **Matching funcional**:
   - Scores calculados correctamente
   - Top 3 matches identificados
   - Ranking apropiado

---

## 📊 MÉTRICAS ESPERADAS

```
Tiempo total de ejecución:     ~2-5 segundos
Documentos analizados:         1 (CV)
Vacantes evaluadas:            5
Matching score promedio:        ~70%
Errores encontrados:           0 (esperado)
Warnings encontrados:          0-1 (aceptable)
```

---

## ✨ SIGUIENTE PASO

Una vez que el test ejecuta correctamente:

1. ✅ Integrar a CI/CD pipeline
2. ✅ Ejecutar pruebas periódicamente
3. ✅ Monitorear performance
4. ✅ Recopilar métricas de matching
5. ✅ Ajustar weights según resultados reales

---

## 📞 SOPORTE

Si encuentras problemas:

1. Revisar `SERVICE_SELECTION_JUSTIFICATION.md` para entender por qué text_vectorization_service
2. Revisar `ARCHITECTURE_COMPARISON.md` para ver flujo de datos
3. Revisar `MIGRATION_COMPLETION_SUMMARY.md` para cambios exactos
4. Ejecutar checklist de verificación anterior

---

**Creado**: 20 de noviembre de 2025
**Última actualización**: HOY
**Status**: ✅ LISTO PARA EJECUTAR
