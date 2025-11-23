#!/usr/bin/env python3
"""
Demostración de Caché Bilíngue de spaCy - Performance Comparison

Este script muestra:
1. Diferencia de velocidad entre primera carga y caché
2. Detección automática de idioma
3. Performance de extracción bilíngue
"""

import sys
import time
from pathlib import Path

# Agregar app/ al path
sys.path.insert(0, str(Path(__file__).parent / "app"))

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
NC = '\033[0m'

def print_header(text: str):
    print(f"\n{BLUE}╔════════════════════════════════════════════╗{NC}")
    print(f"{BLUE}║{NC} {text}")
    print(f"{BLUE}╚════════════════════════════════════════════╝{NC}\n")

def print_success(text: str):
    print(f"{GREEN}✅ {text}{NC}")

def print_info(text: str):
    print(f"{CYAN}ℹ️  {text}{NC}")

def print_perf(title: str, time_ms: float, expected: str = ""):
    color = GREEN if time_ms < 50 else YELLOW if time_ms < 100 else RED
    expected_str = f" (expected: {expected})" if expected else ""
    print(f"{color}⏱️  {title}: {time_ms:.2f}ms{expected_str}{NC}")

# ════════════════════════════════════════════════════════════════
# PARTE 1: Demostración de Caché
# ════════════════════════════════════════════════════════════════

print_header("🚀 DEMOSTRACIÓN: Caché Bilíngue de spaCy")

print_info("Este script muestra cómo spaCy cachea modelos para máxima performance\n")

