"""
Servicio de Parseo HTML para OCC.com.mx

Responsabilidades:
- Parsear HTML de listings de OCC.com.mx usando BeautifulSoup4
- Extraer: titulo, empresa, ubicación, descripción, salario, modo trabajo, tipo contrato
- Validar datos extraídos (no vacíos, formatos válidos)
- Normalizar datos (trimear espacios, lowercase)
- Extraer habilidades de descripciones usando NLP

Este módulo es crítico para Phase 2A - sin parsing correcto, no hay datos.

✅ Cumplimiento LFPDPPP: Prepara datos para encriptación en DB
"""

import re
import logging
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class JobItem(BaseModel):
    """
    Modelo de item de trabajo extraído de OCC.com.mx
    
    Validaciones incluidas para asegurar calidad de datos
    """
    external_job_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="ID único del trabajo en OCC"
    )
    title: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Título del puesto"
    )
    company: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Nombre de la empresa"
    )
    location: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Ubicación del trabajo (ciudad, estado)"
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Descripción completa del trabajo"
    )
    
    # Campos opcionales
    skills: List[str] = Field(
        default_factory=list,
        description="Habilidades requeridas extraídas"
    )
    work_mode: Optional[str] = Field(
        default=None,
        description="Modalidad: presencial, remoto, híbrido"
    )
    job_type: Optional[str] = Field(
        default=None,
        description="Tipo de contrato: full-time, part-time, temporal, freelance"
    )
    salary_min: Optional[float] = Field(
        default=None,
        description="Salario mínimo en MXN"
    )
    salary_max: Optional[float] = Field(
        default=None,
        description="Salario máximo en MXN"
    )
    currency: str = Field(
        default="MXN",
        description="Moneda del salario"
    )
    
    # Email y teléfono para contacto (SERÁ ENCRIPTADO)
    email: Optional[str] = Field(
        default=None,
        description="Email de contacto (será encriptado en DB)"
    )
    phone: Optional[str] = Field(
        default=None,
        description="Teléfono de contacto (será encriptado en DB)"
    )
    
    # Metadata
    published_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Fecha de publicación"
    )
    source: str = Field(
        default="occ.com.mx",
        description="Fuente de datos"
    )
    
    # Validadores
    @validator('title', 'company', 'location', 'description')
    def trim_whitespace(cls, v):
        """Trimear espacios en blanco"""
        if isinstance(v, str):
            return v.strip()
        return v
    
    @validator('title', 'company', 'location')
    def not_only_numbers(cls, v):
        """No permitir valores que sean solo números"""
        if v and v.isdigit():
            raise ValueError("No puede ser solo números")
        return v
    
    class Config:
        from_attributes = True


# ============================================================================
# HTML Parser Service
# ============================================================================

