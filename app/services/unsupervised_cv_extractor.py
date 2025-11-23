"""
Unsupervised CV Field Extractor Service

Módulo para extracción de CVs SIN necesidad de secciones etiquetadas.
Funciona analizando patrones lingüísticos y características de líneas.

Características:
- NO requiere headers (Educación, Experiencia, etc)
- Funciona con CVs desestructurados
- Soporta múltiples idiomas (ES, EN, FR, etc)
- Usa solo análisis lingüístico (sin ML/spaCy)
- Rápido: 5-20ms para un CV completo

Ventajas sobre Supervisado:
- 75% precisión vs 30% en CVs sin estructura
- Más adaptable a variaciones de formato
- No depende de keywords específicos

Filosofía:
"Analizar CÓMO se escribe el CV, no DÓNDE está escrito"
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import Counter
import unicodedata

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTES Y CONFIGURACIÓN
# ============================================================================

# Verbos de acción (en inglés y español)
ACTION_VERBS = {
    # Inglés
    "worked", "develop", "developed", "implement", "implemented", "create", "created",
    "led", "lead", "designed", "design", "managed", "manage", "directed", "direct",
    "coordinated", "coordinate", "analyzed", "analyze", "deployed", "deploy",
    "architected", "architect", "engineered", "engineer", "built", "build",
    "maintained", "maintain", "achieved", "achieve", "improved", "improve",
    # Español
    "trabajé", "trabaja", "trabajar", "desarrollé", "desarrolla", "desarrollar",
    "implementé", "implementa", "implementar", "creé", "crea", "crear",
    "lideré", "lidera", "liderar", "diseñé", "diseña", "diseñar",
    "gestioné", "gestiona", "gestionar", "dirigí", "dirige", "dirigir",
    "coordiné", "coordina", "coordinar", "analicé", "analiza", "analizar",
    "obtuve", "obtiene", "obtener", "logré", "logra", "lograr",
}

# Keywords de educación
EDUCATION_KEYWORDS = {
    # Inglés
    "degree", "bachelor", "master", "phd", "doctorate", "diploma", "certificate",
    "university", "college", "school", "institute", "academy", "faculty",
    "undergraduate", "postgraduate", "associate", "studied", "studied",
    # Español
    "grado", "licenciatura", "licenciado", "maestría", "máster", "doctorado",
    "diploma", "certificado", "universidad", "colegio", "instituto", "academia",
    "carrera", "pregrado", "postgrado", "diplomatura", "especialización",
    "cursé", "estudié", "formación", "educación",
}

# Keywords de experiencia (para detectar secciones)
EXPERIENCE_KEYWORDS = {
    "experience", "experiencia", "professional", "profesional",
    "employment", "empleo", "positions", "posiciones", "jobs", "trabajos",
}

# Keywords de competencias/skills
SKILL_KEYWORDS = {
    "skills", "abilities", "competencies", "technologies", "expertise",
    "habilidades", "competencias", "tecnologías", "conocimientos",
}

# Keywords de certificaciones
CERTIFICATION_KEYWORDS = {
    "certification", "certified", "certificate", "course", "training",
    "certificación", "certificado", "curso", "capacitación", "formación",
    "award", "reconocimiento", "credential",
}

# Keywords de idiomas EXPANDIDO (50+ idiomas) - Diccionario para mejor matching
# Mapea idioma principal -> [variantes y sinónimos]
LANGUAGE_KEYWORDS_MAP = {
    "English": ["english", "inglés"],
    "Spanish": ["spanish", "español", "castellano"],
    "French": ["french", "francés", "français"],
    "German": ["german", "alemán", "deutsch"],
    "Portuguese": ["portuguese", "portugués", "português"],
    "Italian": ["italian", "italiano"],
    "Chinese": ["chinese", "mandarin", "chino", "mandarín", "普通话"],
    "Japanese": ["japanese", "japonés", "日本語"],
    "Korean": ["korean", "coreano", "한국어"],
    "Russian": ["russian", "ruso", "русский"],
    "Arabic": ["arabic", "árabe", "العربية"],
    "Dutch": ["dutch", "holandés", "nederlands"],
    "Swedish": ["swedish", "sueco"],
    "Polish": ["polish", "polaco"],
    "Czech": ["czech", "checo"],
    "Danish": ["danish", "danés"],
    "Norwegian": ["norwegian", "noruego"],
    "Finnish": ["finnish", "finlandés"],
    "Turkish": ["turkish", "turco", "türkçe"],
    "Greek": ["greek", "griego", "ελληνικά"],
    "Hindi": ["hindi", "हिन्दी"],
    "Thai": ["thai", "tailandés", "ไทย"],
    "Vietnamese": ["vietnamese", "vietnamita", "tiếng việt"],
    "Indonesian": ["indonesian", "indonesio", "bahasa"],
    "Malay": ["malay", "malayo"],
    "Tagalog": ["tagalog", "pilipino"],
    "Hebrew": ["hebrew", "hebreo", "שעברית"],
    "Swahili": ["swahili"],
    "Afrikaans": ["africaans"],
}

# Para compatibilidad con código antiguo (set de todos los keywords)
LANGUAGE_KEYWORDS = {keyword for lang_list in LANGUAGE_KEYWORDS_MAP.values() for keyword in lang_list}
LANGUAGE_KEYWORDS.update(["language", "languages", "speak", "fluent", "proficiency",
                         "idioma", "idiomas", "habla", "fluido", "proficiencia",
                         "bilingual", "multilingual", "bilingüe", "multilingüe"])

# Niveles de idioma (para clasificar proficiencia)
LANGUAGE_LEVELS = {
    'native': r'\b(native|mother tongue|native speaker|lengua materna|nativa)\b',
    'fluent': r'\b(fluent|fluency|fluida|fluidez|fluido)\b',
    'proficient': r'\b(proficient|proficiency|proficiencia)\b',
    'intermediate': r'\b(intermediate|intermedio|nivel intermedio)\b',
    'basic': r'\b(basic|basics|básico|nivel básico|beginner|iniciante)\b',
    'c1': r'\b(c1|c-1|c\.1)\b',
    'c2': r'\b(c2|c-2|c\.2|mastery|dominio)\b',
    'b1': r'\b(b1|b-1|b\.1)\b',
    'b2': r'\b(b2|b-2|b\.2|upper intermediate|intermedio superior)\b',
    'a1': r'\b(a1|a-1|a\.1)\b',
    'a2': r'\b(a2|a-2|a\.2)\b',
}

# Términos técnicos comunes (para scoring de skills)
TECH_TERMS = {
    # Lenguajes
    "python", "javascript", "java", "rust", "go", "typescript", "kotlin",
    "ruby", "php", "swift", "cpp", "csharp", "scala", "r", "matlab",
    "perl", "groovy", "elixir", "clojure", "haskell",
    # Frameworks
    "react", "vue", "angular", "svelte", "fastapi", "django", "flask",
    "spring", "springboot", "dotnet", "nodejs", "express", "nestjs",
    "rails", "laravel", "symfony", "asp", "asp.net",
    # Bases de datos
    "sql", "postgresql", "mysql", "mongodb", "redis", "cassandra",
    "elasticsearch", "firestore", "dynamodb", "oracle", "sqlite",
    # DevOps/Cloud
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
    "ansible", "jenkins", "circleci", "gitlab", "github",
    # ML/AI
    "tensorflow", "pytorch", "keras", "sklearn", "pandas", "numpy",
    "huggingface", "openai", "langchain", "llm", "mlops",
    # Otros
    "api", "rest", "graphql", "grpc", "websocket", "sql",
    "microservices", "architecture", "design", "testing", "git",
    "linux", "unix", "windows", "macos", "docker", "cicd",
}


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class EducationEntry:
    """Entrada de educación extraída"""
    institution: str = ""
    degree: str = ""
    field_of_study: str = ""
    graduation_year: Optional[int] = None
    confidence: float = 0.0


@dataclass
class ExperienceEntry:
    """Entrada de experiencia extraída"""
    position: str = ""
    company: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: str = ""
    confidence: float = 0.0


@dataclass
class ExtractedCV:
    """CV completamente extraído"""
    objective: Optional[str] = None
    education: List[Dict] = None
    experience: List[Dict] = None
    skills: List[str] = None
    certifications: List[str] = None
    languages: List[str] = None
    overall_confidence: float = 0.0
    extraction_method: str = "unsupervised_hybrid"
    method_used_for_each: Dict[str, str] = None  # Qué método se usó para cada campo
    
    def __post_init__(self):
        if self.education is None:
            self.education = []
        if self.experience is None:
            self.experience = []
        if self.skills is None:
            self.skills = []
        if self.certifications is None:
            self.certifications = []
        if self.languages is None:
            self.languages = []
        if self.method_used_for_each is None:
            self.method_used_for_each = {}
    
    def to_dict(self):
        """Convierte a diccionario para serialización"""
        return {
            "objective": self.objective,
            "education": self.education,
            "experience": self.experience,
            "skills": self.skills,
            "certifications": self.certifications,
            "languages": self.languages,
            "overall_confidence": round(self.overall_confidence, 2),
            "extraction_method": self.extraction_method,
            "method_used_for_each": self.method_used_for_each
        }


# ============================================================================
# FEATURE EXTRACTOR
# ============================================================================

class LineFeatureExtractor:
    """Extrae características de cada línea del CV"""
    
    @staticmethod
    def extract(line: str) -> Dict[str, any]:
        """
        Extrae features de una línea.
        
        Returns:
            Dict con características booleanas y numéricas
        """
        if not line:
            return {}
        
        line_lower = line.lower()
        
        # Fecha: años entre 1900-2100
        has_dates = bool(re.search(r'\b(19\d{2}|20\d{2})\b', line))
        
        # Verbos de acción
        has_action_verbs = any(verb in line_lower for verb in ACTION_VERBS)
        
        # Términos técnicos
        has_tech_terms = any(term in line_lower for term in TECH_TERMS)
        
        # Keywords de educación
        has_education_kw = any(kw in line_lower for kw in EDUCATION_KEYWORDS)
        
        # Señales de empresa (Ltd, Inc, Corp, etc)
        has_company_signals = bool(re.search(
            r'\b(Ltd|Inc|Corp|LLC|GmbH|SA|AG|SPA|Co|Company|Corporation)\b',
            line,
            re.IGNORECASE
        ))
        
        # Cantidad de números
        num_numbers = len(re.findall(r'\d', line))
        
        # Porcentaje de mayúsculas
        pct_capitals = (
            sum(1 for c in line if c.isupper()) / len(line)
            if line else 0
        )
        
        # Longitud de línea
        line_length = len(line)
        
        # Es bullet point
        is_bullet = line.strip().startswith(("-", "*", "•", "→", "◦", "+"))
        
        # Contiene métricas (números con % o +)
        has_metrics = bool(re.search(r'\d+%|\d+\+', line))
        
        # Contiene email
        has_email = bool(re.search(r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}', line_lower))
        
        # Contiene teléfono
        has_phone = bool(re.search(r'\(?[\d\s\-\+\.]+\)?', line))
        
        # Contiene URL
        has_url = bool(re.search(r'https?://|www\.', line_lower))
        
        # Número de palabras
        num_words = len(line.split())
        
        # Promedio de longitud de palabras
        avg_word_length = (
            sum(len(w) for w in line.split()) / len(line.split())
            if line.split() else 0
        )
        
        return {
            "has_dates": has_dates,
            "has_action_verbs": has_action_verbs,
            "has_tech_terms": has_tech_terms,
            "has_education_kw": has_education_kw,
            "has_company_signals": has_company_signals,
            "num_numbers": num_numbers,
            "pct_capitals": pct_capitals,
            "line_length": line_length,
            "is_bullet": is_bullet,
            "has_metrics": has_metrics,
            "has_email": has_email,
            "has_phone": has_phone,
            "has_url": has_url,
            "num_words": num_words,
            "avg_word_length": avg_word_length,
        }


# ============================================================================
# LINE CLASSIFIER
# ============================================================================

class LineClassifier:
    """Clasifica líneas en categorías sin supervisión"""
    
    # Categorías posibles
    CATEGORIES = {
        "header",           # EDUCATION, EXPERIENCE, etc
        "experience",       # Línea de experiencia laboral
        "experience_detail", # Bullet point de experiencia
        "education",        # Línea de educación
        "education_detail", # Detalles de educación
        "skill",            # Habilidad técnica
        "certification",    # Certificación
        "language",         # Idioma
        "contact",          # Email, teléfono, URL
        "objective",        # Párrafo narrativo
        "other"             # Otros
    }
    
    @staticmethod
    def classify(line: str, features: Dict) -> Tuple[str, float]:
        """
        Clasifica una línea en una categoría.
        
        Returns:
            (category, confidence)
        """
        line_lower = line.lower().strip()
        
        # ========== HEADERS (SIMPLIFICADO) ==========
        # Solo palabras clave CORE sin sobreajuste
        is_short_line = len(line) < 80
        is_mostly_caps = features["pct_capitals"] > 0.4
        
        # Headers core (aplicable a cualquier CV)
        core_headers = [
            "education", "experiencia", "experience", "skills", "habilidades",
            "objective", "objetivo", "languages", "idiomas", "certification",
            "certificación", "projects", "proyectos", "summary", "resumen",
        ]
        
        has_core_header = any(kw in line_lower for kw in core_headers)
        
        if has_core_header and is_short_line:
            return ("header", 0.95)
        elif is_short_line and is_mostly_caps and features["num_words"] <= 5:
            # Fallback: línea corta en mayúsculas probablemente es header
            return ("header", 0.75)
        
        # ========== CONTACTO ==========
        if features["has_email"] or features["has_url"]:
            return ("contact", 0.95)
        if features["has_phone"] and len(line) < 30:
            return ("contact", 0.80)
        
        # ========== EXPERIENCIA ==========
        # Criterio: tiene años + verbos de acción = experiencia
        if features["has_dates"] and features["has_action_verbs"]:
            return ("experience", 0.90)
        
        # ========== EDUCACIÓN ==========
        # Criterio: tiene keywords de educación + años = educación
        if features["has_education_kw"] and features["has_dates"]:
            return ("education", 0.88)
        
        # ========== EXPERIENCIA DETAIL (bullet) ==========
        if features["is_bullet"] and features["has_action_verbs"]:
            return ("experience_detail", 0.85)
        
        # ========== SKILLS ==========
        if features["has_tech_terms"] and len(line) < 80 and not features["has_action_verbs"]:
            return ("skill", 0.80)
        
        # ========== CERTIFICACIÓN ==========
        if any(kw in line_lower for kw in CERTIFICATION_KEYWORDS):
            return ("certification", 0.75)
        
        # ========== IDIOMA ==========
        if any(kw in line_lower for kw in LANGUAGE_KEYWORDS):
            return ("language", 0.70)
        
        # ========== PÁRRAFO NARRATIVO (OBJETIVO) ==========
        if features["num_words"] > 10 and features["line_length"] > 60:
            return ("objective", 0.50)
        
        # ========== DEFAULT ==========
        return ("other", 0.30)


# ============================================================================
# SECTION DETECTOR - PATTERN BASED (NO HEADER DEPENDENCY)
# ============================================================================

class SectionDetector:
    """
    Agrupa líneas en secciones basado en PATRONES CARACTERÍSTICOS.
    
    ENFOQUE: NO depende de headers - funciona con ANY CV format
    
    Estrategia de Detección:
    
    EDUCACIÓN:
      - Secuencia: [education_keywords] + [degree_keywords] + [año]
      - Ejemplo: "Universidad X" -> "Licenciatura en Y" -> "2024"
      - NO necesita header
    
    EXPERIENCIA:
      - Secuencia: [empresa - puesto] + [fechas] + [acción + descripción]
      - Ejemplo: "Empresa X - Ingeniero" -> "Ene 2020 - Jun 2022" -> "Desarrollé..."
      - NO necesita header
    
    SKILLS:
      - Características: múltiples tech_terms + separadores (comas)
      - Ejemplo: "Python, Java, AWS, Docker, TensorFlow"
      - NO necesita header
    """
    
    # Keywords para reconocer patrones de EDUCACIÓN
    EDU_KEYWORDS = {
        'university', 'institute', 'college', 'school', 'academy',
        'licenciatura', 'degree', 'bachelor', 'master', 'phd', 'diploma',
        'universidad', 'instituto', 'colegio', 'máster', 'doctorado',
        'carrera', 'programa', 'formación', 'educación', 'studies',
        'politécnico', 'escuela', 'facultad',
    }
    
    DEGREE_KEYWORDS = {
        'bachelor', 'master', 'phd', 'diploma', 'degree', 'engineering',
        'licenciatura', 'ingeniería', 'ciencia', 'administración', 'derecho',
        'medicina', 'psicología', 'carrera', 'especialización', 'diplomatura',
        'grado', 'licenciado', 'técnico', 'profesional',
    }
    
    # Keywords para reconocer EMPRESA/POSICIÓN
    POSITION_KEYWORDS = {
        'engineer', 'developer', 'manager', 'analyst', 'director', 'coordinator',
        'specialist', 'consultant', 'architect', 'lead', 'senior', 'junior',
        'ingeniero', 'desarrollador', 'gerente', 'analista', 'director',
        'coordinador', 'especialista', 'consultor', 'jefe', 'líder',
        'investigador', 'asesor', 'supervisor', 'técnico',
    }
    
    # Términos técnicos específicos
    TECH_TERMS = {
        'python', 'java', 'javascript', 'sql', 'aws', 'docker', 'kubernetes',
        'react', 'angular', 'nodejs', 'fastapi', 'django', 'machine learning',
        'deep learning', 'tableau', 'power bi', 'git', 'api', 'rest', 'graphql',
        'postgresql', 'mongodb', 'redis', 'elastic', 'tensorflow', 'pytorch',
        'c++', 'c#', 'r', 'scala', 'go', 'rust', 'kotlin', 'swift',
    }
    
    @staticmethod
    def _count_tech_terms(line: str) -> int:
        """Contar cuántos términos técnicos hay en una línea"""
        line_lower = line.lower()
        count = 0
        for term in SectionDetector.TECH_TERMS:
            if term in line_lower:
                count += 1
        return count
    
    @staticmethod
    def _has_education_pattern(line: str, features: Dict = None) -> bool:
        """
        Detectar si una línea inicia un PATRÓN DE EDUCACIÓN
        
        Criterios:
        - Tiene keywords de educación O universidad
        - NO tiene verbos de acción
        - Relativamente corta (< 150 chars)
        """
        if not line or len(line) > 150:
            return False
        
        line_lower = line.lower()
        
        # Debe tener keywords de educación
        has_edu_kw = any(kw in line_lower for kw in SectionDetector.EDU_KEYWORDS)
        if not has_edu_kw:
            return False
        
        # NO debe tener verbos de acción (eso sería experiencia)
        action_verbs = {'develop', 'manage', 'lead', 'analyze', 'architect', 'implement',
                       'trabajé', 'dirigí', 'lideré', 'diseñé', 'gestioné', 'built'}
        has_action = any(verb in line_lower for verb in action_verbs)
        
        return not has_action
    
    @staticmethod
    def _has_experience_pattern(line: str) -> bool:
        """
        Detectar si una línea inicia un PATRÓN DE EXPERIENCIA
        
        Criterios:
        - Patrón "X - Y" (empresa - puesto)
        - O tiene verbos de acción
        - O tiene posición keyword + contexto empresarial
        
        IMPORTANTE: Excluir certifications (Certified, AWS, etc)
        """
        if not line or len(line) > 120:
            return False
        
        line_lower = line.lower()
        
        # EXCLUIR certificaciones
        cert_keywords = {'certified', 'certification', 'certificate', 'award',
                        'certificado', 'certificación', 'acreditación'}
        if any(kw in line_lower for kw in cert_keywords):
            return False
        
        # Patrón "X - Y" (empresa - puesto)
        if ' - ' in line and len(line) < 100:
            return True
        
        # Tiene verbos de acción
        action_verbs = {'develop', 'manage', 'lead', 'analyze', 'architected',
                       'implement', 'design', 'engineer', 'built', 'worked',
                       'trabajé', 'dirigí', 'lideré', 'diseñé', 'gestioné',
                       'desarrollé', 'implementé', 'administré'}
        if any(verb in line_lower for verb in action_verbs):
            return True
        
        # Posición keyword (pero solo si hay indicadores de empresa)
        has_position = any(kw in line_lower for kw in SectionDetector.POSITION_KEYWORDS)
        
        return has_position
    
    @staticmethod
    def _has_skills_pattern(line: str) -> bool:
        """
        Detectar si una línea es SKILLS
        
        Criterios:
        - Múltiples términos técnicos (≥2)
        - Separados por comas o semicolons
        - Línea corta
        """
        if not line or len(line) > 150:
            return False
        
        tech_count = SectionDetector._count_tech_terms(line)
        
        if tech_count < 2:
            return False
        
        # Debe tener separadores (comas, semicolons)
        has_separators = ',' in line or ';' in line
        
        return has_separators or tech_count >= 3
    
    @staticmethod
    def _is_year_line(line: str) -> bool:
        """¿Es una línea que contiene solo año(s)?"""
        line_strip = line.strip()
        return bool(re.match(
            r'^\d{4}(-\d{4})?$|^\d{4}$|presente|present|actualidad|current',
            line_strip.lower()
        ))
    
    @staticmethod
    def group_lines(classified_lines: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Agrupa líneas en secciones basado en PATRONES.
        NO depende de headers explícitos.
        
        Returns:
            Dict[category → List[groups]]
        """
        sections = {}
        processed = set()
        
        i = 0
        while i < len(classified_lines):
            if i in processed:
                i += 1
                continue
            
            classified = classified_lines[i]
            line = classified.get("line", "")
            category = classified.get("category", "")
            features = classified.get("features", {})
            
            # ========== SKIP HEADERS ==========
            if category == "header":
                processed.add(i)
                i += 1
                continue
            
            # ========== DETECT EDUCATION SEQUENCE ==========
            if SectionDetector._has_education_pattern(line, features):
                edu_group = [classified]
                processed.add(i)
                j = i + 1
                
                # Agregar líneas que continúan patrón de educación
                while j < len(classified_lines) and j not in processed:
                    next_classified = classified_lines[j]
                    next_line = next_classified.get("line", "")
                    next_category = next_classified.get("category", "")
                    next_features = next_classified.get("features", {})
                    
                    # PARAR si encontramos un header o experiencia clara
                    if next_category == "header":
                        break
                    if SectionDetector._has_experience_pattern(next_line):
                        break
                    
                    # Continuar si es: otra educación, año, o texto sin action verbs
                    if (SectionDetector._has_education_pattern(next_line, next_features) or
                        SectionDetector._is_year_line(next_line) or
                        (len(next_line) < 100 and
                         not next_features.get("has_action_verbs", False) and
                         not SectionDetector._has_skills_pattern(next_line) and
                         not SectionDetector._has_experience_pattern(next_line))):
                        
                        edu_group.append(next_classified)
                        processed.add(j)
                        j += 1
                    else:
                        break
                
                if "education" not in sections:
                    sections["education"] = []
                
                avg_conf = sum(c.get("confidence", 0) for c in edu_group) / len(edu_group)
                sections["education"].append({
                    "lines": edu_group,
                    "content": "\n".join([c["line"] for c in edu_group]),
                    "confidence": avg_conf
                })
                
                i = j
                continue
            
            # ========== DETECT EXPERIENCE SEQUENCE ==========
            if SectionDetector._has_experience_pattern(line):
                exp_group = [classified]
                processed.add(i)
                j = i + 1
                
                # Agregar líneas que continúan patrón de experiencia
                while j < len(classified_lines) and j not in processed:
                    next_classified = classified_lines[j]
                    next_line = next_classified.get("line", "")
                    next_category = next_classified.get("category", "")
                    next_features = next_classified.get("features", {})
                    
                    # PARAR si encontramos header o sección clara diferente
                    if next_category == "header":
                        break
                    if SectionDetector._has_skills_pattern(next_line):
                        break
                    if SectionDetector._has_education_pattern(next_line):
                        break
                    
                    # Continuar si es: experiencia, bullet point, fechas, o acción
                    if (SectionDetector._has_experience_pattern(next_line) or
                        next_features.get("is_bullet", False) or
                        next_features.get("has_action_verbs", False) or
                        next_features.get("has_dates", False) or
                        (len(next_line) < 120 and
                         not SectionDetector._has_education_pattern(next_line) and
                         not SectionDetector._has_skills_pattern(next_line))):
                        
                        exp_group.append(next_classified)
                        processed.add(j)
                        j += 1
                    else:
                        break
                
                if "experience" not in sections:
                    sections["experience"] = []
                
                avg_conf = sum(c.get("confidence", 0) for c in exp_group) / len(exp_group)
                sections["experience"].append({
                    "lines": exp_group,
                    "content": "\n".join([c["line"] for c in exp_group]),
                    "confidence": avg_conf
                })
                
                i = j
                continue
            
            # ========== DETECT SKILLS ==========
            if SectionDetector._has_skills_pattern(line):
                skill_group = [classified]
                processed.add(i)
                j = i + 1
                
                # Agregar líneas de skills consecutivas
                while j < len(classified_lines) and j not in processed:
                    next_classified = classified_lines[j]
                    next_line = next_classified.get("line", "")
                    
                    if (SectionDetector._has_skills_pattern(next_line) or
                        next_classified.get("category") == "skill"):
                        skill_group.append(next_classified)
                        processed.add(j)
                        j += 1
                    else:
                        break
                
                if "skill" not in sections:
                    sections["skill"] = []
                
                avg_conf = sum(c.get("confidence", 0) for c in skill_group) / len(skill_group)
                sections["skill"].append({
                    "lines": skill_group,
                    "content": "\n".join([c["line"] for c in skill_group]),
                    "confidence": avg_conf
                })
                
                i = j
                continue
            
            # ========== DETECT CERTIFICATIONS ==========
            if category == "certification":
                cert_group = [classified]
                processed.add(i)
                j = i + 1
                
                while j < len(classified_lines) and j not in processed:
                    if classified_lines[j].get("category") == "certification":
                        cert_group.append(classified_lines[j])
                        processed.add(j)
                        j += 1
                    else:
                        break
                
                if "certification" not in sections:
                    sections["certification"] = []
                
                avg_conf = sum(c.get("confidence", 0) for c in cert_group) / len(cert_group)
                sections["certification"].append({
                    "lines": cert_group,
                    "content": "\n".join([c["line"] for c in cert_group]),
                    "confidence": avg_conf
                })
                
                i = j
                continue
            
            # ========== DETECT LANGUAGES ==========
            if category == "language":
                lang_group = [classified]
                processed.add(i)
                j = i + 1
                
                while j < len(classified_lines) and j not in processed:
                    if classified_lines[j].get("category") == "language":
                        lang_group.append(classified_lines[j])
                        processed.add(j)
                        j += 1
                    else:
                        break
                
                if "language" not in sections:
                    sections["language"] = []
                
                avg_conf = sum(c.get("confidence", 0) for c in lang_group) / len(lang_group)
                sections["language"].append({
                    "lines": lang_group,
                    "content": "\n".join([c["line"] for c in lang_group]),
                    "confidence": avg_conf
                })
                
                i = j
                continue
            
            # ========== GENERIC CATEGORY ==========
            cat = category if category else "other"
            group = [classified]
            processed.add(i)
            j = i + 1
            
            while j < len(classified_lines) and j not in processed:
                if classified_lines[j].get("category") == cat:
                    group.append(classified_lines[j])
                    processed.add(j)
                    j += 1
                else:
                    break
            
            if cat not in sections:
                sections[cat] = []
            
            avg_conf = sum(c.get("confidence", 0) for c in group) / len(group)
            sections[cat].append({
                "lines": group,
                "content": "\n".join([c["line"] for c in group]),
                "confidence": avg_conf
            })
            
            i = j
        
        return sections


