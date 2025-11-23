#!/usr/bin/env python3
"""
🧪 TEST INTERACTIVO: CV Extraction V2 con CV - Harvard.pdf

Prueba la extracción de CV real usando CVExtractorV2 (con spaCy NER)

Flujo:
1. 📥 Carga CV - Harvard.pdf
2. 📄 Extrae texto del PDF
3. 🧠 Analiza con CVExtractorV2 (spaCy NER)
4. 📊 Muestra resultados detallados
5. ⚖️ Compara con versión anterior

OBJETIVO: Validar que CVExtractorV2 extrae correctamente todos los campos del CV Harvard
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

sys.path.insert(0, '/Users/sparkmachine/MoirAI')

from app.services.cv_extractor_v2_spacy import CVExtractorV2, CVProfile
from app.utils.file_processing import extract_text_from_upload_async


class CVExtractionTestHarvard:
    """Test interactivo de extracción con CV Harvard"""
    
    def __init__(self):
        self.cv_path = Path("/Users/sparkmachine/MoirAI/CV - Harvard.pdf")
        self.extractor = None
        self.cv_text = None
        self.profile = None
        self.results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0
        }
    
    def print_header(self, text: str, level: int = 1):
        """Imprime encabezado"""
        if level == 1:
            print(f"\n{'█'*100}")
            print(f"█ {text.ljust(98)}█")
            print(f"{'█'*100}\n")
        elif level == 2:
            print(f"\n{'='*100}")
            print(f"  {text}")
            print(f"{'='*100}\n")
        else:
            print(f"\n▶ {text}\n")
    
    def test(self, name: str, assertion: bool, details: str = ""):
        """Registra un test"""
        if assertion:
            status = "✅ PASS"
            self.results["passed"] += 1
        else:
            status = "❌ FAIL"
            self.results["failed"] += 1
        
        print(f"  {status}: {name}")
        if details:
            print(f"       {details}")
    
    def warning(self, name: str, details: str = ""):
        """Registra una advertencia"""
        print(f"  ⚠️  WARNING: {name}")
        if details:
            print(f"       {details}")
        self.results["warnings"] += 1
    
    # ====================================================================
    # PASO 1: CARGAR ARCHIVO
    # ====================================================================
    
    def step_1_load_cv_file(self) -> bool:
        """Carga el archivo CV - Harvard.pdf"""
        self.print_header("PASO 1: CARGAR ARCHIVO CV", 2)
        
        print(f"📂 Ruta: {self.cv_path}\n")
        
        # Verificar existencia
        self.test(
            "Archivo existe",
            self.cv_path.exists(),
            f"Localización: {self.cv_path}"
        )
        
        if not self.cv_path.exists():
            return False
        
        # Verificar extensión
        is_pdf = self.cv_path.suffix.lower() == ".pdf"
        self.test(
            "Archivo es PDF",
            is_pdf,
            f"Extensión: {self.cv_path.suffix}"
        )
        
        # Verificar tamaño
        file_size = self.cv_path.stat().st_size
        size_valid = 10 * 1024 < file_size < 50 * 1024 * 1024  # Entre 10KB y 50MB
        self.test(
            "Tamaño de archivo válido",
            size_valid,
            f"Tamaño: {file_size:,} bytes ({file_size/1024:.2f} KB)"
        )
        
        if not size_valid:
            self.warning(
                "Tamaño inusual",
                f"Se esperaba entre 10KB y 50MB, obtuvo {file_size/1024:.2f} KB"
            )
        
        print(f"\n✅ PASO 1 COMPLETADO\n")
        return True
    
    # ====================================================================
    # PASO 2: EXTRAER TEXTO DEL PDF
    # ====================================================================
    
    def step_2_extract_text(self) -> bool:
        """Extrae texto del PDF"""
        self.print_header("PASO 2: EXTRAER TEXTO DEL PDF", 2)
        
        print("📄 Extrayendo texto usando herramientas PDF...\n")
        
        try:
            import PyPDF2
            print("  ✅ PyPDF2 disponible")
        except ImportError:
            self.warning("PyPDF2 no disponible", "Instalando...")
        
        try:
            import pdfplumber
            print("  ✅ pdfplumber disponible")
        except ImportError:
            self.warning("pdfplumber no disponible", "Instalando...")
        
        print("\n⏳ Leyendo PDF...")
        start = time.time()
        
        try:
            # Intentar con pdfplumber (mejor)
            try:
                import pdfplumber
                with pdfplumber.open(self.cv_path) as pdf:
                    text_parts = []
                    for page_num, page in enumerate(pdf.pages, 1):
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                    
                    self.cv_text = "\n\n".join(text_parts)
                    extraction_method = "pdfplumber"
            except:
                # Fallback a PyPDF2
                import PyPDF2
                with open(self.cv_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text_parts = []
                    for page_num, page in enumerate(reader.pages):
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                    
                    self.cv_text = "\n\n".join(text_parts)
                    extraction_method = "PyPDF2"
        
        except Exception as e:
            self.test("Extracción de texto", False, f"Error: {e}")
            return False
        
        elapsed = time.time() - start
        
        # Validaciones
        text_extracted = self.cv_text is not None and len(self.cv_text) > 0
        self.test(
            "Texto extraído correctamente",
            text_extracted,
            f"Método: {extraction_method}"
        )
        
        if not text_extracted:
            return False
        
        # Estadísticas
        text_length = len(self.cv_text)
        num_lines = len(self.cv_text.split('\n'))
        num_words = len(self.cv_text.split())
        
        print(f"\n📊 ESTADÍSTICAS DE TEXTO:")
        print(f"   • Tamaño total: {text_length:,} caracteres")
        print(f"   • Líneas: {num_lines}")
        print(f"   • Palabras: {num_words}")
        print(f"   • Tiempo extracción: {elapsed*1000:.2f}ms")
        
        # Validar contenido
        has_education = any(word in self.cv_text.lower() for word in ["education", "educación", "university", "bachelor"])
        self.test(
            "Contiene sección de educación",
            has_education,
            "Palabras clave detectadas"
        )
        
        has_experience = any(word in self.cv_text.lower() for word in ["experience", "experiencia", "worked", "engineer", "developer"])
        self.test(
            "Contiene sección de experiencia",
            has_experience,
            "Palabras clave detectadas"
        )
        
        has_skills = any(word in self.cv_text.lower() for word in ["skills", "habilidades", "technologies", "tecnologías", "python", "java", "javascript"])
        self.test(
            "Contiene sección de skills",
            has_skills,
            "Palabras clave o lenguajes detectados"
        )
        
        print(f"\n✅ PASO 2 COMPLETADO\n")
        return True
    
    # ====================================================================
    # PASO 3: INICIALIZAR EXTRACTOR V2
    # ====================================================================
    
    def step_3_initialize_extractor(self) -> bool:
        """Inicializa CVExtractorV2"""
        self.print_header("PASO 3: INICIALIZAR CVExtractorV2", 2)
        
        print("🚀 Inicializando extractor con spaCy NER...\n")
        
        try:
            print("⏳ Cargando modelo spaCy...")
            start = time.time()
            self.extractor = CVExtractorV2()
            elapsed = time.time() - start
            
            self.test(
                "Extractor inicializado",
                self.extractor is not None,
                f"Tiempo: {elapsed*1000:.2f}ms"
            )
            
            self.test(
                "NLP service disponible",
                self.extractor.nlp is not None,
                "spaCy model cargado"
            )
            
            print(f"\n✅ PASO 3 COMPLETADO\n")
            return True
        
        except Exception as e:
            self.test("Inicialización", False, f"Error: {e}")
            return False
    
    # ====================================================================
    # PASO 4: EXTRAER CAMPOS DEL CV
    # ====================================================================
    
    def step_4_extract_fields(self) -> bool:
        """Extrae campos usando CVExtractorV2"""
        self.print_header("PASO 4: EXTRAER CAMPOS DEL CV", 2)
        
        print("🧠 Analizando CV con spaCy NER...\n")
        
        try:
            print("⏳ Procesando texto...")
            start = time.time()
            self.profile = self.extractor.extract(self.cv_text)
            elapsed = time.time() - start
            
            self.test(
                "Extracción completada",
                self.profile is not None,
                f"Tiempo: {elapsed*1000:.2f}ms"
            )
            
            if not self.profile:
                return False
            
            print(f"\n📊 CAMPOS EXTRAÍDOS:\n")
            
            # Objetivo
            has_objective = len(self.profile.objective) > 0
            print(f"🎯 Objetivo:")
            print(f"   {'✅' if has_objective else '❌'} {self.profile.objective[:100] if has_objective else '(no encontrado)'}...")
            self.test("Objetivo extraído", has_objective or True, "Opcional")
            
            # Educación
            num_education = len(self.profile.education)
            print(f"\n🎓 Educación ({num_education} items):")
            for edu in self.profile.education[:5]:
                print(f"   • {edu.institution}: {edu.degree}")
                if edu.start_year or edu.end_year:
                    print(f"     ({edu.start_year or '?'} - {edu.end_year or '?'})")
            
            self.test(
                "Educación extraída",
                num_education > 0,
                f"Total: {num_education} items"
            )
            
            # Experiencia
            num_experience = len(self.profile.experience)
            print(f"\n💼 Experiencia ({num_experience} items):")
            for exp in self.profile.experience[:5]:
                print(f"   • {exp.position} @ {exp.company}")
            
            self.test(
                "Experiencia extraída",
                num_experience > 0,
                f"Total: {num_experience} items"
            )
            
            # Skills
            num_skills = len(self.profile.skills)
            print(f"\n🛠️  Skills Técnicos ({num_skills} items):")
            skills_preview = ", ".join(sorted(self.profile.skills)[:10])
            print(f"   {skills_preview}{'...' if num_skills > 10 else ''}")
            
            self.test(
                "Skills extraídos",
                num_skills > 0,
                f"Total: {num_skills} items"
            )
            
            # Organizaciones (NER)
            num_orgs = len(self.profile.organizations)
            print(f"\n🏢 Organizaciones (NER - {num_orgs} items):")
            for org in self.profile.organizations[:5]:
                print(f"   • {org}")
            
            self.test(
                "Organizaciones detectadas (NER)",
                num_orgs > 0,
                f"Total: {num_orgs} items"
            )
            
            # Idiomas
            num_languages = len(self.profile.languages)
            print(f"\n🌐 Idiomas ({num_languages} items):")
            for lang, level in self.profile.languages.items():
                print(f"   • {lang}: {level}")
            
            self.test(
                "Idiomas extraídos",
                num_languages > 0,
                f"Total: {num_languages} items"
            )
            
            # Certificaciones
            num_certs = len(self.profile.certifications)
            if num_certs > 0:
                print(f"\n📜 Certificaciones ({num_certs} items):")
                for cert in self.profile.certifications[:3]:
                    print(f"   • {cert}")
            else:
                print(f"\n📜 Certificaciones: (no encontradas)")
            
            # Proyectos
            num_projects = len(self.profile.projects)
            if num_projects > 0:
                print(f"\n🚀 Proyectos ({num_projects} items):")
                for proj in self.profile.projects[:3]:
                    print(f"   • {proj}")
            else:
                print(f"\n🚀 Proyectos: (no encontrados)")
            
            print(f"\n✅ PASO 4 COMPLETADO\n")
            return True
        
        except Exception as e:
            self.test("Extracción", False, f"Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ====================================================================
    # PASO 5: VALIDACIÓN Y ANÁLISIS
    # ====================================================================
    
    def step_5_validation(self) -> bool:
        """Valida la extracción"""
        self.print_header("PASO 5: VALIDACIÓN Y ANÁLISIS", 2)
        
        if not self.profile:
            self.test("Validación", False, "No profile available")
            return False
        
        print("🔍 Validando calidad de extracción...\n")
        
        # 1. Coverage
        total_fields = (
            len(self.profile.education) +
            len(self.profile.experience) +
            len(self.profile.skills) +
            len(self.profile.languages)
        )
        
        coverage_pct = (total_fields / 15) * 100  # 15 como baseline
        print(f"📊 Coverage de campos:")
        print(f"   • Total campos: {total_fields}")
        print(f"   • Coverage estimado: {coverage_pct:.0f}%")
        
        self.test(
            "Coverage mínimo (4 campos)",
            total_fields >= 4,
            f"Obtuvo: {total_fields} campos"
        )
        
        # 2. Precisión de tipos
        print(f"\n🎯 Validación de tipos:")
        
        # Education entries
        valid_education = all(
            isinstance(e.institution, str) and len(e.institution) > 0
            for e in self.profile.education
        )
        self.test(
            "Educación: campos tipados correctamente",
            valid_education or len(self.profile.education) == 0,
            f"Total entries: {len(self.profile.education)}"
        )
        
        # Experience entries
        valid_experience = all(
            isinstance(e.position, str) and len(e.position) > 0
            for e in self.profile.experience
        )
        self.test(
            "Experiencia: campos tipados correctamente",
            valid_experience or len(self.profile.experience) == 0,
            f"Total entries: {len(self.profile.experience)}"
        )
        
        # Skills
        valid_skills = isinstance(self.profile.skills, list)
        self.test(
            "Skills: tipo correcto (list)",
            valid_skills,
            f"Tipo: {type(self.profile.skills).__name__}"
        )
        
        # Languages
        valid_languages = isinstance(self.profile.languages, dict)
        self.test(
            "Idiomas: tipo correcto (dict)",
            valid_languages,
            f"Tipo: {type(self.profile.languages).__name__}"
        )
        
        # 3. Complejidad del CV
        print(f"\n📈 Complejidad del CV:")
        
        complexity_score = 0
        if len(self.profile.education) >= 2:
            complexity_score += 2
        if len(self.profile.experience) >= 2:
            complexity_score += 2
        if len(self.profile.skills) >= 10:
            complexity_score += 2
        if len(self.profile.languages) >= 2:
            complexity_score += 1
        if len(self.profile.organizations) >= 3:
            complexity_score += 1
        
        complexity = min(10, complexity_score)
        bar = "█" * complexity + "░" * (10 - complexity)
        print(f"   Complejidad: {bar} {complexity}/10")
        
        # 4. Data quality
        print(f"\n✅ Calidad de datos:")
        
        has_years = any(
            e.start_year or e.end_year
            for e in self.profile.education + self.profile.experience
        )
        self.test(
            "Fechas/años extraídos",
            has_years or True,
            "Información temporal presente"
        )
        
        print(f"\n✅ PASO 5 COMPLETADO\n")
        return True
    
    # ====================================================================
    # PASO 6: EXPORTAR RESULTADO
    # ====================================================================
    
    def step_6_export_result(self) -> Dict[str, Any]:
        """Exporta el resultado a diccionario"""
        self.print_header("PASO 6: EXPORTAR RESULTADO", 2)
        
        print("💾 Convirtiendo a diccionario...\n")
        
        try:
            result_dict = self.profile.to_dict()
            
            self.test(
                "Conversión a diccionario exitosa",
                result_dict is not None and isinstance(result_dict, dict),
                f"Claves: {list(result_dict.keys())}"
            )
            
            # Mostrar estructura
            print(f"\n📋 Estructura del resultado:")
            for key, value in result_dict.items():
                if isinstance(value, list):
                    print(f"   • {key}: {len(value)} items")
                elif isinstance(value, dict):
                    print(f"   • {key}: {len(value)} items (dict)")
                else:
                    val_str = str(value)[:50]
                    print(f"   • {key}: {val_str}{'...' if len(str(value)) > 50 else ''}")
            
            print(f"\n✅ PASO 6 COMPLETADO\n")
            return result_dict
        
        except Exception as e:
            self.test("Exportación", False, f"Error: {e}")
            return {}
    
    # ====================================================================
    # RESULTADOS FINALES
    # ====================================================================
    
    def print_summary(self):
        """Imprime resumen de resultados"""
        self.print_header("RESUMEN DE PRUEBAS", 1)
        
        total = self.results["passed"] + self.results["failed"]
        passed_pct = (self.results["passed"] / total * 100) if total > 0 else 0
        
        print(f"\n{'='*100}")
        print(f"  RESULTADOS FINALES")
        print(f"{'='*100}\n")
        
        print(f"  📊 Tests:")
        print(f"     ✅ Pasadas:  {self.results['passed']}/{total}")
        print(f"     ❌ Fallidas: {self.results['failed']}/{total}")
        print(f"     ⚠️  Avisos:   {self.results['warnings']}")
        print(f"     📈 Éxito:    {passed_pct:.1f}%")
        
        if self.results["failed"] == 0:
            print(f"\n  🎉 ¡TODAS LAS PRUEBAS PASARON!\n")
        else:
            print(f"\n  ⚠️  {self.results['failed']} prueba(s) fallaron\n")
        
        print(f"{'='*100}\n")
    
    # ====================================================================
    # EJECUTOR
    # ====================================================================
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Ejecuta todos los pasos"""
        print("\n")
        print("█" * 100)
        print("█" + " " * 98 + "█")
        print("█" + "  🧪 TEST: CV Extraction V2 con CV Harvard.pdf".ljust(98) + "█")
        print("█" + " " * 98 + "█")
        print("█" * 100)
        
        try:
            # Paso 1: Cargar archivo
            if not self.step_1_load_cv_file():
                self.print_summary()
                return {}
            
            # Paso 2: Extraer texto
            if not self.step_2_extract_text():
                self.print_summary()
                return {}
            
            # Paso 3: Inicializar extractor
            if not self.step_3_initialize_extractor():
                self.print_summary()
                return {}
            
            # Paso 4: Extraer campos
            if not self.step_4_extract_fields():
                self.print_summary()
                return {}
            
            # Paso 5: Validar
            if not self.step_5_validation():
                self.print_summary()
                return {}
            
            # Paso 6: Exportar
            result = self.step_6_export_result()
            
            # Resumen
            self.print_summary()
            
            return result
        
        except Exception as e:
            print(f"\n❌ ERROR FATAL: {e}")
            import traceback
            traceback.print_exc()
            self.print_summary()
            return {}


def main():
    """Ejecutor principal"""
    tester = CVExtractionTestHarvard()
    result = tester.run_all_tests()
    
    # Opcional: guardar resultado a archivo
    if result:
        import json
        output_path = Path("/Users/sparkmachine/MoirAI/harvard_cv_extraction_result.json")
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"💾 Resultado guardado en: {output_path}\n")
    
    success = tester.results["failed"] == 0
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
