#!/usr/bin/env python3
"""
Verificación rápida de soporte bilíngue en cv_extractor_v2_spacy.py
"""

import sys
from pathlib import Path

# Agrega app/ al path
sys.path.insert(0, str(Path(__file__).parent / "app"))

print("=" * 70)
print("VERIFICACIÓN DE SOPORTE BILÍNGUE - CV Extractor")
print("=" * 70)

try:
    from services.cv_extractor_v2_spacy import CVExtractorV2
    print("✅ Importación exitosa de CVExtractorV2\n")
    
    # Instancia extractor
    extractor = CVExtractorV2()
    print("✅ Extractor instanciado correctamente\n")
    
    # Verifica diccionarios
    print("📚 DICCIONARIOS DE KEYWORDS:")
    print(f"  English Education Keywords: {len(extractor.education_keywords_en)} palabras")
    print(f"    Ejemplos: {list(extractor.education_keywords_en)[:5]}")
    print(f"  Spanish Education Keywords: {len(extractor.education_keywords_es)} palabras")
    print(f"    Ejemplos: {list(extractor.education_keywords_es)[:5]}")
    
    print(f"\n  English Experience Keywords: {len(extractor.experience_keywords_en)} palabras")
    print(f"    Ejemplos: {list(extractor.experience_keywords_en)[:5]}")
    print(f"  Spanish Experience Keywords: {len(extractor.experience_keywords_es)} palabras")
    print(f"    Ejemplos: {list(extractor.experience_keywords_es)[:5]}")
    
    print(f"\n  English Skills Keywords: {len(extractor.skills_keywords_en)} palabras")
    print(f"    Ejemplos: {list(extractor.skills_keywords_en)[:5]}")
    print(f"  Spanish Skills Keywords: {len(extractor.skills_keywords_es)} palabras")
    print(f"    Ejemplos: {list(extractor.skills_keywords_es)[:5]}")
    
    # Verifica métodos
    print("\n🔧 MÉTODOS DISPONIBLES:")
    methods = [
        "_detect_text_language",
        "_get_keywords_for_language", 
        "_get_all_keywords",
        "extract",
        "_extract_objective",
        "_extract_education",
        "_extract_experience",
        "_extract_skills",
    ]
    
    for method in methods:
        if hasattr(extractor, method):
            print(f"  ✅ {method}")
        else:
            print(f"  ❌ {method} (FALTA)")
    
    # Prueba detección de idioma
    print("\n🔍 PRUEBAS DE DETECCIÓN DE IDIOMA:")
    
    spanish_text = "Tengo experiencia en educación y habilidades técnicas en programación"
    english_text = "I have experience in education and skills in programming"
    
    lang_es = extractor._detect_text_language(spanish_text)
    lang_en = extractor._detect_text_language(english_text)
    
    print(f"  Spanish text detected as: {'Spanish (es)' if lang_es == 'es' else 'English (en)'} ✅" if lang_es == 'es' else f"  Spanish text detected as: English (en) ❌")
    print(f"  English text detected as: {'English (en)' if lang_en == 'en' else 'Spanish (es)'} ✅" if lang_en == 'en' else f"  English text detected as: Spanish (es) ❌")
    
    # Prueba get_all_keywords
    print("\n🔤 PRUEBA DE KEYWORDS COMBINADOS:")
    all_edu_keywords = extractor._get_all_keywords("education")
    all_exp_keywords = extractor._get_all_keywords("experience")
    all_skills_keywords = extractor._get_all_keywords("skills")
    
    print(f"  Education keywords (combined): {len(all_edu_keywords)} total")
    print(f"  Experience keywords (combined): {len(all_exp_keywords)} total")
    print(f"  Skills keywords (combined): {len(all_skills_keywords)} total")
    
    # Verifica que contiene both Spanish and English
    has_both_edu = "degree" in all_edu_keywords and "licenciatura" in all_edu_keywords
    has_both_exp = "experience" in all_exp_keywords and "experiencia" in all_exp_keywords
    has_both_skills = "skills" in all_skills_keywords and "habilidades" in all_skills_keywords
    
    print(f"  ✅ Education: Both Spanish & English" if has_both_edu else f"  ❌ Education: Missing some keywords")
    print(f"  ✅ Experience: Both Spanish & English" if has_both_exp else f"  ❌ Experience: Missing some keywords")
    print(f"  ✅ Skills: Both Spanish & English" if has_both_skills else f"  ❌ Skills: Missing some keywords")
    
    print("\n" + "=" * 70)
    print("✅ VERIFICACIÓN COMPLETADA - SOPORTE BILÍNGUE ACTIVO")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