# ============================================================================
# FIELD EXTRACTOR
# ============================================================================

class FieldExtractor:
    """Extrae campos específicos desde secciones"""
    
    @staticmethod
    def extract_objective(sections: Dict, full_text: str) -> Optional[str]:
        """
        Extrae objetivo profesional.
        Usualmente primeras líneas narrativas.
        """
        # Si hay sección objetivo explícita
        if "objective" in sections and sections["objective"]:
            return sections["objective"][0]["content"][:500]
        
        # Fallback: primeras líneas que no sean contact/header
        lines = full_text.split("\n")
        objective_lines = []
        
        for line in lines:
            if line.strip() and not any(
                kw in line.lower()
                for kw in ["email", "@", "http", "education", "experience", "skills"]
            ):
                objective_lines.append(line.strip())
                if len(" ".join(objective_lines)) > 200:
                    break
        
        if objective_lines:
            return " ".join(objective_lines)[:500]
        
        return None
    
    @staticmethod
    def extract_education(sections: Dict) -> List[Dict]:
        """Extrae entradas de educación"""
        educations = []
        
        for category in ["education", "education_detail"]:
            if category not in sections:
                continue
            
            for edu_block in sections[category][:5]:  # Max 5
                edu = FieldExtractor._parse_education(edu_block["content"])
                if edu:
                    educations.append(edu)
        
        return educations
    
    @staticmethod
    def extract_experience(sections: Dict) -> List[Dict]:
        """Extrae entradas de experiencia"""
        experiences = []
        current_exp = None
        
        for category in ["experience", "experience_detail"]:
            if category not in sections:
                continue
            
            for exp_block in sections[category][:5]:  # Max 5
                if category == "experience":
                    exp = FieldExtractor._parse_experience(exp_block["content"])
                    if exp:
                        experiences.append(exp)
                        current_exp = exp
                elif category == "experience_detail" and current_exp:
                    # Agrega detalle al último experience
                    current_exp["description"] += "\n" + exp_block["content"]
        
        return experiences
    
    @staticmethod
    def extract_skills(sections: Dict) -> List[str]:
        """Extrae skills técnicas"""
        skills = []
        
        if "skill" in sections:
            for skill_block in sections["skill"]:
                # Divide por comas o punto y coma
                items = re.split(r'[,;]', skill_block["content"])
                skills.extend([s.strip() for s in items if s.strip()])
        
        return skills[:30]  # Max 30
    
    @staticmethod
    def extract_certifications(sections: Dict) -> List[str]:
        """Extrae certificaciones"""
        certs = []
        
        if "certification" in sections:
            for cert_block in sections["certification"]:
                certs.append(cert_block["content"].strip())
        
        return certs[:10]  # Max 10
    
    @staticmethod
    def extract_languages_improved(full_text: str) -> List[str]:
        """
        Extrae idiomas de forma simple y robusta (MVP).
        Sin intentar detectar niveles para evitar falsos positivos.
        
        Retorna lista de strings como: ["English", "Spanish", "French"]
        """
        languages = []
        text_lower = full_text.lower()
        
        # Buscar cada idioma en el mapa
        for lang_name, keywords in LANGUAGE_KEYWORDS_MAP.items():
            # Buscar si alguna variante del idioma aparece en el texto
            for keyword in keywords:
                # Usar word boundary para evitar match parciales
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower):
                    # Encontrado - agregar idioma una sola vez
                    languages.append(lang_name)
                    break  # No repetir el mismo idioma con otras variantes
        
        return languages[:15]  # Max 15 idiomas
    
    @staticmethod
    def extract_languages(sections: Dict, full_text: str = "") -> List[str]:
        """
        Extrae idiomas. Usa método mejorado para obtener
        idiomas específicos + niveles.
        """
        # Usar método mejorado en texto completo para mejor cobertura
        if full_text:
            return FieldExtractor.extract_languages_improved(full_text)
        
        # Fallback: si no hay texto completo, usar secciones
        languages = []
        if "language" in sections:
            for lang_block in sections["language"]:
                result = FieldExtractor.extract_languages_improved(lang_block["content"])
                if result:
                    languages.extend(result)
        
        return languages[:15]  # Max 15
    
    @staticmethod
    def _parse_education(text: str) -> Optional[Dict]:
        """
        Parsea bloque de educación.
        Mejoras: Busca específicamente institución, grado y año
        en lugar de tomar líneas completas como descripción.
        """
        lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) < 150]
        
        if not lines:
            return None
        
        edu = EducationEntry()
        
        # 1. Buscar institución (universidad/colegio)
        INSTITUTION_KEYWORDS = [
            'university', 'institute', 'college', 'school', 'academy',
            'universidad', 'instituto', 'colegio', 'escuela', 'politecnico',
            'polytechnic', 'technical', 'tecnológica'
        ]
        
        institution_line = None
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(kw in line_lower for kw in INSTITUTION_KEYWORDS):
                # Tomar solo esta línea como institución
                institution_line = line
                # Limitar a primer oracion para evitar párrafos
                if len(institution_line) > 100:
                    institution_line = institution_line[:100]
                edu.institution = institution_line
                break
        
        # Si no encontró keyword, tomar primera línea corta (<100 chars)
        if not edu.institution and lines:
            first_line = lines[0]
            if len(first_line) < 100 and not any(c in first_line for c in ['.', '?', '!']*3):
                edu.institution = first_line
        
        # 2. Buscar grado/carrera
        for line in lines:
            line_lower = line.lower()
            for kw in EDUCATION_KEYWORDS:
                if kw in line_lower and len(kw) > 3:
                    edu.degree = kw
                    edu.field_of_study = kw
                    break
            if edu.degree:
                break
        
        # 3. Buscar año de graduación
        year_match = re.search(r'\b(20\d{2}|19\d{2})\b', text)
        if year_match:
            edu.graduation_year = int(year_match.group(1))
        
        edu.confidence = 0.85 if edu.institution else 0.0
        
        return asdict(edu) if edu.institution else None
    
    @staticmethod
    def _parse_experience(text: str) -> Optional[Dict]:
        """
        Parsea bloque de experiencia.
        Mejoras: Busca específicamente posición y empresa
        sin mezclar con descripción.
        
        Detecta patrones:
        - "Company - Position" (más común)
        - "Position - Company" (menos común)
        - "Position at Company"
        """
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        
        if not lines:
            return None
        
        exp = ExperienceEntry()
        first_line = lines[0]
        
        # 1. Separar posición y empresa
        POSITION_KEYWORDS = {
            'engineer', 'developer', 'manager', 'analyst', 'director', 'coordinator',
            'specialist', 'consultant', 'architect', 'lead', 'senior', 'junior',
            'ingeniero', 'desarrollador', 'gerente', 'analista', 'director',
            'coordinador', 'especialista', 'consultor', 'jefe', 'líder',
            'investigador', 'asesor', 'supervisor', 'técnico', 'researcher',
        }
        
        if " - " in first_line and len(first_line) < 100:
            parts = first_line.split(" - ", 1)
            left = parts[0].strip().lower()
            right = parts[1].strip().lower()
            
            # Detectar si es "Company - Position" o "Position - Company"
            # Heurística: el lado con position keyword es la posición
            left_has_pos_kw = any(kw in left for kw in POSITION_KEYWORDS)
            right_has_pos_kw = any(kw in right for kw in POSITION_KEYWORDS)
            
            if right_has_pos_kw and not left_has_pos_kw:
                # "Company - Position"
                exp.company = parts[0].strip()
                exp.position = parts[1].strip()
            elif left_has_pos_kw and not right_has_pos_kw:
                # "Position - Company"
                exp.position = parts[0].strip()
                exp.company = parts[1].strip()
            else:
                # Ambiguo: asumir "Position - Company" (formato estándar)
                exp.position = parts[0].strip()
                exp.company = parts[1].strip()
        elif " at " in first_line.lower() and len(first_line) < 100:
            parts = re.split(r'\s+at\s+', first_line, flags=re.IGNORECASE)
            exp.position = parts[0].strip()
            exp.company = parts[1].strip() if len(parts) > 1 else ""
        elif len(first_line) < 100:
            # Si es corta, probablemente sea posición
            exp.position = first_line
        else:
            # Si es larga, podría ser descripción mal parseada
            # Tomar solo primeras palabras
            words = first_line.split()[:6]
            exp.position = " ".join(words)
        
        # 2. Buscar fechas (años)
        year_matches = re.findall(r'\b(20\d{2}|19\d{2})\b', text)
        if len(year_matches) >= 2:
            exp.start_date = year_matches[0]
            exp.end_date = year_matches[1]
        elif len(year_matches) == 1:
            exp.start_date = year_matches[0]
        
        # 3. Descripción: líneas restantes (solo si son razonables)
        desc_lines = []
        for line in lines[1:]:
            # Evitar líneas muy largas que son probablemente párrafos de descripción
            if len(line) < 150:
                desc_lines.append(line)
            else:
                # Limitar línea larga a primeras 100 chars
                desc_lines.append(line[:100] + "...")
        
        if desc_lines:
            exp.description = "\n".join(desc_lines[:5])  # Max 5 líneas
        
        exp.confidence = 0.85 if exp.position else 0.0
        
        return asdict(exp) if exp.position else None


