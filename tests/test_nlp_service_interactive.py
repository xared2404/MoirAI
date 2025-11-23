#!/usr/bin/env python3
"""
Script interactivo para probar todos los métodos del NLPService
Permite validar comportamiento de normalización, tokenización, matching y scoring
"""

import json
from app.services.nlp_service import NLPService, _clean_text
from typing import List, Dict


class NLPServiceTester:
    """Clase para ejecutar pruebas interactivas del NLPService"""
    
    def __init__(self):
        self.nlp_service = NLPService()
        self.test_results = []
    
    # ============================================================================
    # PRUEBAS DE NORMALIZACIÓN (_clean_text)
    # ============================================================================
    
    def test_clean_text(self):
        """Prueba exhaustiva de la función _clean_text"""
        print("\n" + "="*80)
        print("TEST 1: NORMALIZACIÓN DE TEXTO (_clean_text)")
        print("="*80)
        
        test_cases = [
            # (input, descripción)
            ("Python", "Minúsculas básicas"),
            ("C++", "Lenguaje C++"),
            ("C#", "Lenguaje C#"),
            ("Node.js", "Node.js"),
            ("Café con Azúcar", "Acentos y diacríticos"),
            ("Machine Learning & AI/ML", "Caracteres especiales"),
            ("  Python   Developer  ", "Espacios múltiples"),
            ("Python_Developer-2024!", "Símbolos y números"),
            ("", "String vacío"),
            ("   ", "Solo espacios"),
            ("JAVA, C++, Python 3.11", "Múltiples lenguajes"),
            ("naïve résumé café", "Múltiples acentos"),
        ]
        
        results = []
        for input_text, description in test_cases:
            output = _clean_text(input_text)
            results.append({
                "input": input_text,
                "output": output,
                "description": description,
                "length_before": len(input_text),
                "length_after": len(output)
            })
            print(f"\n📝 {description}")
            print(f"   Input:  '{input_text}'")
            print(f"   Output: '{output}'")
        
        self.test_results.append(("clean_text", results))
        return results
    
    # ============================================================================
    # PRUEBAS DE _list_to_text
    # ============================================================================
    
    def test_list_to_text(self):
        """Prueba de concatenación y limpieza de listas de strings"""
        print("\n" + "="*80)
        print("TEST 2: CONVERSIÓN DE LISTAS A TEXTO (_list_to_text)")
        print("="*80)
        
        test_cases = [
            (["Python", "Java", "C++"], "Lista de lenguajes"),
            (["Machine Learning", "Data Science", "AI"], "Conceptos técnicos"),
            (["  Python  ", "  Java  "], "Strings con espacios"),
            ([], "Lista vacía"),
            ([""], "Lista con string vacío"),
            (["Python", "", "Java"], "Lista con strings mezclados"),
            (["Café", "Naïve", "Résumé"], "Strings con acentos"),
        ]
        
        results = []
        for items, description in test_cases:
            output = self.nlp_service._list_to_text(items)
            results.append({
                "input": items,
                "output": output,
                "description": description,
                "num_items": len(items)
            })
            print(f"\n📋 {description}")
            print(f"   Input:  {items}")
            print(f"   Output: '{output}'")
        
        self.test_results.append(("list_to_text", results))
        return results
    
    # ============================================================================
    # PRUEBAS DE _tfidf_cosine
    # ============================================================================
    
    def test_tfidf_cosine(self):
        """Prueba de similitud coseno TF-IDF"""
        print("\n" + "="*80)
        print("TEST 3: SIMILITUD COSENO TF-IDF (_tfidf_cosine)")
        print("="*80)
        
        test_cases = [
            # (text_a, text_b, descripción)
            ("Python developer", "Python developer", "Textos idénticos"),
            ("Python developer", "Python", "Similitud parcial alta"),
            ("Python developer", "Java developer", "Similitud media"),
            ("Python development", "Java programming", "Similitud baja"),
            ("", "Python", "Texto A vacío"),
            ("Python", "", "Texto B vacío"),
            ("", "", "Ambos textos vacíos"),
            (
                "Machine learning with Python and scikit-learn",
                "Machine learning in Python using sklearn",
                "Descripciones similares"
            ),
            (
                "Frontend development with React and Vue.js",
                "Backend development with Django and FastAPI",
                "Dominios diferentes"
            ),
        ]
        
        results = []
        for text_a, text_b, description in test_cases:
            score = self.nlp_service._tfidf_cosine(text_a, text_b)
            results.append({
                "text_a": text_a,
                "text_b": text_b,
                "score": round(score, 4),
                "description": description
            })
            print(f"\n🔍 {description}")
            print(f"   Text A:  '{text_a}'")
            print(f"   Text B:  '{text_b}'")
            print(f"   Score:   {score:.4f}")
        
        self.test_results.append(("tfidf_cosine", results))
        return results
    
    # ============================================================================
    # PRUEBAS DE _matching_items
    # ============================================================================
    
    def test_matching_items(self):
        """Prueba de identificación de items que aparecen en un texto"""
        print("\n" + "="*80)
        print("TEST 4: IDENTIFICACIÓN DE ITEMS COINCIDENTES (_matching_items)")
        print("="*80)
        
        test_cases = [
            # (items, text, descripción)
            (
                ["Python", "Java", "C++"],
                "Buscamos un desarrollador con experiencia en Python y Java",
                "Coincidencias por frase completa"
            ),
            (
                ["Machine Learning", "Data Science"],
                "Se requiere experiencia en machine learning y análisis de datos",
                "Coincidencias parciales por tokens"
            ),
            (
                ["API REST", "FastAPI", "PostgreSQL"],
                "Desarrollador backend con FastAPI y PostgreSQL para APIs",
                "Mezcla de coincidencias completas y parciales"
            ),
            (
                ["React", "Vue", "Angular"],
                "Frontend developer con experiencia en Node.js y TypeScript",
                "Sin coincidencias"
            ),
            (
                [],
                "Cualquier texto aquí",
                "Lista vacía"
            ),
            (
                ["Python", ""],
                "Buscamos Python developer",
                "Items con strings vacíos"
            ),
            (
                ["machine learning", "MACHINE LEARNING", "Machine Learning"],
                "Somos expertos en machine learning",
                "Variaciones de capitalización (normalizadas)"
            ),
        ]
        
        results = []
        for items, text, description in test_cases:
            matches = self.nlp_service._matching_items(items, text)
            results.append({
                "items": items,
                "text": text,
                "matches": matches,
                "description": description,
                "match_count": len(matches)
            })
            print(f"\n✓ {description}")
            print(f"   Items: {items}")
            print(f"   Text:  '{text}'")
            print(f"   Matches: {matches} ({len(matches)} encontrados)")
        
        self.test_results.append(("matching_items", results))
        return results
    
    # ============================================================================
    # PRUEBAS DE calculate_match_score
    # ============================================================================
    
    def test_calculate_match_score(self):
        """Prueba del cálculo de score de matching principal"""
        print("\n" + "="*80)
        print("TEST 5: CÁLCULO DE SCORE DE MATCHING (calculate_match_score)")
        print("="*80)
        
        test_cases = [
            {
                "skills": ["Python", "SQL", "Machine Learning"],
                "projects": [
                    "Sistema de recomendación con Python y sklearn",
                    "API REST con FastAPI y PostgreSQL"
                ],
                "job_desc": "Buscamos desarrollador Python para API REST con experiencia en BD y ML",
                "weights": None,
                "description": "Caso completo: skills + projects + job description"
            },
            {
                "skills": ["Python", "FastAPI"],
                "projects": [],
                "job_desc": "Desarrollador Python con experiencia en FastAPI",
                "weights": None,
                "description": "Solo skills (sin proyectos)"
            },
            {
                "skills": [],
                "projects": ["Backend con FastAPI y PostgreSQL"],
                "job_desc": "API REST con FastAPI y manejo de datos",
                "weights": None,
                "description": "Solo proyectos (sin skills)"
            },
            {
                "skills": [],
                "projects": [],
                "job_desc": "",
                "weights": None,
                "description": "Todos los campos vacíos"
            },
            {
                "skills": ["Python", "Java"],
                "projects": ["Proyecto en Java"],
                "job_desc": "Buscamos desarrollador Python",
                "weights": {"skills": 0.9, "projects": 0.1},
                "description": "Con pesos customizados (favor a skills)"
            },
            {
                "skills": ["Python", "Java"],
                "projects": ["Proyecto en Java"],
                "job_desc": "Buscamos desarrollador Python",
                "weights": {"skills": 0.1, "projects": 0.9},
                "description": "Con pesos customizados (favor a projects)"
            },
            {
                "skills": ["C++", "Node.js", "C#"],
                "projects": ["API con Node.js", "Desktop app en C#"],
                "job_desc": "Desarrollador full-stack con C++, Node.js y C#. Experiencia en APIs.",
                "weights": None,
                "description": "Tokens técnicos especiales (C++, C#, Node.js)"
            },
        ]
        
        results = []
        for test_case in test_cases:
            score, details = self.nlp_service.calculate_match_score(
                test_case["skills"],
                test_case["projects"],
                test_case["job_desc"],
                weights=test_case["weights"]
            )
            
            results.append({
                "description": test_case["description"],
                "skills": test_case["skills"],
                "projects": test_case["projects"],
                "job_desc": test_case["job_desc"],
                "weights": test_case["weights"],
                "score": round(score, 4),
                "details": details
            })
            
            print(f"\n🎯 {test_case['description']}")
            print(f"   Skills:     {test_case['skills']}")
            print(f"   Projects:   {test_case['projects']}")
            print(f"   Job Desc:   '{test_case['job_desc']}'")
            if test_case["weights"]:
                print(f"   Weights:    {test_case['weights']}")
            print(f"   ────────────────────────────────────────")
            print(f"   SCORE: {score:.4f}")
            print(f"   ────────────────────────────────────────")
            print(f"   Skill Similarity:     {details['skill_similarity']:.4f}")
            print(f"   Project Similarity:   {details['project_similarity']:.4f}")
            print(f"   Weights Used:         {details['weights_used']}")
            print(f"   Matching Skills:      {details['matching_skills']}")
            print(f"   Matching Projects:    {details['matching_projects']}")
        
        self.test_results.append(("calculate_match_score", results))
        return results
    
    # ============================================================================
    # PRUEBAS DE EDGE CASES Y SEGURIDAD
    # ============================================================================
    
    def test_security_edge_cases(self):
        """Prueba de casos límite y seguridad (DoS, inputs maliciosos)"""
        print("\n" + "="*80)
        print("TEST 6: CASOS LÍMITE Y SEGURIDAD")
        print("="*80)
        
        test_cases = [
            {
                "skills": ["A" * 300],  # Excede MAX_SKILL_LEN (200)
                "projects": [],
                "job_desc": "Python",
                "description": "Skill muy largo (truncado a 200 chars)"
            },
            {
                "skills": [],
                "projects": ["B" * 3000],  # Excede MAX_PROJECT_LEN (2000)
                "job_desc": "API",
                "description": "Project muy largo (truncado a 2000 chars)"
            },
            {
                "skills": ["Python"],
                "projects": [],
                "job_desc": "C" * 60000,  # Excede MAX_JOB_DESC_LEN (50000)
                "description": "Job description muy larga (truncado a 50000 chars)"
            },
            {
                "skills": None,  # None en lugar de lista
                "projects": None,
                "job_desc": "Python",
                "description": "None en skills y projects (debe convertir a [])"
            },
            {
                "skills": ["Python", None, "Java", ""],  # Mezclados
                "projects": [""],
                "job_desc": "Developer",
                "description": "Lista con None y strings vacíos (debe filtrar)"
            },
            {
                "skills": ["<script>alert('xss')</script>"],
                "projects": ["'; DROP TABLE students; --"],
                "job_desc": "<?php echo 'test'; ?>",
                "description": "Intentos de inyección (debe sanitizar)"
            },
        ]
        
        results = []
        for test_case in test_cases:
            try:
                score, details = self.nlp_service.calculate_match_score(
                    test_case["skills"],
                    test_case["projects"],
                    test_case["job_desc"]
                )
                
                results.append({
                    "description": test_case["description"],
                    "score": round(score, 4),
                    "status": "✅ OK",
                    "details": details
                })
                
                print(f"\n✅ {test_case['description']}")
                print(f"   Score: {score:.4f}")
                print(f"   Status: Procesado sin errores")
                
            except Exception as e:
                results.append({
                    "description": test_case["description"],
                    "error": str(e),
                    "status": "❌ ERROR"
                })
                print(f"\n❌ {test_case['description']}")
                print(f"   Error: {str(e)}")
        
        self.test_results.append(("security_edge_cases", results))
        return results
    
    # ============================================================================
    # GENERACIÓN DE REPORTE
    # ============================================================================
    
    def generate_report(self):
        """Genera un reporte JSON de todas las pruebas"""
        print("\n" + "="*80)
        print("REPORTE DE PRUEBAS")
        print("="*80)
        
        report = {
            "total_test_groups": len(self.test_results),
            "tests": {name: len(results) for name, results in self.test_results}
        }
        
        print("\nResumen de pruebas ejecutadas:")
        for name, count in report["tests"].items():
            print(f"  ✓ {name}: {count} casos")
        
        # Guardar reporte detallado
        report_file = "/Users/sparkmachine/MoirAI/nlp_service_test_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "summary": report,
                    "detailed_results": [
                        {"test_group": name, "results": results}
                        for name, results in self.test_results
                    ]
                },
                f,
                indent=2,
                ensure_ascii=False
            )
        
        print(f"\n📄 Reporte detallado guardado en: {report_file}")
        return report
    
    # ============================================================================
    # EJECUCIÓN PRINCIPAL
    # ============================================================================
    
    def run_all_tests(self):
        """Ejecuta todas las pruebas"""
        print("\n" + "🚀 "*40)
        print("INICIANDO PRUEBAS INTERACTIVAS DEL NLPService")
        print("🚀 "*40)
        
        self.test_clean_text()
        self.test_list_to_text()
        self.test_tfidf_cosine()
        self.test_matching_items()
        self.test_calculate_match_score()
        self.test_security_edge_cases()
        
        self.generate_report()
        
        print("\n" + "✨ "*40)
        print("TODAS LAS PRUEBAS COMPLETADAS")
        print("✨ "*40 + "\n")


def main():
    """Función principal"""
    tester = NLPServiceTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
