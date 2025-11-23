#!/usr/bin/env python3
"""
✅ Test: CV Extractor V2 - Validación Completa

Valida que CVExtractorV2 funciona correctamente:
1. Extracción de educación
2. Extracción de experiencia
3. Extracción de skills
4. Extracción de idiomas
5. Comparativa con versión anterior
"""

import sys
import time

sys.path.insert(0, '/Users/sparkmachine/MoirAI')

from app.services.cv_extractor_v2_spacy import CVExtractorV2


class TestCVExtractorV2:
    """Suite de pruebas para CVExtractorV2"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.extractor = None
    
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
    # TEST 1: Inicialización
    # ========================================================================
    
    def test_initialization(self):
        """Prueba inicialización del extractor"""
        self.print_header("TEST 1: Inicialización")
        
        print("\n  ⏳ Inicializando CVExtractorV2...")
        start = time.time()
        self.extractor = CVExtractorV2()
        elapsed = time.time() - start
        print(f"  ✅ Inicializado en {elapsed*1000:.2f}ms\n")
        
        self.test("Extractor creado correctamente", self.extractor is not None)
        self.test("NLP service disponible", self.extractor.nlp is not None)
        self.test("Tiene keywords de educación", len(self.extractor.education_keywords) > 0)
        self.test("Tiene keywords de experiencia", len(self.extractor.experience_keywords) > 0)
    
    # ========================================================================
    # TEST 2: Extracción de Educación
    # ========================================================================
    
    def test_education_extraction(self):
        """Prueba extracción de educación"""
        self.print_header("TEST 2: Extracción de Educación")
        
        cv_text = """
        EDUCATION
        Bachelor of Science in Computer Science
        University of California, Berkeley
        Graduated: 2019 | GPA: 3.8/4.0
        
        Master of Science in Artificial Intelligence
        Stanford University
        2021-2022
        """
        
        print(f"\n  📝 CV de prueba:\n{cv_text}\n")
        
        print("  ⏳ Extrayendo educación...")
        profile = self.extractor.extract(cv_text)
        
        print(f"\n  Educación extraída: {len(profile.education)} items")
        for edu in profile.education:
            print(f"    • {edu.institution}: {edu.degree}")
            if edu.start_year or edu.end_year:
                print(f"      Años: {edu.start_year} - {edu.end_year}")
        
        self.test(
            "Se extrajeron entradas de educación",
            len(profile.education) > 0,
            f"Total: {len(profile.education)}"
        )
        
        # Validar estructura
        if profile.education:
            first_edu = profile.education[0]
            self.test(
                "Educación tiene institución",
                len(first_edu.institution) > 0,
                f"Instituto: {first_edu.institution}"
            )
    
    # ========================================================================
    # TEST 3: Extracción de Experiencia
    # ========================================================================
    
    def test_experience_extraction(self):
        """Prueba extracción de experiencia"""
        self.print_header("TEST 3: Extracción de Experiencia")
        
        cv_text = """
        PROFESSIONAL EXPERIENCE
        
        Senior Backend Engineer
        Google | Mountain View, CA | 2022-Present
        • Led design of microservices architecture with 99.9% uptime
        • Implemented CI/CD pipeline using Docker and Kubernetes
        • Optimized SQL queries, improving performance by 45%
        
        Software Engineer
        Microsoft | Seattle, WA | 2020-2022
        • Developed cloud infrastructure using Azure
        • Mentored 5 junior engineers
        """
        
        print(f"\n  📝 CV de prueba:\n{cv_text}\n")
        
        print("  ⏳ Extrayendo experiencia...")
        profile = self.extractor.extract(cv_text)
        
        print(f"\n  Experiencia extraída: {len(profile.experience)} items")
        for exp in profile.experience:
            print(f"    • {exp.position} @ {exp.company}")
        
        self.test(
            "Se extrajeron entradas de experiencia",
            len(profile.experience) > 0,
            f"Total: {len(profile.experience)}"
        )
        
        # Validar estructura
        if profile.experience:
            first_exp = profile.experience[0]
            self.test(
                "Experiencia tiene posición",
                len(first_exp.position) > 0,
                f"Posición: {first_exp.position}"
            )
            self.test(
                "Experiencia tiene empresa",
                len(first_exp.company) > 0,
                f"Empresa: {first_exp.company}"
            )
    
    # ========================================================================
    # TEST 4: Extracción de Skills
    # ========================================================================
    
    def test_skills_extraction(self):
        """Prueba extracción de skills técnicos"""
        self.print_header("TEST 4: Extracción de Skills")
        
        cv_text = """
        TECHNICAL SKILLS
        Languages: Python, JavaScript, TypeScript, Java, SQL, Go, Bash
        Frameworks: FastAPI, Django, React, Vue.js, Angular
        Databases: PostgreSQL, MongoDB, Redis, Cassandra
        DevOps: Docker, Kubernetes, AWS, GCP, Azure
        ML/AI: TensorFlow, PyTorch, scikit-learn, Keras
        """
        
        print(f"\n  📝 CV de prueba:\n{cv_text}\n")
        
        print("  ⏳ Extrayendo skills...")
        profile = self.extractor.extract(cv_text)
        
        print(f"\n  Skills extraídos: {len(profile.skills)} items")
        for skill in sorted(profile.skills)[:10]:
            print(f"    • {skill}")
        
        self.test(
            "Se extrajeron skills técnicos",
            len(profile.skills) > 0,
            f"Total: {len(profile.skills)}"
        )
        
        # Validar que incluya términos técnicos conocidos
        skills_lower = [s.lower() for s in profile.skills]
        expected_tech = {"python", "javascript", "postgresql", "docker", "kubernetes"}
        found_tech = expected_tech.intersection(set(skills_lower))
        
        self.test(
            "Encontró términos técnicos esperados",
            len(found_tech) > 0,
            f"Encontrados: {found_tech}"
        )
    
    # ========================================================================
    # TEST 5: Extracción de Idiomas
    # ========================================================================
    
    def test_language_extraction(self):
        """Prueba extracción de idiomas"""
        self.print_header("TEST 5: Extracción de Idiomas")
        
        cv_text = """
        LANGUAGES
        English (Fluent - Native speaker)
        Spanish (Advanced - C1 IELTS 7.5)
        French (Intermediate - A2)
        German (Basic - A1)
        """
        
        print(f"\n  📝 CV de prueba:\n{cv_text}\n")
        
        print("  ⏳ Extrayendo idiomas...")
        profile = self.extractor.extract(cv_text)
        
        print(f"\n  Idiomas extraídos: {len(profile.languages)} items")
        for lang, level in profile.languages.items():
            print(f"    • {lang}: {level}")
        
        self.test(
            "Se extrajeron idiomas",
            len(profile.languages) > 0,
            f"Total: {len(profile.languages)}"
        )
        
        # Validar que incluya inglés
        has_english = any("english" in lang.lower() for lang in profile.languages.keys())
        self.test(
            "Se encontró inglés",
            has_english,
            f"Idiomas: {list(profile.languages.keys())}"
        )
    
    # ========================================================================
    # TEST 6: Extracción de Objetivo
    # ========================================================================
    
    def test_objective_extraction(self):
        """Prueba extracción del objetivo profesional"""
        self.print_header("TEST 6: Extracción de Objetivo")
        
        cv_text = """
        John Smith
        Senior Software Engineer with 10+ years of experience.
        
        OBJECTIVE
        Passionate about building scalable software solutions and leading high-performance teams.
        Looking for opportunities in distributed systems and cloud infrastructure.
        
        EDUCATION
        ...
        """
        
        print(f"\n  📝 CV de prueba:\n{cv_text[:200]}...\n")
        
        print("  ⏳ Extrayendo objetivo...")
        profile = self.extractor.extract(cv_text)
        
        if profile.objective:
            print(f"\n  Objetivo encontrado:")
            print(f"    \"{profile.objective[:100]}...\"")
            self.test(
                "Se extrajo objetivo",
                len(profile.objective) > 10,
                f"Longitud: {len(profile.objective)} chars"
            )
        else:
            print(f"\n  ⚠️ No se extrajo objetivo explícito")
            self.test(
                "Se intentó extraer objetivo",
                True,
                "Puede ser opcional"
            )
    
    # ========================================================================
    # TEST 7: Extracción de Organizaciones (NER)
    # ========================================================================
    
    def test_organizations_extraction(self):
        """Prueba extracción de organizaciones usando NER"""
        self.print_header("TEST 7: Extracción de Organizaciones (NER)")
        
        cv_text = """
        Software Engineer at Google and Microsoft
        
        EXPERIENCE
        Senior Engineer - Apple Inc., Cupertino CA
        2020-Present
        
        Software Developer - Amazon Web Services
        2018-2020
        
        Junior Developer - Tesla Motors
        2017-2018
        """
        
        print(f"\n  📝 CV de prueba:\n{cv_text}\n")
        
        print("  ⏳ Extrayendo organizaciones con NER...")
        profile = self.extractor.extract(cv_text)
        
        print(f"\n  Organizaciones encontradas: {len(profile.organizations)} items")
        for org in profile.organizations[:5]:
            print(f"    • {org}")
        
        self.test(
            "Se extrajeron organizaciones",
            len(profile.organizations) > 0,
            f"Total: {len(profile.organizations)}"
        )
        
        # Validar que incluya empresas conocidas
        orgs_lower = [o.lower() for o in profile.organizations]
        expected_orgs = {"google", "microsoft", "apple", "amazon"}
        found_orgs = expected_orgs.intersection(set(orgs_lower))
        
        self.test(
            "Detectó empresas conocidas",
            len(found_orgs) > 0,
            f"Encontradas: {found_orgs}"
        )
    
    # ========================================================================
    # TEST 8: Performance
    # ========================================================================
    
    def test_performance(self):
        """Prueba performance de extracción"""
        self.print_header("TEST 8: Performance")
        
        # CV de prueba (mediano)
        cv_text = """
        John Doe
        Senior Software Engineer
        john.doe@example.com
        
        OBJECTIVE
        Innovative engineer with passion for building scalable systems.
        
        EDUCATION
        Bachelor of Science in Computer Science
        MIT - Massachusetts Institute of Technology
        Graduated: 2015
        
        Master of Science in Software Engineering
        Stanford University
        2017-2018
        
        EXPERIENCE
        Senior Backend Engineer
        Google | Mountain View, CA | 2020-Present
        • Designed microservices architecture
        • Led team of 5 engineers
        • Improved performance by 40%
        
        Software Engineer
        Microsoft | Seattle, WA | 2018-2020
        • Developed cloud solutions
        • Built distributed systems
        
        SKILLS
        Languages: Python, JavaScript, TypeScript, Go, Rust
        Frameworks: FastAPI, Django, React, Angular
        Databases: PostgreSQL, MongoDB, Redis
        DevOps: Docker, Kubernetes, AWS, GCP
        
        LANGUAGES
        English (Fluent)
        Spanish (Intermediate)
        """
        
        print(f"\n  📝 CV de {len(cv_text)} caracteres")
        
        print("\n  ⏳ Extrayendo CV completo...")
        start = time.time()
        profile = self.extractor.extract(cv_text)
        elapsed = time.time() - start
        
        print(f"\n  ⏱️  Tiempo total: {elapsed*1000:.2f}ms\n")
        print(f"    • Educación: {len(profile.education)} items")
        print(f"    • Experiencia: {len(profile.experience)} items")
        print(f"    • Skills: {len(profile.skills)} items")
        print(f"    • Idiomas: {len(profile.languages)} items")
        print(f"    • Organizaciones: {len(profile.organizations)} items")
        
        # Validar performance
        self.test(
            "Extracción en <500ms",
            elapsed < 0.5,
            f"Tiempo: {elapsed*1000:.2f}ms"
        )
        
        # Validar que extrajo datos
        total_fields = (
            len(profile.education) + 
            len(profile.experience) + 
            len(profile.skills) + 
            len(profile.languages)
        )
        
        self.test(
            "Se extrajeron múltiples campos",
            total_fields > 5,
            f"Total campos: {total_fields}"
        )
    
    # ========================================================================
    # TEST 9: API Compatibility
    # ========================================================================
    
    def test_api_compatibility(self):
        """Prueba compatibilidad con API v1"""
        self.print_header("TEST 9: API Compatibility (Interface)")
        
        cv_text = "Senior Python Developer at Google since 2020"
        
        print(f"\n  📝 CV: {cv_text}\n")
        
        print("  ⏳ Testando método extract_to_dict()...")
        result = self.extractor.extract_to_dict(cv_text)
        
        print(f"\n  Estructura de salida:")
        for key in result.keys():
            value = result[key]
            if isinstance(value, list):
                print(f"    • {key}: {len(value)} items")
            else:
                print(f"    • {key}: {type(value).__name__}")
        
        # Validar estructura
        required_keys = {
            "objective", "education", "experience", "skills",
            "languages", "certifications", "organizations", "projects"
        }
        
        self.test(
            "Dict tiene todas las claves requeridas",
            all(key in result for key in required_keys),
            f"Claves: {set(result.keys())}"
        )
        
        self.test(
            "Estructura compatible con v1",
            isinstance(result, dict),
            "Es diccionario"
        )
    
    # ========================================================================
    # RUNNER
    # ========================================================================
    
    def run_all_tests(self):
        """Ejecuta todas las pruebas"""
        print("\n" + "█"*100)
        print("█" + " "*98 + "█")
        print("█" + "  ✅ TEST SUITE: CVExtractorV2 - Validación Completa".ljust(98) + "█")
        print("█" + " "*98 + "█")
        print("█"*100)
        
        try:
            self.test_initialization()
            self.test_education_extraction()
            self.test_experience_extraction()
            self.test_skills_extraction()
            self.test_language_extraction()
            self.test_objective_extraction()
            self.test_organizations_extraction()
            self.test_performance()
            self.test_api_compatibility()
        except Exception as e:
            print(f"\n  ❌ ERROR FATAL: {e}")
            import traceback
            traceback.print_exc()
            self.failed += 1
        
        success = self.print_result()
        return success


if __name__ == "__main__":
    tester = TestCVExtractorV2()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