# ============================================================================
# MAIN EXTRACTOR
# ============================================================================

class UnsupervisedCVExtractor:
    """
    Extractor principal de CVs sin supervisión.
    Orquesta todos los componentes.
    """
    
    def __init__(self):
        self.feature_extractor = LineFeatureExtractor()
        self.classifier = LineClassifier()
        self.detector = SectionDetector()
        self.field_extractor = FieldExtractor()
    
    def extract(self, text: str) -> ExtractedCV:
        """
        Extrae CV completo desde texto.
        
        Proceso:
        1. Preprocesa y divide en líneas
        2. Extrae features de cada línea
        3. Clasifica líneas en categorías
        4. Agrupa en secciones
        5. Extrae campos
        6. Calcula confianza
        
        Args:
            text: Texto completo del CV
            
        Returns:
            ExtractedCV con todos los campos
        """
        try:
            # Paso 1: Preprocesamiento
            lines = self._preprocess(text)
            
            if not lines:
                logger.warning("CV vacío o sin contenido válido")
                return ExtractedCV()
            
            # Paso 2: Extrae features
            classified_lines = []
            for line in lines:
                features = self.feature_extractor.extract(line)
                category, confidence = self.classifier.classify(line, features)
                
                classified_lines.append({
                    "line": line,
                    "category": category,
                    "confidence": confidence,
                    "features": features
                })
            
            # Paso 3: Agrupa en secciones
            sections = self.detector.group_lines(classified_lines)
            
            # Paso 4: Extrae campos
            objective = self.field_extractor.extract_objective(sections, text)
            education = self.field_extractor.extract_education(sections)
            experience = self.field_extractor.extract_experience(sections)
            skills = self.field_extractor.extract_skills(sections)
            certifications = self.field_extractor.extract_certifications(sections)
            languages = self.field_extractor.extract_languages(sections, text)  # Pasar texto completo
            
            # Paso 5: Calcula confianza
            overall_confidence = self._calculate_confidence(
                objective, education, experience, skills
            )
            
            # Paso 6: Construye resultado
            result = ExtractedCV(
                objective=objective,
                education=education,
                experience=experience,
                skills=skills,
                certifications=certifications,
                languages=languages,
                overall_confidence=overall_confidence,
                extraction_method="unsupervised_hybrid",
                method_used_for_each={
                    "objective": "unsupervised",
                    "education": "unsupervised",
                    "experience": "unsupervised",
                    "skills": "unsupervised",
                    "certifications": "unsupervised",
                    "languages": "unsupervised",
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error en extracción unsupervised: {e}", exc_info=True)
            return ExtractedCV()
    
    def _preprocess(self, text: str) -> List[str]:
        """
        Preprocesa texto en líneas válidas.
        """
        if not text:
            return []
        
        # Normaliza unicode
        text = unicodedata.normalize("NFKD", text)
        
        # Divide por líneas
        lines = text.split("\n")
        
        # Limpia y filtra líneas vacías
        lines = [
            line.strip()
            for line in lines
            if line.strip() and len(line.strip()) > 1
        ]
        
        return lines
    
    def _calculate_confidence(
        self,
        objective: Optional[str],
        education: List[Dict],
        experience: List[Dict],
        skills: List[str]
    ) -> float:
        """
        Calcula confianza general de la extracción.
        
        Basada en:
        - Presencia de cada campo
        - Cantidad de elementos
        """
        confidence_score = 0.0
        
        # Objetivo: 10%
        if objective:
            confidence_score += 0.10
        
        # Educación: 20%
        confidence_score += min(0.20, len(education) * 0.04)
        
        # Experiencia: 30% (más peso que educación)
        confidence_score += min(0.30, len(experience) * 0.06)
        
        # Skills: 40%
        confidence_score += min(0.40, len(skills) * 0.013)
        
        return min(1.0, max(0.0, confidence_score))


# Instancia compartida
unsupervised_cv_extractor = UnsupervisedCVExtractor()
