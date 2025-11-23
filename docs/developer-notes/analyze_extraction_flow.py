#!/usr/bin/env python3
"""
Análisis: ¿Dónde se pierde la información en la extracción?

Simulamos el flujo exacto del CV del usuario para ver dónde falla.
"""

import sys
sys.path.insert(0, '/Users/sparkmachine/MoirAI')

from app.services.unsupervised_cv_extractor import UnsupervisedCVExtractor
import json

# Simular el texto del CV del usuario (lo que el backend recibió)
cv_text = """
Enrique Valdés García
Ciudad de México, México • 5+ años de experiencia

OBJETIVO PROFESIONAL
Científico de datos apasionado por extraer insights de grandes volúmenes de datos. 
Experiencia en machine learning, estadística y análisis exploratorio. 
Busco contribuir en equipos de datos que generen impacto empresarial.

EDUCACIÓN
Universidad de México
Licenciatura en Ciencia de Datos para Negocios
2024

EXPERIENCIA PROFESIONAL
Nu México - Investigador de Operaciones (Fraude)
Mayo 2022 – Presente
• Analicé patrones y anomalías en datos de transacciones para detección de fraude
• Desarrollé modelos de machine learning para prevención de riesgos
• Utilicé Tableau, Power BI, Python, SQL en análisis avanzados

HABILIDADES TÉCNICAS
Python, SQL, Machine Learning, Deep Learning, Tableau, Power BI, Looker, 
ETL, Excel, Git, AWS, Docker

IDIOMAS
Español (Nativo), Inglés (Fluido), Francés (Básico)

CERTIFICACIONES
AWS Certified Developer
Google Cloud Professional
"""

print("=" * 80)
print("🔬 ANÁLISIS: Flujo de Extracción del CV")
print("=" * 80)

print("\n1️⃣  TEXTO ORIGINAL (primeras 300 chars):")
print("-" * 80)
print(cv_text[:300] + "...")

# Ejecutar extractor
extractor = UnsupervisedCVExtractor()
result = extractor.extract(cv_text)

print("\n2️⃣  RESULTADO DE EXTRACCIÓN:")
print("-" * 80)
print(f"Overall Confidence: {result.overall_confidence:.2f}")

print(f"\n📌 Objetivo:\n  {result.objective[:100] if result.objective else 'N/A'}...")

print(f"\n🎓 Educación ({len(result.education)} items):")
for i, edu in enumerate(result.education, 1):
    print(f"  {i}. {edu.get('institution', 'N/A')} - {edu.get('degree', 'N/A')} ({edu.get('graduation_year', 'N/A')})")

print(f"\n💼 Experiencia ({len(result.experience)} items):")
for i, exp in enumerate(result.experience, 1):
    print(f"  {i}. {exp.get('position', 'N/A')} en {exp.get('company', 'N/A')} ({exp.get('start_date', 'N/A')})")

print(f"\n🛠️  Skills ({len(result.skills)} items):")
print(f"  {', '.join(result.skills[:10])}")

print(f"\n🌍 Idiomas ({len(result.languages)} items):")
print(f"  {', '.join(result.languages)}")

print(f"\n🏆 Certificaciones ({len(result.certifications)} items):")
print(f"  {', '.join(result.certifications)}")

print("\n" + "=" * 80)
print("✨ CONCLUSIÓN:")
print("=" * 80)
if result.overall_confidence > 0.7:
    print("✅ Extracción de BUENA CALIDAD")
else:
    print("❌ Extracción de MALA CALIDAD - necesita mejoras")

# Mostrar métodos usados
print("\nMétodos de extracción:")
for field, method in result.method_used_for_each.items():
    print(f"  - {field}: {method}")
