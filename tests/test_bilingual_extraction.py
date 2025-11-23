#!/usr/bin/env python3
"""
Test script para verificar extracción bilíngue de CV (Spanish + English)
"""

import sys
import logging
from pathlib import Path

# Agrega app/ al path
sys.path.insert(0, str(Path(__file__).parent / "app"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ========================
# DATOS DE PRUEBA
# ========================

CV_ENGLISH = """
John Smith
Software Engineer

OBJECTIVE
Experienced Software Engineer with 5 years of experience developing web applications
and leading technical teams. Seeking a challenging role at a forward-thinking company.

EDUCATION
Bachelor of Science in Computer Science
University of California, Berkeley
Graduated: May 2018
GPA: 3.8/4.0

EXPERIENCE
Senior Software Engineer
Google Inc., Mountain View, CA
January 2021 - Present
- Developed microservices architecture using Python and FastAPI
- Led team of 4 engineers on critical backend systems
- Improved API response time by 40%

Software Developer
Microsoft Corporation, Seattle, WA
June 2018 - December 2020
- Implemented RESTful APIs using C# and ASP.NET Core
- Managed database optimization and performance tuning
- Mentored junior developers on best practices

SKILLS
Programming Languages: Python, JavaScript, C#, SQL
Frameworks: FastAPI, React, ASP.NET Core
Databases: PostgreSQL, MongoDB, Redis
Tools: Git, Docker, Kubernetes, AWS

LANGUAGES
English: Native
Spanish: Intermediate
"""

CV_SPANISH = """
Juan García López
Ingeniero de Software

OBJETIVO
Ingeniero de software experimentado con 6 años de experiencia desarrollando
aplicaciones web y liderando equipos técnicos. Busco un rol desafiante en una
empresa innovadora.

EDUCACIÓN
Licenciatura en Ingeniería Informática
Universidad Nacional Autónoma de México
Graduado: Junio 2017
Promedio: 9.2/10

EXPERIENCIA
Ingeniero de Software Senior
Google México, Ciudad de México
Enero 2021 - Presente
- Desarrollé arquitectura de microservicios usando Python y FastAPI
- Lideré equipo de 5 ingenieros en sistemas críticos
- Mejoré tiempo de respuesta de API en 50%

Desarrollador de Software
Microsoft Latinoamérica, México
Julio 2018 - Diciembre 2020
- Implementé APIs RESTful usando C# y ASP.NET Core
- Gestioné optimización de bases de datos
- Mentoricé desarrolladores junior en mejores prácticas

HABILIDADES
Lenguajes de Programación: Python, JavaScript, C#, SQL
Frameworks: FastAPI, React, ASP.NET Core
Bases de Datos: PostgreSQL, MongoDB, Redis
Herramientas: Git, Docker, Kubernetes, AWS

IDIOMAS
Español: Nativo
Inglés: Avanzado
Francés: Básico
"""

CV_MIXED = """
María Silva
Software Engineer / Ingeniera de Software

OBJECTIVE / OBJETIVO
Desarrolladora full-stack con experiencia en web applications. Experienced developer
seeking challenging roles en empresas innovadoras.

EDUCATION / EDUCACIÓN
Bachelor of Science in Computer Science - 2019
Universidad de Buenos Aires - Licenciatura en Ciencias de la Computación

EXPERIENCE / EXPERIENCIA
Senior Developer at Acme Corp (2021-Present)
Ingeniera Senior en Tecnología de XYZ S.A. (2021-Presente)
- Developed Python microservices / Desarrollé microservicios en Python
- Led cross-functional teams / Lideré equipos multifuncionales
- Managed PostgreSQL databases / Gestioné bases de datos PostgreSQL

SKILLS / HABILIDADES
Python, JavaScript, React, FastAPI, PostgreSQL, Docker

LANGUAGES / IDIOMAS
Spanish (Nativo), English (Advanced), Portuguese (Intermediate)
"""


def test_extraction(cv_text: str, cv_name: str):
    """Prueba extracción de CV"""
    logger.info(f"\n{'='*70}")
    logger.info(f"Testing: {cv_name}")
    logger.info(f"{'='*70}\n")
    
    try:
        from services.cv_extractor_v2_spacy import CVExtractorV2
        
        extractor = CVExtractorV2()
        
        # Detecta idioma
        detected_lang = extractor._detect_text_language(cv_text)
        logger.info(f"🔍 Detected Language: {'Spanish' if detected_lang == 'es' else 'English'} ({detected_lang})")
        
        # Extrae CV
        profile = extractor.extract(cv_text)
        
        # Muestra resultados
        logger.info(f"\n📋 PROFILE EXTRACTION RESULTS:")
        logger.info(f"  Objective: {profile.objective[:80]}...")
        logger.info(f"  Education entries: {len(profile.education)}")
        for edu in profile.education:
            logger.info(f"    - {edu.degree} @ {edu.institution}")
        
        logger.info(f"  Experience entries: {len(profile.experience)}")
        for exp in profile.experience:
            logger.info(f"    - {exp.position} @ {exp.company}")
        
        logger.info(f"  Skills found: {len(profile.skills)}")
        for skill in profile.skills[:5]:
            logger.info(f"    - {skill}")
        if len(profile.skills) > 5:
            logger.info(f"    ... and {len(profile.skills) - 5} more")
        
        logger.info(f"  Languages: {profile.languages}")
        logger.info(f"  Certifications: {len(profile.certifications)}")
        logger.info(f"  Organizations: {profile.organizations}")
        
        logger.info(f"\n✅ Extraction completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during extraction: {e}", exc_info=True)
        return False


def main():
    """Main test runner"""
    logger.info("\n" + "="*70)
    logger.info("BILINGUAL CV EXTRACTION TEST SUITE")
    logger.info("="*70)
    
    results = []
    
    # Test 1: English CV
    results.append(test_extraction(CV_ENGLISH, "English CV"))
    
    # Test 2: Spanish CV
    results.append(test_extraction(CV_SPANISH, "Spanish CV"))
    
    # Test 3: Mixed CV
    results.append(test_extraction(CV_MIXED, "Mixed English/Spanish CV"))
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("TEST SUMMARY")
    logger.info("="*70)
    passed = sum(results)
    total = len(results)
    logger.info(f"Passed: {passed}/{total}")
    
    if passed == total:
        logger.info("✅ All tests passed!")
        return 0
    else:
        logger.error(f"❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