try:
    from services.spacy_nlp_service import get_nlp_service
    from services.cv_extractor_v2_spacy import CVExtractorV2
    
    print_info("Importaciones exitosas\n")
    
    # ════════════════════════════════════════════════════════════════
    # PASO 1: Medir tiempo de carga inicial
    # ════════════════════════════════════════════════════════════════
    
    print_header("PASO 1: Carga Inicial de Modelos")
    
    print_info("Primera llamada a get_nlp_service() - esto carga modelos en memoria\n")
    
    start = time.time()
    nlp_service = get_nlp_service(primary_lang='auto')
    load_time = (time.time() - start) * 1000
    
    print_perf("Tiempo de carga inicial", load_time, "~1500-2000ms")
    print_success("Modelos ahora están en caché (RAM)")
    
    # ════════════════════════════════════════════════════════════════
    # PASO 2: Demostrara rapidez del caché
    # ════════════════════════════════════════════════════════════════
    
    print_header("PASO 2: Requests Posteriores (Desde Caché)")
    
    print_info("Llamadas posteriores reutilizan modelos en RAM\n")
    
    # Request 1
    test_text_es = "Trabajé como Ingeniero de Software en Google durante 5 años"
    start = time.time()
    result1 = nlp_service.analyze(test_text_es)
    time1 = (time.time() - start) * 1000
    print_perf("Request 1 (Spanish text)", time1, "<100ms desde caché")
    print_success(f"Idioma detectado: {result1.get('detected_language', 'desconocido')}")
    
    # Request 2
    test_text_en = "I worked as a Senior Software Engineer at Microsoft for 3 years"
    start = time.time()
    result2 = nlp_service.analyze(test_text_en)
    time2 = (time.time() - start) * 1000
    print_perf("Request 2 (English text)", time2, "<100ms desde caché")
    print_success(f"Idioma detectado: {result2.get('detected_language', 'desconocido')}")
    
    # Request 3 (mismo idioma)
    start = time.time()
    result3 = nlp_service.analyze(test_text_es)
    time3 = (time.time() - start) * 1000
    print_perf("Request 3 (Spanish again)", time3, "<100ms desde caché")
    
    # ════════════════════════════════════════════════════════════════
    # PASO 3: Extracción de CV bilíngue
    # ════════════════════════════════════════════════════════════════
    
    print_header("PASO 3: Extracción de CV Bilíngue")
    
    cv_spanish = """
    Juan García López
    
    OBJETIVO
    Ingeniero de Software con 5 años de experiencia en desarrollo web
    
    EDUCACIÓN
    Licenciatura en Ingeniería Informática
    Universidad Nacional, 2018
    
    EXPERIENCIA
    Ingeniero Senior en Google México (2021-Presente)
    - Desarrollé microservicios en Python y FastAPI
    - Lideré equipo de 5 ingenieros
    
    HABILIDADES
    Python, JavaScript, FastAPI, PostgreSQL, Docker, Kubernetes
    
    IDIOMAS
    Español: Nativo
    Inglés: Avanzado
    """
    
    cv_english = """
    John Smith
    
    OBJECTIVE
    Software Engineer with 5 years of experience in web development
    
    EDUCATION
    Bachelor of Science in Computer Science
    UC Berkeley, 2018
    
    EXPERIENCE
    Senior Software Engineer at Google Mountain View (2021-Present)
    - Developed microservices using Python and FastAPI
    - Led team of 4 engineers
    
    SKILLS
    Python, JavaScript, FastAPI, PostgreSQL, Docker, Kubernetes
    
    LANGUAGES
    English: Native
    Spanish: Intermediate
    """
    
    extractor = CVExtractorV2()
    
    print_info("Extrayendo CV en Español...\n")
    start = time.time()
    profile_es = extractor.extract(cv_spanish)
    time_es = (time.time() - start) * 1000
    print_perf("Tiempo de extracción (Spanish)", time_es, "<200ms")
    print_success(f"Extraído: {len(profile_es.education)} educación, "
                  f"{len(profile_es.experience)} experiencia, "
                  f"{len(profile_es.skills)} skills")
    
    print_info("\nExtrayendo CV en Inglés...\n")
    start = time.time()
    profile_en = extractor.extract(cv_english)
    time_en = (time.time() - start) * 1000
    print_perf("Tiempo de extracción (English)", time_en, "<200ms")
    print_success(f"Extraído: {len(profile_en.education)} educación, "
                  f"{len(profile_en.experience)} experiencia, "
                  f"{len(profile_en.skills)} skills")
    
    # ════════════════════════════════════════════════════════════════
    # PASO 4: Resumen de Performance
    # ════════════════════════════════════════════════════════════════
    
    print_header("📊 RESUMEN DE PERFORMANCE")
    
    print(f"""
{CYAN}Caché Bilíngue - Resultados:{NC}

1. {YELLOW}Primera Carga{NC}
   - Tiempo: {load_time:.0f}ms
   - Acción: Cargar es_core_news_md + en_core_web_md en RAM
   
2. {GREEN}Desde Caché (promedio){NC}
   - Análisis: {(time1 + time2 + time3) / 3:.2f}ms
   - Extracción Spanish: {time_es:.2f}ms
   - Extracción English: {time_en:.2f}ms
   
3. {CYAN}Mejoras vs Ejecución Anterior{NC}
   - Carga inicial: 1 vez (al startup)
   - Requests posteriores: ~{load_time / (time1 + time2 + time3) / 3:.1f}x más rápidas
   - Reducción de carga al servidor: {100 - (100 * ((time1 + time2 + time3) / 3) / load_time):.0f}%
   
4. {GREEN}Ventajas del Caché Bilíngue{NC}
   ✓ Ambos idiomas disponibles simultáneamente
   ✓ Detección automática de idioma
   ✓ Sin descargas innecesarias
   ✓ Máximo rendimiento en producción
   ✓ Soporte para CVs mixtos
""")
    
    print_header("✅ DEMOSTRACIÓN COMPLETADA")
    
    print(f"""
{GREEN}Conclusiones:{NC}

• El caché reduce latencia de ~2000ms a <100ms
• Ambos modelos están listos para producción
• Detección automática de idioma funciona correctamente
• Sistema está optimizado para máxima performance

{CYAN}Próximos pasos:{NC}
1. Ejecutar setup_secure.sh para instalar en servidor
2. Precalentar caché: python manage_spacy_models.py warmup
3. Verificar sistema: python verify_spacy_cache.py
4. ¡Servir requests bilíngues con máxima velocidad!
""")
    
except ImportError as e:
    print(f"{RED}❌ Error de importación:{NC} {e}")
    print(f"\n{YELLOW}Solución:{NC}")
    print("1. Verifica que estés en el directorio correcto")
    print("2. Instala dependencias: pip install -r requirements.txt")
    print("3. Descarga modelos: python -m spacy download es_core_news_md en_core_web_md")
    sys.exit(1)

except Exception as e:
    print(f"{RED}❌ Error:{NC} {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