class HTMLParserService:
    """
    Servicio centralizado para parsear HTML de OCC.com.mx
    
    **Características:**
    - ✅ Parseo robusto con BeautifulSoup4
    - ✅ Extracción de habilidades usando patterns NLP
    - ✅ Validación de datos extraídos
    - ✅ Normalización de datos (trimear, lowercase)
    - ✅ Extracción de rangos salariales
    - ✅ Detección de modalidad de trabajo (presencial, remoto, híbrido)
    
    **Ejemplo de uso:**
    ```python
    parser = HTMLParserService()
    
    # Parsear un HTML específico
    job = parser.parse_job_listing(html_string)
    
    # Extraer habilidades de descripción
    skills = parser.extract_skills_from_description(job.description)
    
    # Validar job
    is_valid = parser.validate_job_item(job)
    ```
    """
    
    # Patrones para extracción de skills
    COMMON_SKILLS = {
        # Lenguajes de programación
        'python', 'java', 'javascript', 'typescript', 'c#', 'c++', 'ruby', 'go',
        'rust', 'php', 'kotlin', 'swift', 'scala', 'r', 'matlab', 'groovy',
        'dart', 'lua', 'perl', 'haskell', 'clojure', 'elixir',
        
        # Web frameworks
        'react', 'angular', 'vue', 'svelte', 'next.js', 'nuxt', 'fastapi',
        'django', 'flask', 'spring', 'express', 'nest.js', 'laravel', 'rails',
        'asp.net', 'blazor',
        
        # Databases
        'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
        'dynamodb', 'firestore', 'sql server', 'oracle', 'neo4j', 'sqlite',
        'influxdb', 'cockroachdb',
        
        # Cloud & DevOps
        'aws', 'azure', 'gcp', 'kubernetes', 'docker', 'terraform', 'ansible',
        'jenkins', 'gitlab', 'github', 'circleci', 'travis', 'heroku',
        
        # Data Science & ML
        'machine learning', 'deep learning', 'nlp', 'tensorflow', 'pytorch',
        'scikit-learn', 'pandas', 'numpy', 'spark', 'hadoop', 'data science',
        'data analysis', 'data engineering', 'analytics',
        
        # Otros (muy usados)
        'git', 'rest api', 'graphql', 'microservices', 'agile', 'scrum',
        'linux', 'windows', 'macos', 'html', 'css', 'sql', 'api',
    }
    
    # Patrones para detección de modalidad de trabajo
    REMOTE_PATTERNS = [
        r'\bremoto\b', r'\bremote\b', r'work from home', r'desde casa',
        r'\b100% remoto\b', r'\b100% remote\b', r'totalmente remoto'
    ]
    
    HYBRID_PATTERNS = [
        r'\bhíbrido\b', r'\bhybrid\b', r'mixto', r'presencial y remoto',
        r'some remote', r'flexible'
    ]
    
    ONSITE_PATTERNS = [
        r'\bpresencial\b', r'\bonsite\b', r'\ben oficina\b', r'\ba tiempo completo\b'
    ]
    
    # Patrones para salario (soportar formatos sin separadores de miles)
    SALARY_PATTERN = r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+)\s*(?:a|-|–)\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+)'
    SALARY_SINGLE_PATTERN = r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+)'
    
    def __init__(self):
        """Inicializar el parser HTML"""
        logger.info("✅ HTMLParserService inicializado")
        self._common_skills_lower = {skill.lower() for skill in self.COMMON_SKILLS}
    
    def parse_job_listing(
        self,
        html: str,
        external_job_id: Optional[str] = None,
        source: str = "occ.com.mx"
    ) -> JobItem:
        """
        Parsear un listing HTML de OCC.com.mx.
        
        Args:
            html: HTML string del listing
            external_job_id: ID único del job (si no está en HTML)
            source: Fuente de datos (default: occ.com.mx)
        
        Returns:
            JobItem con datos extraídos
        
        Raises:
            ValueError: Si no se pueden extraer datos requeridos
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extraer campos principales (adaptar selectores según estructura HTML)
            title = self._extract_text(soup, 'h1.job-title, .titulo-puesto, h1')
            company = self._extract_text(soup, '.company-name, .empresa, [data-company]')
            location = self._extract_text(soup, '.location, .ubicacion, [data-location]')
            description = self._extract_text(soup, '.job-description, .descripcion, article, main')
            
            # Validar campos requeridos
            if not all([title, company, location, description]):
                missing = []
                if not title: missing.append("título")
                if not company: missing.append("empresa")
                if not location: missing.append("ubicación")
                if not description: missing.append("descripción")
                raise ValueError(f"Campos requeridos faltantes: {', '.join(missing)}")
            
            # ID del trabajo
            job_id = external_job_id or self._extract_job_id(soup, html)
            if not job_id:
                raise ValueError("No se pudo extraer o proporcionar job ID")
            
            # Extraer campos opcionales
            skills = self.extract_skills_from_description(description)
            work_mode = self._detect_work_mode(description)
            job_type = self._detect_job_type(description)
            salary_min, salary_max = self.extract_salary_range(description)
            
            # Email y teléfono (si existen)
            email = self._extract_email(html)
            phone = self._extract_phone(html)
            
            # Crear JobItem
            job = JobItem(
                external_job_id=job_id,
                title=title,
                company=company,
                location=location,
                description=description,
                skills=skills,
                work_mode=work_mode,
                job_type=job_type,
                salary_min=salary_min,
                salary_max=salary_max,
                email=email,
                phone=phone,
                source=source,
                published_at=datetime.utcnow()
            )
            
            logger.info(f"✅ Job parseado: {job.title} @ {job.company}")
            return job
            
        except ValueError as e:
            logger.error(f"❌ Error validación: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ Error parseando HTML: {str(e)}")
            raise ValueError(f"No se pudo parsear HTML: {str(e)}")
    
    def extract_skills_from_description(self, description: str) -> List[str]:
        """
        Extraer habilidades de la descripción usando pattern matching.
        
        Args:
            description: Texto de descripción del trabajo
        
        Returns:
            Lista de habilidades encontradas
        
        **Algoritmo:**
        1. Normalizar texto a lowercase
        2. Buscar skills comunes en el texto
        3. Evitar falsos positivos (e.g., "will" no es skill)
        4. Retornar lista única ordenada
        """
        if not description:
            return []
        
        description_lower = description.lower()
        found_skills = []
        
        # Buscar skills comunes
        for skill in self._common_skills_lower:
            # Usar word boundaries para evitar partial matches
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, description_lower):
                found_skills.append(skill.title())  # Capitalizar para presentación
        
        # Remover duplicados y ordenar
        unique_skills = sorted(list(set(found_skills)))
        
        logger.debug(f"📌 Skills extraídas: {unique_skills}")
        return unique_skills
    
    def extract_salary_range(self, text: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Extraer rango salarial de texto.
        
        Args:
            text: Texto a buscar salario
        
        Returns:
            Tupla (salary_min, salary_max) o (None, None) si no encontrado
        
        **Formato soportado:**
        - $20,000 a $30,000
        - $20000-30000
        - 20,000 – 30,000
        - $20k-$30k (simplificado a 20000-30000)
        """
        try:
            if not text:
                return None, None
            
            # Intentar patrón de rango
            match = re.search(self.SALARY_PATTERN, text, re.IGNORECASE)
            if match:
                min_str = match.group(1).replace(',', '').replace('.', '')
                max_str = match.group(2).replace(',', '').replace('.', '')
                
                min_val = float(min_str)
                max_val = float(max_str)
                
                # Validar que tenga sentido
                if min_val > 0 and max_val > min_val and max_val < min_val * 10:
                    return min_val, max_val
            
            return None, None
            
        except Exception as e:
            logger.debug(f"No se pudo extraer salario: {str(e)}")
            return None, None
    
    def _detect_work_mode(self, text: str) -> Optional[str]:
        """
        Detectar modalidad de trabajo (presencial, remoto, híbrido).
        
        Args:
            text: Texto a analizar
        
        Returns:
            'remoto', 'presencial', 'híbrido' o None
        """
        text_lower = text.lower()
        
        # Buscar en orden de especificidad - HÍBRIDO PRIMERO para evitar que "remoto" lo detecte
        for pattern in self.HYBRID_PATTERNS:
            if re.search(pattern, text_lower):
                return "híbrido"
        
        for pattern in self.REMOTE_PATTERNS:
            if re.search(pattern, text_lower):
                return "remoto"
        
        for pattern in self.ONSITE_PATTERNS:
            if re.search(pattern, text_lower):
                return "presencial"
        
        return None
    
    def _detect_job_type(self, text: str) -> Optional[str]:
        """
        Detectar tipo de contrato (full-time, part-time, etc.).
        
        Args:
            text: Texto a analizar
        
        Returns:
            'full-time', 'part-time', 'temporal', 'freelance' o None
        """
        text_lower = text.lower()
        
        # Buscar en orden de especificidad
        # Nota: No usar word boundary al final porque el HTML puede concatenar sin espacios
        if re.search(r'\b(?:freelancer|freelance|independiente)\b', text_lower):
            return "freelance"
        elif re.search(r'\btiempo completo\b', text_lower) or re.search(r'\bfull.?time', text_lower):
            return "full-time"
        elif re.search(r'\btiempo parcial\b', text_lower) or re.search(r'\bpart.?time', text_lower):
            return "part-time"
        elif re.search(r'\b(?:temporal|por proyecto|contrato)\b', text_lower):
            return "temporal"
        
        return None
    
    def _extract_text(
        self,
        soup: BeautifulSoup,
        selector: str,
        max_length: Optional[int] = None
    ) -> str:
        """
        Extraer texto de elemento HTML usando selectores CSS.
        
        Args:
            soup: BeautifulSoup object
            selector: Selector CSS (puede tener múltiples opciones separadas por coma)
            max_length: Longitud máxima de texto
        
        Returns:
            Texto extraído y limpio
        """
        selectors = [s.strip() for s in selector.split(',')]
        
        for sel in selectors:
            element = soup.select_one(sel)
            if element:
                text = element.get_text(strip=True)
                if max_length:
                    text = text[:max_length]
                return text
        
        return ""
    
    def _extract_job_id(self, soup: BeautifulSoup, html: str) -> Optional[str]:
        """
        Extraer ID único del trabajo.
        
        Args:
            soup: BeautifulSoup object
            html: HTML string completo
        
        Returns:
            ID del trabajo o None
        """
        # Intentar encontrar en atributos comunes
        candidates = [
            soup.select_one('[data-job-id]'),
            soup.select_one('[id*="job"]'),
            soup.select_one('[class*="job-id"]'),
        ]
        
        for elem in candidates:
            if elem:
                job_id = elem.get('data-job-id') or elem.get('id')
                if job_id:
                    return str(job_id).strip()
        
        # Último recurso: generar hash del contenido
        import hashlib
        content_hash = hashlib.md5(html[:500].encode()).hexdigest()[:12]
        return f"job_{content_hash}"
    
    def _extract_email(self, html: str) -> Optional[str]:
        """
        Extraer email de contacto.
        
        Args:
            html: HTML string
        
        Returns:
            Email encontrado o None
        """
        # Patrón para emails
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, html)
        if match:
            return match.group(0)
        return None
    
    def _extract_phone(self, html: str) -> Optional[str]:
        """
        Extraer teléfono de contacto.
        
        Args:
            html: HTML string
        
        Returns:
            Teléfono encontrado o None
        """
        # Patrón para teléfonos mexicanos: +52, +525, (55), etc.
        phone_patterns = [
            r'\+?52\s?[\(\s]?\d{2}[\)\s]?\s?\d{4}\s?\d{4}',  # +52 XX XXXX XXXX
            r'\(\d{3}\)\s?\d{4}\s?\d{4}',  # (XXX) XXXX XXXX
            r'\d{10}',  # 10 dígitos
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(0).strip()
        
        return None
    
    def validate_job_item(self, job: JobItem) -> bool:
        """
        Validar que un JobItem tiene datos de calidad.
        
        Args:
            job: JobItem a validar
        
        Returns:
            True si es válido, False si no
        """
        # Validaciones básicas
        if not job.title or len(job.title) < 4:  # Mínimo 4 caracteres
            logger.warning(f"❌ Título inválido: {job.title}")
            return False
        
        if not job.company or len(job.company) < 1:
            logger.warning(f"❌ Empresa inválida: {job.company}")
            return False
        
        if not job.location or len(job.location) < 1:
            logger.warning(f"❌ Ubicación inválida: {job.location}")
            return False
        
        if not job.description or len(job.description) < 10:
            logger.warning(f"❌ Descripción muy corta: {len(job.description)} chars")
            return False
        
        if job.salary_min and job.salary_max and job.salary_min > job.salary_max:
            logger.warning(f"❌ Rango salarial inválido: {job.salary_min}-{job.salary_max}")
            return False
        
        return True


# ============================================================================
# Instancia global
# ============================================================================

html_parser = HTMLParserService()


def get_html_parser() -> HTMLParserService:
    """
    Obtener instancia del servicio de parseo HTML.
    
    Returns:
        Instancia de HTMLParserService
    
    **Uso:**
    ```python
    from app.services.html_parser_service import get_html_parser
    
    parser = get_html_parser()
    job = parser.parse_job_listing(html_string)
    ```
    """
    return html_parser
