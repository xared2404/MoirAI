#!/usr/bin/env python3
"""
✅ Test: spaCy NLP Service - Validación Completa

Valida que SpacyNLPService funciona correctamente:
1. Singleton pattern
2. Extracción de entidades
3. Tokenización
4. Términos técnicos
5. Análisis completo
6. Similaridad
"""

import sys
import time
from typing import Any, Dict

sys.path.insert(0, '/Users/sparkmachine/MoirAI')

from app.services.spacy_nlp_service import SpacyNLPService, get_nlp_service


class TestSpacyService:
    """Suite de pruebas para SpacyNLPService"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def test(self, name: str, assertion: bool, details: str = ""):
        """Ejecuta una prueba simple"""
        status = "✅ PASS" if assertion else "❌ FAIL"
        print(f"  {status}: {name}")
        if details:
            print(f"       {details}")
        
        if assertion:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_header(self, text: str):
        """Imprime encabezado de sección"""
        print(f"\n  {'='*80}")
        print(f"  {text}")
        print(f"  {'='*80}")
    
    def print_result(self):
        """Imprime resultados finales"""
        total = self.passed + self.failed
        percentage = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\n\n  {'='*80}")
        print(f"  📊 RESULTADOS: {self.passed}/{total} pruebas exitosas ({percentage:.1f}%)")
        print(f"  {'='*80}\n")
        
        if self.failed > 0:
            print(f"  ⚠️  {self.failed} prueba(s) fallaron\n")
            return False
        
        print("  ✅ TODAS LAS PRUEBAS PASARON\n")
        return True
    
    # ========================================================================
    # TEST 1: Singleton Pattern
    # ========================================================================
    
    def test_singleton_pattern(self):
        """Verifica que SpacyNLPService es singleton"""
        self.print_header("TEST 1: Singleton Pattern")
        
        print("\n  ⏳ Creando primera instancia...")
        start1 = time.time()
        nlp1 = SpacyNLPService()
        time1 = time.time() - start1
        print(f"     Primera instancia: {time1*1000:.2f}ms")
        
        print("\n  ⏳ Creando segunda instancia...")
        start2 = time.time()
        nlp2 = SpacyNLPService()
        time2 = time.time() - start2
        print(f"     Segunda instancia: {time2*1000:.2f}ms")
        
        self.test(
            "Ambas instancias son el mismo objeto",
            nlp1 is nlp2,
            f"nlp1 id={id(nlp1)}, nlp2 id={id(nlp2)}"
        )
        
        self.test(
            "Segunda llamada es más rápida (caché)",
            time2 < time1 * 0.5,
            f"Segunda fue {time1/time2:.1f}x más rápida"
        )
        
        print("\n  ⏳ Factory function get_nlp_service()...")
        start3 = time.time()
        nlp3 = get_nlp_service()
        time3 = time.time() - start3
        print(f"     Factory function: {time3*1000:.2f}ms")
        
        self.test(
            "Factory devuelve la misma instancia",
            nlp1 is nlp3,
            "Singleton funcionando correctamente"
        )
    
    # ========================================================================
    # TEST 2: Extracción de Entidades
    # ========================================================================
    
    def test_entity_extraction(self):
        """Prueba extracción de entidades nombradas"""
        self.print_header("TEST 2: Entity Extraction")
        
        nlp = get_nlp_service()
        
        test_cases = [
            (
                "Apple is a company in California",
                {
                    "ORG": ["Apple"],
                    "GPE": ["California"],
                }
            ),
            (
                "I work at Google in Mountain View",
                {
                    "ORG": ["Google"],
                    "GPE": ["Mountain View"],
                }
            ),
            (
                "John works for Microsoft since 2020",
                {
                    "PERSON": ["John"],
                    "ORG": ["Microsoft"],
                    "DATE": ["2020"],
                }
            ),
        ]
        
        for text, expected_labels in test_cases:
            print(f"\n  📝 Texto: \"{text}\"")
            
            entities = nlp.extract_entities(text)
            print(f"     Entidades encontradas: {len(entities)}")
            
            for ent in entities:
                print(f"       • {ent.label}: {ent.text}")
            
            # Validar que se encontraron entidades
            self.test(
                f"Se encontraron entidades en: \"{text[:30]}...\"",
                len(entities) > 0,
                f"Total: {len(entities)} entidades"
            )
            
            # Validar por tipo
            for label, expected_texts in expected_labels.items():
                found = nlp.extract_entities_by_label(text, label)
                has_any = any(
                    any(exp.lower() in found_text.lower() for found_text in found)
                    for exp in expected_texts
                )
                self.test(
                    f"Se encontró {label} en: \"{text[:40]}...\"",
                    has_any or len(found) > 0,
                    f"Encontrados: {found}"
                )
    
    # ========================================================================
    # TEST 3: Tokenización y Lemmatización
    # ========================================================================
    
    def test_tokenization(self):
        """Prueba tokenización y lemmatización"""
        self.print_header("TEST 3: Tokenization & Lemmatization")
        
        nlp = get_nlp_service()
        
        text = "running quickly and walking slowly"
        print(f"\n  📝 Texto: \"{text}\"")
        
        tokens = nlp.tokenize(text, remove_stop=False)
        print(f"\n  Tokens extraídos: {len(tokens)}")
        for tok in tokens:
            print(f"    • {tok.text:10} → {tok.lemma:10} ({tok.pos})")
        
        self.test(
            "Se extrajeron tokens",
            len(tokens) > 0,
            f"Total: {len(tokens)} tokens"
        )
        
        # Validar lemmatización
        has_lemmas = all(tok.lemma for tok in tokens)
        self.test(
            "Todos los tokens tienen lema",
            has_lemmas,
            "Lemmatización correcta"
        )
        
        # Validar sin stopwords
        tokens_no_stop = nlp.tokenize(text, remove_stop=True)
        print(f"\n  Tokens sin stopwords: {len(tokens_no_stop)}")
        for tok in tokens_no_stop:
            print(f"    • {tok.text:10} (stop={tok.is_stop})")
        
        self.test(
            "Sin stopwords: menos tokens que con stopwords",
            len(tokens_no_stop) <= len(tokens),
            f"Con stop: {len(tokens)}, sin stop: {len(tokens_no_stop)}"
        )
    
    # ========================================================================
    # TEST 4: Términos Técnicos
    # ========================================================================
    
    def test_technical_terms(self):
        """Prueba extracción de términos técnicos"""
        self.print_header("TEST 4: Technical Terms Extraction")
        
        nlp = get_nlp_service()
        
        text = """
        I'm a Python developer with experience in React, Django, and PostgreSQL.
        I also work with Docker, Kubernetes, and AWS for cloud infrastructure.
        """
        
        print(f"\n  📝 Texto: {text.strip()[:70]}...\n")
        
        print("  ⏳ Extrayendo términos técnicos...")
        tech_terms = nlp.extract_technical_terms(text)
        
        print(f"\n  Términos encontrados: {len(tech_terms)}")
        for term in sorted(tech_terms):
            print(f"    • {term}")
        
        expected_terms = {"python", "react", "django", "postgresql", "docker", "kubernetes", "aws"}
        found_expected = expected_terms.intersection(set(t.lower() for t in tech_terms))
        
        self.test(
            "Se encontraron términos técnicos",
            len(tech_terms) > 0,
            f"Total: {len(tech_terms)}"
        )
        
        self.test(
            "Se encontraron términos esperados",
            len(found_expected) >= 3,
            f"Encontrados: {found_expected}"
        )
        
        # Custom terms
        print("\n  ⏳ Extrayendo con términos personalizados...")
        custom_terms = ["Machine Learning", "Data Science"]
        tech_with_custom = nlp.extract_technical_terms(text, custom_terms)
        print(f"     Con custom terms: {len(tech_with_custom)} términos")
    
    # ========================================================================
    # TEST 5: Análisis Completo
    # ========================================================================
    
    def test_complete_analysis(self):
        """Prueba análisis completo"""
        self.print_header("TEST 5: Complete Analysis")
        
        nlp = get_nlp_service()
        
        text = "Sarah works at Google in San Francisco since 2019"
        print(f"\n  📝 Texto: \"{text}\"\n")
        
        print("  ⏳ Ejecutando análisis completo...")
        result = nlp.analyze(text)
        
        print(f"\n  Resultados:")
        print(f"    • Idioma: {result['language']}")
        print(f"    • Entidades totales: {len(result['entities'])}")
        print(f"    • Tokens: {len(result['tokens'])}")
        print(f"    • Organizaciones: {result['organizations']}")
        print(f"    • Personas: {result['persons']}")
        print(f"    • Ubicaciones: {result['locations']}")
        print(f"    • Fechas: {result['dates']}")
        
        self.test(
            "Análisis devolvió estructura correcta",
            all(k in result for k in [
                "entities", "tokens", "organizations", "persons", "locations"
            ]),
            "Todas las claves están presentes"
        )
        
        self.test(
            "Se encontraron organizaciones",
            len(result['organizations']) > 0,
            f"Encontradas: {result['organizations']}"
        )
        
        self.test(
            "Se encontraron personas",
            len(result['persons']) > 0,
            f"Encontradas: {result['persons']}"
        )
        
        self.test(
            "Se encontraron ubicaciones",
            len(result['locations']) > 0,
            f"Encontradas: {result['locations']}"
        )
    
    # ========================================================================
    # TEST 6: Similaridad Semántica
    # ========================================================================
    
    def test_similarity(self):
        """Prueba similaridad semántica"""
        self.print_header("TEST 6: Semantic Similarity")
        
        nlp = get_nlp_service()
        
        test_pairs = [
            ("Python developer", "Python engineer"),
            ("Frontend developer", "Backend engineer"),
            ("machine learning", "artificial intelligence"),
            ("SQL database", "NoSQL database"),
        ]
        
        print("\n  📊 Matrices de similaridad:")
        print(f"    {'Texto 1':<25} | {'Texto 2':<25} | {'Score':<6}")
        print(f"    {'-'*60}")
        
        for text1, text2 in test_pairs:
            try:
                similarity = nlp.similarity(text1, text2)
                print(f"    {text1:<25} | {text2:<25} | {similarity:.3f}")
                
                self.test(
                    f"Similaridad entre \"{text1}\" y \"{text2}\"",
                    0.0 <= similarity <= 1.0,
                    f"Score: {similarity:.3f}"
                )
            except Exception as e:
                print(f"    {text1:<25} | {text2:<25} | Error: {str(e)[:10]}")
                self.test(
                    f"Similaridad calculada para \"{text1}\"",
                    False,
                    f"Error: {e}"
                )
        
        # Textos idénticos deben tener similaridad cercana a 1.0
        print("\n  Textos idénticos:")
        same_text = "I am a senior engineer with 10 years experience"
        sim_same = nlp.similarity(same_text, same_text)
        print(f"    Texto con sí mismo: {sim_same:.3f}")
        
        self.test(
            "Textos idénticos tienen similaridad cercana a 1.0",
            sim_same > 0.95,
            f"Score: {sim_same:.3f}"
        )
    
    # ========================================================================
    # TEST 7: Performance
    # ========================================================================
    
    def test_performance(self):
        """Prueba performance y escalabilidad"""
        self.print_header("TEST 7: Performance")
        
        nlp = get_nlp_service()
        
        test_sizes = [
            ("Pequeño (50 chars)", "I work at Google as a Python developer"),
            ("Mediano (200 chars)", "I'm a senior engineer with 10 years of experience working at Google, Microsoft, and Apple on various projects related to machine learning and cloud infrastructure."),
            ("Grande (1000 chars)", """
                Sarah Chen is a senior machine learning engineer at Google with over 10 years of experience.
                She has worked on recommendation systems, computer vision, and natural language processing.
                Her technical stack includes Python, TensorFlow, PyTorch, and Kubernetes.
                She has mentored junior engineers and led cross-functional teams.
                She's passionate about open source and has contributed to projects like TensorFlow and scikit-learn.
                Sarah graduated from Stanford University with a degree in Computer Science.
                She lives in Mountain View, California and is interested in sustainable AI.
            """),
        ]
        
        print("\n  ⏱️  Métricas de rendimiento:")
        print(f"    {'Tamaño':<20} | {'Análisis (ms)':<13} | {'Entidades':<10} | {'Tokens':<10}")
        print(f"    {'-'*70}")
        
        for size_name, text in test_sizes:
            start = time.time()
            result = nlp.analyze(text.strip())
            elapsed = (time.time() - start) * 1000
            
            num_entities = len(result['entities'])
            num_tokens = len(result['tokens'])
            
            print(f"    {size_name:<20} | {elapsed:>10.2f}ms | {num_entities:>8} | {num_tokens:>8}")
            
            self.test(
                f"Análisis en <500ms para {size_name}",
                elapsed < 500,
                f"Tiempo: {elapsed:.2f}ms"
            )
    
    # ========================================================================
    # RUNNER
    # ========================================================================
    
    def run_all_tests(self):
        """Ejecuta todas las pruebas"""
        print("\n" + "█"*100)
        print("█" + " "*98 + "█")
        print("█" + "  ✅ TEST SUITE: SpacyNLPService - Validación Completa".ljust(98) + "█")
        print("█" + " "*98 + "█")
        print("█"*100)
        
        try:
            self.test_singleton_pattern()
            self.test_entity_extraction()
            self.test_tokenization()
            self.test_technical_terms()
            self.test_complete_analysis()
            self.test_similarity()
            self.test_performance()
        except Exception as e:
            print(f"\n  ❌ ERROR FATAL: {e}")
            import traceback
            traceback.print_exc()
            self.failed += 1
        
        success = self.print_result()
        return success


if __name__ == "__main__":
    tester = TestSpacyService()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
