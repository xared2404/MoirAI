"""
Servicio de web scraping para OCC.com.mx
Permite extraer información de ofertas de trabajo y realizar búsquedas automatizadas.
"""

import asyncio
import re
import html
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode, urlparse, parse_qs
import json
import logging

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Session, create_engine, select

from ..core.database import get_session
from ..core.config import settings

# Configurar logging
logger = logging.getLogger(__name__)


class JobOffer(BaseModel):
    """Modelo para una oferta de trabajo extraída de OCC"""
    job_id: str
    title: str
    company: str
    company_verified: bool = False
    location: str
    salary: Optional[str] = None
    publication_date: Optional[str] = None  # Ahora opcional para manejar errores de scraping
    description: Optional[str] = None
    benefits: List[str] = []
    job_type: Optional[str] = None  # Tiempo completo, medio tiempo, etc.
    work_mode: Optional[str] = None  # Remoto, presencial, híbrido
    category: Optional[str] = None
    subcategory: Optional[str] = None
    experience_required: Optional[str] = None
    # ✅ AGREGAR: experience_level (para compatibilidad con JobPosition)
    experience_level: Optional[str] = None
    education_required: Optional[str] = None
    skills: List[str] = []
    url: Optional[str] = None  # Ahora opcional para manejar errores de scraping
    is_featured: bool = False
    is_new: bool = False
    company_logo: Optional[str] = None
    contact_info: Dict = Field(default_factory=dict)
    # Campos adicionales del contenedor de detalles
    full_description: Optional[str] = None
    requirements: List[str] = []
    activities: List[str] = []
    soft_skills: List[str] = []
    work_schedule: Optional[str] = None
    contract_type: Optional[str] = None
    minimum_education: Optional[str] = None
    share_url: Optional[str] = None
    job_detail_id: Optional[str] = None


class SearchFilters(BaseModel):
    """Filtros de búsqueda para OCC"""
    keyword: str
    location: Optional[str] = None
    category: Optional[str] = None
    salary_range: Optional[str] = None
    experience_level: Optional[str] = None
    work_mode: Optional[str] = None  # remote, hybrid, onsite
    job_type: Optional[str] = None
    company_verified: bool = False
    sort_by: str = "relevance"  # relevance, date
    page: int = 1


class OCCScraper:
    """Servicio principal para web scraping de OCC.com.mx"""
    
    BASE_URL = "https://www.occ.com.mx"
    SEARCH_URL = f"{BASE_URL}/empleos/de-"
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'identity',  # Desactivar compresión para evitar problemas de parsing
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            headers=self.headers, 
            timeout=30.0,
            follow_redirects=True  # Seguir redirects automáticamente
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    def _build_search_url(self, filters: SearchFilters) -> str:
        """Construye la URL de búsqueda basada en los filtros"""
        # Normalizar keyword para URL
        keyword_normalized = filters.keyword.lower().replace(" ", "-")
        base_url = f"{self.SEARCH_URL}{keyword_normalized}/"
        
        params = {}
        
        if filters.location:
            params['l'] = filters.location
        
        if filters.salary_range:
            params['salario'] = filters.salary_range
        
        if filters.experience_level:
            params['experiencia'] = filters.experience_level
        
        if filters.work_mode:
            if filters.work_mode == "remote":
                params['modalidad'] = "remoto"
            elif filters.work_mode == "hybrid":
                params['modalidad'] = "hibrido"
            elif filters.work_mode == "onsite":
                params['modalidad'] = "presencial"
        
        if filters.company_verified:
            params['empresa_verificada'] = "1"
        
        if filters.sort_by == "date":
            params['sort'] = "2"
        else:
            params['sort'] = "1"  # relevance
        
        if filters.page > 1:
            params['page'] = str(filters.page)
        
        if params:
            return f"{base_url}?{urlencode(params)}"
        return base_url
    
    async def search_jobs(self, filters: SearchFilters) -> Tuple[List[JobOffer], int]:
        """
        Realiza una búsqueda de empleos en OCC
        Returns: (list_of_jobs, total_results)
        """
        search_url = self._build_search_url(filters)
        logger.info(f"Buscando empleos en: {search_url}")
        
        try:
            # Agregar delay para ser respetuoso con el servidor
            await asyncio.sleep(1)
            
            response = await self.session.get(search_url)
            response.raise_for_status()
            
            # Verificar que el contenido sea texto válido
            content_type = response.headers.get('content-type', '')
            if 'text/html' not in content_type:
                logger.warning(f"Content-Type inesperado: {content_type}")
            
            # Intentar decodificar el contenido correctamente
            try:
                html_content = response.content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    html_content = response.content.decode('latin-1')
                except UnicodeDecodeError:
                    html_content = response.content.decode('utf-8', errors='ignore')
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extraer total de resultados
            total_results = self._extract_total_results(soup)
            
            # Extraer ofertas de trabajo
            job_offers = self._extract_job_offers(soup, filters.keyword)
            
            logger.info(f"Encontradas {len(job_offers)} ofertas de {total_results} totales")
            return job_offers, total_results
            
        except httpx.RequestError as e:
            logger.error(f"Error en la solicitud HTTP: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado al buscar empleos: {e}")
            raise
    
    def _extract_total_results(self, soup: BeautifulSoup) -> int:
        """Extrae el número total de resultados"""
        try:
            # Buscar el elemento que contiene el total de ofertas
            total_elem = soup.find('p', {'data-total-offers': True})
            if total_elem:
                total_text = total_elem.get_text(strip=True)
                # Extraer número del texto "292 resultados"
                numbers = re.findall(r'\d+', total_text)
                if numbers:
                    return int(numbers[0])
            
            # Método alternativo: buscar en el texto
            results_text = soup.find(text=re.compile(r'\d+\s+resultados?'))
            if results_text:
                numbers = re.findall(r'\d+', results_text)
                if numbers:
                    return int(numbers[0])
            
            return 0
        except Exception as e:
            logger.warning(f"No se pudo extraer el total de resultados: {e}")
            return 0
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """
        Extrae habilidades técnicas de un texto usando keywords predefinidas.
        Se utiliza como método consolidado desde múltiples parsers.
        
        Args:
            text (str): Texto a analizar (descripción, título, etc.)
            
        Returns:
            List[str]: Lista de habilidades encontradas
        """
        # Keywords técnicas conocidas (expandible)
        tech_keywords = [
            'python', 'java', 'javascript', 'c\\+\\+', 'sql', 'r\\b', 'scala', 'kotlin',
            'react', 'angular', 'vue', 'node\\.?js', 'express', 'django', 'flask',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins',
            'git', 'rest', 'api', 'graphql', 'mongodb', 'postgresql', 'mysql',
            'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'pandas', 'numpy',
            'data science', 'analytics', 'tableau', 'power bi', 'looker', 'scrum', 'agile'
        ]
        
        skills = []
        text_lower = text.lower()
        
        for keyword in tech_keywords:
            if re.search(keyword, text_lower):
                # Limpiar nombre de skill y evitar duplicados
                skill_name = keyword.replace('\\\\', '')
                if skill_name not in skills:
                    skills.append(skill_name.title())
        
        logger.debug(f"Skills extracted from text: {skills}")
        return skills
    
    def _detect_work_mode(self, text: str) -> str:
        """
        Detecta el modo de trabajo (Remoto, Híbrido, Presencial) basado en keywords.
        Método consolidado usado por múltiples parsers.
        
        Args:
            text (str): Texto a analizar
            
        Returns:
            str: Modo de trabajo detectado
        """
        text_lower = text.lower()
        
        # Detectar modalidad de trabajo por keywords
        if any(word in text_lower for word in ['remoto', 'remote', 'trabajo desde casa', 'desde casa', 'home office']):
            logger.debug("Work mode detected: Remote")
            return "Remoto"
        elif any(word in text_lower for word in ['híbrido', 'hybrid', 'híbrida', 'mixto']):
            logger.debug("Work mode detected: Hybrid")
            return "Híbrido"
        elif any(word in text_lower for word in ['presencial', 'onsite', 'on-site', 'oficina', 'en sitio']):
            logger.debug("Work mode detected: Onsite")
            return "Presencial"
        else:
            logger.debug("Work mode: Not specified")
            return "No especificado"
    
    def _detect_job_type(self, text: str) -> str:
        """
        Detecta el tipo de contrato/empleo basado en keywords.
        Método consolidado usado por múltiples parsers.
        
        Args:
            text (str): Texto a analizar
            
        Returns:
            str: Tipo de contrato detectado
        """
        text_lower = text.lower()
        
        # Detectar tipo de contrato por keywords
        if any(word in text_lower for word in ['tiempo completo', 'full-time', 'full time', 'fulltime', 'jornada completa']):
            logger.debug("Job type detected: Full-time")
            return "Tiempo Completo"
        elif any(word in text_lower for word in ['tiempo parcial', 'part-time', 'part time', 'parttime', 'jornada parcial']):
            logger.debug("Job type detected: Part-time")
            return "Tiempo Parcial"
        elif any(word in text_lower for word in ['freelance', 'freelancer', 'proyecto', 'contratista', 'por proyecto']):
            logger.debug("Job type detected: Freelance")
            return "Freelance"
        elif any(word in text_lower for word in ['temporal', 'provisional', 'indefinido']):
            logger.debug("Job type detected: Temporal")
            return "Temporal"
        else:
            logger.debug("Job type: Not specified")
            return "No especificado"
    
    def _extract_job_offers(self, soup: BeautifulSoup, search_keyword: str) -> List[JobOffer]:
        """Extrae las ofertas de trabajo de la página de resultados"""
        job_offers = []
        
        # Buscar todos los contenedores de ofertas
        job_containers = soup.find_all('div', {'data-offers-grid-offer-item-container': ''})
        
        for container in job_containers:
            try:
                job_offer = self._parse_job_container(container, search_keyword)
                if job_offer:
                    job_offers.append(job_offer)
            except Exception as e:
                logger.warning(f"Error al parsear oferta de trabajo: {e}")
                continue
        
        return job_offers
    
    def _parse_job_container(self, container: BeautifulSoup, search_keyword: str) -> Optional[JobOffer]:
        """Parsea un contenedor individual de oferta de trabajo"""
        try:
            # Extraer ID de la oferta - generar uno si no existe
            job_id = container.get('data-id', '')
            if not job_id:
                # Generar ID basado en título + empresa si no hay data-id
                title_elem = container.find('h2')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    job_id = f"occ-{hash(title) % 1000000}"
                else:
                    return None
            
            # Extraer título
            title_elem = container.find('h2')
            title = title_elem.get_text(strip=True) if title_elem else "Sin título"
            
            # Extraer empresa - múltiples estrategias
            company = "Empresa no especificada"
            company_verified = False
            
            # Estrategia 1: buscar link de empresa
            company_elem = container.find('a', href=re.compile(r'/empleos/bolsa-de-trabajo-'))
            
            # Estrategia 2: buscar por patrones de texto común
            if not company_elem:
                company_elem = container.find('span', string=re.compile(r'Empresa confidencial'))
            
            # Estrategia 3: buscar cualquier link que no sea el título del empleo
            if not company_elem:
                links = container.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if 'empleo' not in href and 'empleos' not in href and link.get_text(strip=True):
                        company_elem = link
                        break
            
            # Estrategia 4: buscar texto después del título
            if not company_elem:
                # Buscar párrafos que podrían contener nombre de empresa
                paragraphs = container.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 3 and len(text) < 100:
                        company_elem = p
                        break
            
            if company_elem:
                company = company_elem.get_text(strip=True)
                # Verificar si la empresa está verificada
                verified_icon = container.find('svg', {'viewBox': '0 0 24 24'})
                company_verified = verified_icon is not None
            
            # Extraer ubicación - múltiples estrategias
            location = "Ubicación no especificada"
            
            # Estrategia 1: buscar por clases específicas
            location_elem = container.find('p', class_=re.compile(r'text-grey-900.*text-sm'))
            
            # Estrategia 2: buscar por patrones de texto de ubicación
            if not location_elem:
                # Buscar texto que contenga palabras típicas de ubicación
                location_patterns = [
                    re.compile(r'.*(Ciudad.*México|CDMX|México.*DF).*', re.IGNORECASE),
                    re.compile(r'.*(Guadalajara|Monterrey|Puebla|Tijuana).*', re.IGNORECASE),
                    re.compile(r'.*\b\w+,\s*\w+\b.*'),  # Patrón "Ciudad, Estado"
                ]
                
                all_text = container.get_text()
                for pattern in location_patterns:
                    match = pattern.search(all_text)
                    if match:
                        location = match.group(0).strip()[:50]  # Limitar longitud
                        break
            
            # Estrategia 3: buscar en párrafos pequeños
            if not location_elem and location == "Ubicación no especificada":
                paragraphs = container.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and 10 < len(text) < 50 and (',' in text or 'México' in text):
                        location_elem = p
                        break
            
            if location_elem:
                location = location_elem.get_text(strip=True)
            
            # Extraer salario
            salary_elem = container.find('span', class_=re.compile(r'mr-2.*font-base'))
            salary = None
            if salary_elem:
                salary_text = salary_elem.get_text(strip=True)
                if "sueldo no mostrado" not in salary_text.lower():
                    salary = salary_text
            
            # Extraer fecha de publicación
            date_elem = container.find('span', class_=re.compile(r'mr-2.*text-sm.*font-light'))
            publication_date = date_elem.get_text(strip=True) if date_elem else "Fecha no especificada"
            
            # Extraer beneficios
            benefits = []
            benefit_items = container.find_all('li', class_=re.compile(r'block.*relative.*font-light'))
            for item in benefit_items:
                benefit_text = item.get_text(strip=True)
                if benefit_text:
                    benefits.append(benefit_text)
            
            # Verificar si es oferta destacada
            is_featured = container.find('span', string=re.compile(r'Recomendada')) is not None
            
            # Verificar si es nueva oferta
            is_new = container.find('span', string=re.compile(r'Sé de los primeros en postularte')) is not None
            
            # Extraer logo de la empresa
            company_logo = None
            img_elem = container.find('img', alt=re.compile(r'Imagen de empresa'))
            if img_elem and img_elem.get('src'):
                company_logo = img_elem.get('src')
            
            # Extraer descripción breve del empleo (si está disponible en el contenedor)
            description = None
            # Buscar párrafos que podrían contener descripción
            all_text = container.get_text()
            # Si hay suficiente contenido, intentar extraer una descripción
            if len(all_text) > 200:
                # Extraer las primeras 200 caracteres significativos
                text_lines = [line.strip() for line in all_text.split('\n') if line.strip() and len(line.strip()) > 20]
                if len(text_lines) > 3:
                    description = '\n'.join(text_lines[2:5])[:300]  # Primeras 300 chars
            
            # Extraer categoría/tipo de empleo si está disponible
            category = None
            work_mode = None
            job_type = None
            
            # Buscar en el HTML del contenedor etiquetas que indiquen tipo
            tags = container.find_all('span', class_=re.compile(r'badge|label|tag|category|type'))
            for tag in tags:
                tag_text = tag.get_text(strip=True).lower()
                # Detectar modalidad de trabajo
                if 'remoto' in tag_text:
                    work_mode = 'Remoto'
                elif 'híbrido' in tag_text:
                    work_mode = 'Híbrido'
                elif 'presencial' in tag_text:
                    work_mode = 'Presencial'
                # Detectar tipo de contrato
                elif 'tiempo completo' in tag_text or 'full-time' in tag_text:
                    job_type = 'Tiempo Completo'
                elif 'tiempo parcial' in tag_text or 'part-time' in tag_text:
                    job_type = 'Tiempo Parcial'
                elif 'freelance' in tag_text or 'contratista' in tag_text:
                    job_type = 'Freelance'
            
            # Extraer requisitos educativos si están visibles
            education_required = None
            experience_required = None
            
            # Buscar patrones de educación
            for text in container.get_text().split('\n'):
                text = text.strip()
                if 'licenciatura' in text.lower() or 'ingeniería' in text.lower() or 'maestría' in text.lower():
                    education_required = text[:100]
                elif 'año' in text.lower() and 'experiencia' in text.lower():
                    experience_required = text[:100]
            
            # Extraer habilidades técnicas usando método consolidado
            container_text = container.get_text()
            skills = self._extract_skills_from_text(container_text)
            
            # Construir URL de la oferta
            job_url = f"{self.BASE_URL}/empleo/{job_id}"
            
            return JobOffer(
                job_id=job_id,
                title=title,
                company=company,
                company_verified=company_verified,
                location=location,
                salary=salary,
                publication_date=publication_date,
                description=description,
                benefits=benefits,
                job_type=job_type,
                work_mode=work_mode,
                category=category,
                experience_required=experience_required,
                education_required=education_required,
                skills=skills,
                url=job_url,
                is_featured=is_featured,
                is_new=is_new,
                company_logo=company_logo
            )
            
        except Exception as e:
            logger.error(f"Error al parsear contenedor de oferta: {e}")
            return None
    
    async def get_job_details_api(self, job_id: str) -> Optional[JobOffer]:
        """
        Obtiene los detalles completos de una oferta usando el endpoint API alternativo.
        Este método usa: https://oferta.occ.com.mx/offer/{job_id}/d/j
        que retorna HTTP 200 y JSON completo (vs HTML bloqueado en /empleo/{job_id})
        """
        api_url = f"https://oferta.occ.com.mx/offer/{job_id}/d/j"
        
        headers = {
            "referer": "https://www.occ.com.mx/",
            "origin": "https://www.occ.com.mx",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        
        try:
            response = await self.session.get(api_url, headers=headers, params={"ipo": "41", "iapo": "1"})
            response.raise_for_status()
            
            data = response.json()
            job_offer = self._parse_job_detail_from_api(data, job_id)
            
            if job_offer:
                logger.info(f"Job details retrieved from API for job_id: {job_id}")
                return job_offer
            else:
                logger.warning(f"Failed to parse API response for job_id: {job_id}")
                return None
            
        except httpx.HTTPStatusError as e:
            logger.warning(f"API endpoint returned {e.response.status_code} for job_id {job_id}, falling back to HTML scraping")
            return await self.get_job_details(job_id)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response for job_id {job_id}: {e}")
            return await self.get_job_details(job_id)
        except httpx.RequestError as e:
            logger.error(f"Network error retrieving API job details for {job_id}: {e}")
            return await self.get_job_details(job_id)
        except Exception as e:
            logger.error(f"Unexpected error retrieving API job details for {job_id}: {e}")
            return await self.get_job_details(job_id)
    
    def _parse_job_detail_from_api(self, data: dict, job_id: str) -> Optional[JobOffer]:
        """
        Parsea la respuesta JSON del API alternativo de OCC.
        Estructura: { o: {...}, c: {...}, e: {...}, s: {...}, sk: {...}, kq: {...} }
        
        Endpoint: https://oferta.occ.com.mx/offer/{job_id}/d/j?ipo=41&iapo=1
        
        Mapeo de Campos Disponibles:
        ✅ st        = Fecha de publicación (ISO 8601): "2025-10-21T00:00:00Z"
        ✅ lha       = URL de acceso directo (con tracking): "https://www.occ.com.mx?oi=..."
        ✅ ur        = URL de compartir relativa (con parámetros): "/empleo/oferta/20808643..."
        ✅ dlu       = Fecha última actualización (ISO 8601): "2025-10-21T00:00:00Z"
        ✅ dluf      = Fecha formateada (español): "21 de octubre"
        ✅ dlur      = Fecha relativa (texto): "Hace 3 días"
        ✅ pt        = Posting time (ISO 8601): "2025-10-21T00:00:00Z"
        ✅ Contacto  = Campos "cn" (nombre) en sección company_data
        
        Campos Extraídos (25+):
        ✅ Título, Empresa, Ubicación, Salario, Categoría
        ✅ Tipo de Contrato, Modalidad, Educación, Experiencia
        ✅ Descripción (HTML), Habilidades, Logo Empresa
        ✅ Fecha de Publicación (st), URL de Compartir (lha, ur)
        ⚠️ Beneficios (en HTML de descripción), Soft skills (requiere NLP)
        ❌ Contacto Directo (email/teléfono - no disponible en API)
        """
        try:
            # Extraer secciones principales
            offer = data.get("o", {})  # Offer details
            company_data = data.get("c", {})  # Company
            extra_data = data.get("e", {})  # Extra info
            skills_data = data.get("sk", {})  # Skills
            
            # ===== CAMPOS CRÍTICOS (SIEMPRE DISPONIBLES) =====
            
            # Campos principales de la oferta (offer section "o")
            job_title = offer.get("t", "Sin título")
            company_name = company_data.get("cn", "Empresa no especificada")
            company_verified = company_data.get("cver", False)
            location = offer.get("l", "Ubicación no especificada")
            
            # Información salarial
            salary_min = offer.get("smin")
            salary_max = offer.get("smax")
            salary_currency = offer.get("sc", "MXN")
            
            # Categorías y tipo de empleo
            category = offer.get("cat", []) if offer.get("cat") else []
            work_mode = offer.get("wm", "No especificado")  # Remote mode: presencial/remoto/hibrido
            contract_type = offer.get("ct", "Indefinido")  # Contract type
            
            # Requisitos
            education_required = extra_data.get("me", "No especificado")
            experience_required = extra_data.get("ex", "No especificado")
            
            # ===== FECHAS DE PUBLICACIÓN =====
            # Campo "st" = Fecha de publicación (ISO 8601): "2025-10-21T00:00:00Z"
            # Campo "dlu" = Fecha última actualización (ISO 8601): "2025-10-21T00:00:00Z"
            # Campo "dluf" = Fecha formateada en español (ej: "21 de octubre")
            # Campo "dlur" = Fecha relativa (ej: "Hace 3 días")
            # Campo "pt" = Posting time (ISO 8601): "2025-10-21T00:00:00Z"
            #
            # ESTRATEGIA: Mantener fecha relativa como string para BD
            # El job_application_service hace la conversión si es necesario
            
            publication_date = None
            
            # Prioridad 1: Usar "st" (fecha de publicación en ISO 8601)
            if offer.get("st"):
                publication_date = offer.get("st")  # Mantener como string ISO
                logger.debug(f"Publication date from 'st' field (ISO): {publication_date}")
            
            # Fallback 2: Usar "dlur" (fecha relativa)
            elif offer.get("dlur"):
                publication_date = offer.get("dlur")  # Ej: "Hace 5 días"
                logger.debug(f"Using relative date 'dlur': {publication_date}")
            
            # Fallback 3: Usar "dluf" (fecha formateada en español)
            elif offer.get("dluf"):
                publication_date = offer.get("dluf")  # Ej: "21 de octubre"
                logger.debug(f"Using formatted date 'dluf': {publication_date}")
            
            # Fallback final: fecha actual si nada está disponible
            if not publication_date:
                publication_date = datetime.now().isoformat()
                logger.warning(f"No publication date found for job {job_id}, using current datetime")
            
            # URL de la oferta
            # Prioridad 1: Usar "lha" (URL con tracking)
            job_url = offer.get("lha") if offer.get("lha") else f"https://www.occ.com.mx/empleo/{job_id}"
            
            # URL de compartir
            # Campo "ur" = URL relativa con todos los parámetros de tracking
            share_url = offer.get("ur")
            if share_url and not share_url.startswith("http"):
                share_url = f"https://www.occ.com.mx{share_url}"
            elif not share_url:
                share_url = f"https://www.occ.com.mx/empleo/oferta/{job_id}"
            
            logger.debug(f"URLs extracted - job_url: {job_url}, share_url: {share_url[:80]}...")
            
            # ===== DESCRIPCIÓN (HTML DECODIFICADO) =====
            description = ""
            full_description = ""
            description_html = offer.get("ld", "")
            
            if description_html:
                try:
                    # Decodificar entidades HTML
                    decoded_description = html.unescape(description_html)
                    # Extraer texto limpio con BeautifulSoup
                    soup = BeautifulSoup(decoded_description, 'html.parser')
                    full_description = soup.get_text(separator=" ", strip=True)
                    description = full_description[:500]  # Resumen de 500 chars
                    
                    logger.debug(f"Description decoded for job_id {job_id}, length: {len(full_description)}")
                except Exception as e:
                    logger.warning(f"Error decoding HTML description for job_id {job_id}: {e}")
                    description = ""
                    full_description = ""
            
            # ===== DETECCIÓN DE MODALIDAD Y TIPO =====
            
            # Detectar modo de trabajo mejorado (Remote, Hybrid, Presencial)
            detected_work_mode = self._detect_work_mode(
                f"{description} {job_title} {work_mode}"
            )
            
            # Detectar tipo de contrato mejorado
            detected_job_type = self._detect_job_type(
                f"{contract_type} {job_title} {full_description}"
            )
            
            # ===== HABILIDADES/SKILLS =====
            
            skills_list = []
            
            # Intentar extraer de sección de skills
            if isinstance(skills_data, list):
                skills_list = [
                    s.get("n", "").strip() 
                    for s in skills_data 
                    if s.get("n", "").strip()
                ]
            elif isinstance(skills_data, dict):
                skills_list = skills_data.get("list", [])
            
            # Si no hay habilidades en la sección, detectarlas del texto
            if not skills_list:
                combined_text = f"{full_description} {job_title} {description}"
                skills_list = self._extract_skills_from_text(combined_text)
                logger.debug(f"Skills extracted from text for job_id {job_id}: {skills_list}")
            
            # ===== BENEFICIOS Y REQUISITOS (DESDE HTML) =====
            
            benefits = []
            requirements = []
            activities = []
            soft_skills = []
            
            # Intentar extraer beneficios del HTML de descripción
            if description_html:
                try:
                    soup = BeautifulSoup(html.unescape(description_html), 'html.parser')
                    
                    # Buscar listas de beneficios
                    uls = soup.find_all('ul')
                    for ul in uls:
                        lis = ul.find_all('li')
                        for li in lis:
                            text = li.get_text(strip=True)
                            if text and len(text) > 5 and len(text) < 150:
                                benefits.append(text)
                    
                    # Remover duplicados
                    benefits = list(set(benefits))[:10]  # Máximo 10 beneficios
                    
                except Exception as e:
                    logger.debug(f"Could not extract benefits from HTML for {job_id}: {e}")
            
            # ===== CREAR OBJETO JOBOFFER =====
            
            job_offer = JobOffer(
                job_id=job_id,
                title=job_title,
                company=company_name,
                company_verified=company_verified,
                location=location,
                description=description,
                salary=f"${salary_min:,} - ${salary_max:,} {salary_currency}" if salary_min or salary_max else None,
                category=category if isinstance(category, str) else ", ".join(category) if category else None,
                contract_type=detected_job_type,
                work_mode=detected_work_mode,
                education_required=education_required,
                experience_required=experience_required,
                skills=skills_list,
                benefits=benefits,
                requirements=requirements[:5] if requirements else [],
                activities=activities[:5] if activities else [],
                soft_skills=soft_skills,
                full_description=full_description[:1000],  # Limitar a 1000 chars para no saturar DB
                url=job_url,
                publication_date=publication_date,  # ✅ String: ISO 8601 o fecha relativa
                is_featured=False,
                is_new=False,
                company_logo=company_data.get("logo", ""),
                share_url=share_url  # ✅ URL de compartir real
            )
            
            logger.info(f"✅ Successfully parsed job from API: {job_title} @ {company_name}")
            logger.info(f"   Publication date: {publication_date}")
            logger.info(f"   Share URL: {share_url[:60]}...")
            return job_offer
            
        except KeyError as e:
            logger.error(f"Missing required field in API response for job_id {job_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing API job detail response for job_id {job_id}: {e}")
            return None
    
    async def get_job_details(self, job_id: str) -> Optional[JobOffer]:
        """
        Obtiene los detalles completos de una oferta específica.
        Primero intenta usar el API endpoint alternativo, luego fallback a HTML scraping.
        """
        # Intentar primero con el API endpoint (más confiable)
        job_offer = await self.get_job_details_api(job_id)
        if job_offer:
            return job_offer
        
        # Fallback a HTML scraping si el API falla
        detail_url = f"{self.BASE_URL}/empleo/{job_id}"
        
        try:
            response = await self.session.get(detail_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._parse_job_detail(soup, job_id)
            
        except httpx.RequestError as e:
            logger.error(f"Error al obtener detalles del trabajo {job_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al obtener detalles: {e}")
            return None
    
    def _parse_job_detail(self, soup: BeautifulSoup, job_id: str) -> Optional[JobOffer]:
        """Parsea la página de detalles de una oferta específica"""
        try:
            # Buscar el contenedor principal de detalles
            detail_container = soup.find('div', {'id': 'job-detail-container'}) or soup.find('div', {'class': 'box_detail'})
            
            if not detail_container:
                logger.warning(f"No se encontró contenedor de detalles para job_id: {job_id}")
                return None
            
            # Extraer información principal
            job_details = self._extract_detailed_job_info(detail_container, job_id)
            
            return job_details
            
        except Exception as e:
            logger.error(f"Error al parsear detalles de la oferta {job_id}: {e}")
            return None
    
    def _extract_detailed_job_info(self, container: BeautifulSoup, job_id: str) -> JobOffer:
        """Extrae información detallada del contenedor de detalles (job-detail-container)"""
        
        try:
            # Título del empleo
            title_elem = container.find('p', {'data-offers-grid-detail-title': ''}) or container.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else "Sin título"
            
            # Empresa - buscar con <a> que contiene "Empresa confidencial" o nombre real
            company = "Empresa no especificada"
            company_verified = False
            company_link = container.find('a', href=re.compile(r'empresa-confidencial|empresa-verificada'))
            if company_link:
                company = company_link.get_text(strip=True)
            else:
                # Buscar por atributo hd_company_name
                company_input = container.find('input', {'id': 'hd_company_name'})
                if company_input:
                    company = company_input.get('value', 'Empresa no especificada')
            
            # Verificar si la empresa está verificada - buscar el icono o texto de verificación
            verified_elem = container.find('a', href=re.compile(r'Qué-significa-Empresa-verificada'))
            if verified_elem and verified_elem.find_previous_sibling() and 'verificada' in verified_elem.get_text().lower():
                company_verified = True
            
            # Ubicación
            location = "Ubicación no especificada"
            location_labels = container.find_all('label', class_='font-light')
            for label in location_labels:
                text = label.get_text(strip=True)
                if len(text) > 3 and text != 'en':
                    location = text
                    break
            
            # Alternativa: buscar en el segundo párrafo después del título
            if location == "Ubicación no especificada":
                spans = container.find_all('span', class_='line-clamp-1')
                for span in spans:
                    text = span.get_text(strip=True)
                    if 'en ' in text and any(city in text for city in ['México', 'Guadalajara', 'Monterrey', 'CDMX']):
                        parts = text.split(' en ')
                        if len(parts) > 1:
                            location = parts[1].strip()
                            break
            
            # Fecha de publicación
            publication_date = "Fecha no especificada"
            date_p = container.find('p', class_='flex font-light')
            if date_p:
                publication_date = date_p.get_text(strip=True)
            
            # Salario - buscar en párrafo con icono de dinero
            salary = None
            salary_pattern = re.compile(r'\$[\d,]+.*?(Mensual|Anual|Semanal)?')
            salary_paras = container.find_all('p')
            for para in salary_paras:
                text = para.get_text()
                if '$' in text and ('Mensual' in text or 'Anual' in text):
                    salary_match = salary_pattern.search(text)
                    if salary_match:
                        salary = salary_match.group(0)
                        break
            
            # Categoría y subcategoría - buscar secciones "Sobre el empleo"
            category = None
            subcategory = None
            education_required = None
            
            # Buscar todas las líneas de detalles
            about_section = container.find(string=re.compile(r'Sobre el empleo'))
            if about_section:
                parent = about_section.find_parent()
                if parent:
                    detail_links = parent.find_all('a', href=re.compile(r'/empleos/'))
                    if len(detail_links) > 0:
                        category = detail_links[0].get_text(strip=True)
                    if len(detail_links) > 1:
                        subcategory = detail_links[1].get_text(strip=True)
            
            # Educación mínima requerida
            edu_text = container.find(string=re.compile(r'Educación mínima'))
            if edu_text:
                parent_div = edu_text.find_parent()
                if parent_div:
                    edu_elem = parent_div.find('span', class_='text-base font-light')
                    if edu_elem:
                        education_required = edu_elem.get_text(strip=True)
            
            # Detalles: Contratación, Horario, Espacio de trabajo
            job_type = None
            work_schedule = None
            work_mode = None
            
            details_section = container.find(string=re.compile(r'Detalles'))
            if details_section:
                parent = details_section.find_parent()
                if parent:
                    detail_divs = parent.find_all('div', class_=re.compile(r'mb-1|flex'))
                    for div in detail_divs:
                        text_content = div.get_text()
                        if 'Contratación:' in text_content:
                            link = div.find('a')
                            if link:
                                job_type = link.get_text(strip=True)
                        elif 'Horario:' in text_content:
                            link = div.find('a')
                            if link:
                                work_schedule = link.get_text(strip=True)
                        elif 'Espacio de trabajo:' in text_content:
                            link = div.find('a')
                            if link:
                                text = link.get_text(strip=True).lower()
                                if 'presencial' in text:
                                    work_mode = 'presencial'
                                elif 'remoto' in text or 'home office' in text:
                                    work_mode = 'remoto'
                                elif 'híbrido' in text or 'mixto' in text:
                                    work_mode = 'híbrido'
            
            # Beneficios - buscar sección "Beneficios"
            benefits = []
            benefits_header = container.find(string=re.compile(r'Beneficios'))
            if benefits_header:
                parent = benefits_header.find_parent()
                if parent:
                    ul = parent.find('ul', class_=re.compile(r'list-disc'))
                    if ul:
                        lis = ul.find_all('li')
                        for li in lis:
                            text = li.get_text(strip=True)
                            if text:
                                benefits.append(text)
            
            # Descripción completa - buscar sección "Descripción"
            full_description = None
            description_header = container.find(string=re.compile(r'Descripción'))
            if description_header:
                parent = description_header.find_parent()
                if parent:
                    desc_div = parent.find_next('div', class_=re.compile(r'break-words'))
                    if desc_div:
                        full_description = desc_div.get_text(strip=True)
            
            # Requisitos y habilidades desde la descripción
            requirements = []
            activities = []
            soft_skills = []
            
            if full_description:
                # Buscar secciones de requisitos
                if 'Requisitos:' in full_description:
                    req_section = full_description.split('Requisitos:')[1].split('Habilidades:')[0] if 'Habilidades:' in full_description else full_description.split('Requisitos:')[1]
                    requirements = [r.strip() for r in req_section.split('\n') if r.strip() and len(r.strip()) > 5]
                
                # Buscar actividades
                if 'Actividades:' in full_description:
                    act_section = full_description.split('Actividades:')[1].split('Habilidades:')[0] if 'Habilidades:' in full_description else full_description.split('Actividades:')[1]
                    activities = [a.strip() for a in act_section.split('\n') if a.strip() and len(a.strip()) > 5]
                
                # Buscar habilidades soft
                if 'Habilidades:' in full_description:
                    hab_section = full_description.split('Habilidades:')[1].split('Requisitos:')[0] if 'Requisitos:' in full_description else full_description.split('Habilidades:')[1]
                    soft_skills = [h.strip() for h in hab_section.split(',') if h.strip()]
            
            # Habilidades técnicas desde campo oculto
            skills = []
            skills_input = container.find('input', {'id': 'hd_skills'})
            if skills_input and skills_input.get('value'):
                try:
                    skills_data = json.loads(skills_input.get('value'))
                    skills = [skill.get('sn', '') for skill in skills_data if skill.get('sn')]
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Información de contacto
            contact_info = {}
            contact_name_input = container.find('input', {'id': 'hd_contact_name'})
            contact_phone_input = container.find('input', {'id': 'hd_contact_phone'})
            contact_mail_input = container.find('input', {'id': 'hd_contact_mail'})
            
            if contact_name_input and contact_name_input.get('value'):
                contact_info['name'] = contact_name_input.get('value')
            if contact_phone_input and contact_phone_input.get('value'):
                contact_info['phone'] = contact_phone_input.get('value')
            if contact_mail_input and contact_mail_input.get('value'):
                contact_info['email'] = contact_mail_input.get('value')
            
            # URL compartible
            share_url = None
            share_container = container.find('div', {'job-share-container': ''})
            if share_container:
                share_url = share_container.get('data-url')
            
            # ID de detalle del trabajo
            job_detail_id = None
            detail_input = container.find('input', {'id': 'hihco_detail'})
            if detail_input:
                job_detail_id = detail_input.get('value')
            
            # Verificar si es oferta destacada
            is_featured = container.find('label', string=re.compile(r'Recomendada')) is not None
            
            # Verificar si es nueva (publicada ayer o hoy)
            is_new = 'Ayer' in publication_date or 'Hoy' in publication_date
            
            # Logo de la empresa
            company_logo = None
            img_elem = container.find('img', {'src': re.compile(r'logos')})
            if img_elem:
                company_logo = img_elem.get('src')
            
            return JobOffer(
                job_id=job_id,
                title=title,
                company=company,
                company_verified=company_verified,
                location=location,
                salary=salary,
                publication_date=publication_date,
                description=full_description,
                benefits=benefits,
                job_type=job_type,
                work_mode=work_mode,
                category=category,
                subcategory=subcategory,
                education_required=education_required,
                skills=skills,
                url=f"{self.BASE_URL}/empleo/oferta/{job_id}",
                is_featured=is_featured,
                is_new=is_new,
                company_logo=company_logo,
                contact_info=contact_info,
                full_description=full_description,
                requirements=requirements,
                activities=activities,
                soft_skills=soft_skills,
                work_schedule=work_schedule,
                contract_type=job_type,
                share_url=share_url,
                job_detail_id=job_detail_id
            )
            
        except Exception as e:
            logger.error(f"Error al extraer información detallada del empleo: {e}")
            # Retornar un objeto mínimo
            return JobOffer(
                job_id=job_id,
                title="Error al procesar",
                company="Desconocida",
                location="No disponible",
                publication_date="N/A",
                url=f"{self.BASE_URL}/empleo/oferta/{job_id}"
            )
    
    async def search_jobs_with_details(self, filters: SearchFilters, include_details: bool = True, fetch_full_details: bool = False) -> Tuple[List[JobOffer], int]:
        """
        Realiza una búsqueda de empleos en OCC con opción de incluir detalles completos.
        
        Args:
            filters: Criterios de búsqueda
            include_details: Si incluir info enriquecida del contenedor (siempre activado)
            fetch_full_details: Si obtener detalles completos vía API OCC para cada job (más lento, datos 95%+ completos)
        
        Returns: (list_of_jobs, total_results)
        
        NOTA sobre velocidad:
        - Sin fetch_full_details (default): 2-3 segundos (20 resultados)
        - Con fetch_full_details=True: 4-7 segundos (100-200ms × 20 jobs adicionales)
        - Se recomienda usar caché para optimizar (PASO 5)
        """
        logger.info(f"Starting job search with filters: {filters.dict()}")
        logger.debug(f"fetch_full_details={fetch_full_details}, include_details={include_details}")
        
        # Paso 1: Realizar la búsqueda inicial - los detalles ya están enriquecidos desde _parse_job_container
        jobs, total_results = await self.search_jobs(filters)
        logger.info(f"Initial search returned {len(jobs)} jobs out of {total_results} total")
        
        if not include_details:
            logger.debug("include_details=False, retorno datos básicos")
            return jobs, total_results
        
        # Paso 2: Si fetch_full_details=False, retorna data del contenedor enriquecida
        if not fetch_full_details:
            logger.debug("fetch_full_details=False, retorno datos enriquecidos del contenedor")
            return jobs, total_results
        
        # Paso 3: fetch_full_details=True → Obtener datos completos vía API para cada job
        logger.info(f"Fetching full details for {len(jobs)} jobs via API (this will take ~100-200ms per job)")
        enriched_jobs = []
        
        for idx, job in enumerate(jobs, 1):
            try:
                logger.debug(f"Fetching full details for job {idx}/{len(jobs)}: {job.job_id}")
                
                # Obtener detalles completos via API OCC
                full_job = await self.get_job_details_api(job.job_id)
                
                if full_job:
                    logger.debug(f"✓ Full details retrieved for job {job.job_id}")
                    enriched_jobs.append(full_job)
                else:
                    logger.warning(f"⚠ Could not parse API response for {job.job_id}, using container data")
                    enriched_jobs.append(job)
                    
            except asyncio.TimeoutError:
                logger.warning(f"⏱ Timeout fetching details for {job.job_id}, using container data")
                enriched_jobs.append(job)
            except Exception as e:
                logger.warning(f"Error fetching full details for {job.job_id}: {e}, using container data")
                enriched_jobs.append(job)  # Fallback a data del contenedor
        
        logger.info(f"Enrichment complete: {len(enriched_jobs)} jobs with full details")
        return enriched_jobs, total_results
    
    async def get_trending_jobs(self, limit: int = 20) -> List[JobOffer]:
        """Obtiene empleos en tendencia (más recientes y destacados)"""
        filters = SearchFilters(
            keyword="data science",  # Keyword popular para pruebas
            sort_by="date"
        )
        
        jobs, _ = await self.search_jobs(filters)
        
        # Filtrar y ordenar por empleos destacados primero, luego por fecha
        trending = sorted(jobs, key=lambda x: (x.is_featured, x.is_new), reverse=True)
        
        return trending[:limit]
    
    async def get_job_statistics(self, keywords: List[str]) -> Dict[str, any]:
        """Obtiene estadísticas de empleos para múltiples keywords"""
        stats = {
            "keywords": keywords,
            "total_jobs": 0,
            "jobs_by_keyword": {},
            "top_companies": {},
            "top_locations": {},
            "average_features": {
                "featured_percentage": 0,
                "new_percentage": 0,
                "verified_companies": 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
        all_jobs = []
        
        for keyword in keywords:
            filters = SearchFilters(keyword=keyword)
            jobs, total = await self.search_jobs(filters)
            
            stats["jobs_by_keyword"][keyword] = {
                "total_found": len(jobs),
                "total_available": total
            }
            
            all_jobs.extend(jobs)
            await asyncio.sleep(1)  # Delay entre búsquedas
        
        # Calcular estadísticas generales
        stats["total_jobs"] = len(all_jobs)
        
        if all_jobs:
            # Top empresas
            company_counts = {}
            location_counts = {}
            featured_count = 0
            new_count = 0
            verified_count = 0
            
            for job in all_jobs:
                # Contar empresas
                if job.company not in company_counts:
                    company_counts[job.company] = 0
                company_counts[job.company] += 1
                
                # Contar ubicaciones
                if job.location not in location_counts:
                    location_counts[job.location] = 0
                location_counts[job.location] += 1
                
                # Contar características
                if job.is_featured:
                    featured_count += 1
                if job.is_new:
                    new_count += 1
                if job.company_verified:
                    verified_count += 1
            
            # Top 10 empresas
            stats["top_companies"] = dict(sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10])
            
            # Top 10 ubicaciones
            stats["top_locations"] = dict(sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10])
            
            # Porcentajes
            total_jobs = len(all_jobs)
            stats["average_features"]["featured_percentage"] = round((featured_count / total_jobs) * 100, 2)
            stats["average_features"]["new_percentage"] = round((new_count / total_jobs) * 100, 2)
            stats["average_features"]["verified_companies"] = round((verified_count / total_jobs) * 100, 2)
        
        return stats
    
    def _normalize_date(self, date_text: str) -> str:
        """Normaliza las fechas relativas de OCC a fechas absolutas"""
        date_text = date_text.lower().strip()
        now = datetime.now()
        
        if "hoy" in date_text:
            return now.strftime("%Y-%m-%d")
        elif "ayer" in date_text:
            return (now - timedelta(days=1)).strftime("%Y-%m-%d")
        elif "hace" in date_text:
            # Extraer número de días
            match = re.search(r'hace\s+(\d+)\s+día', date_text)
            if match:
                days = int(match.group(1))
                return (now - timedelta(days=days)).strftime("%Y-%m-%d")
        
        return date_text


class OCCJobTracker:
    """Servicio para rastrear y monitorear ofertas de trabajo"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.scraper = OCCScraper()
    
    async def track_search_results(self, 
                                 filters: SearchFilters, 
                                 max_pages: int = 5) -> Dict[str, any]:
        """
        Rastrea los resultados de una búsqueda específica
        """
        all_jobs = []
        total_results = 0
        
        async with OCCScraper() as scraper:
            for page in range(1, max_pages + 1):
                filters.page = page
                jobs, total = await scraper.search_jobs(filters)
                
                if page == 1:
                    total_results = total
                
                all_jobs.extend(jobs)
                
                # Si no hay más resultados, salir del loop
                if len(jobs) == 0:
                    break
                
                # Delay para evitar ser bloqueado
                await asyncio.sleep(2)
        
        return {
            "search_filters": filters.dict(),
            "total_results": total_results,
            "jobs_found": len(all_jobs),
            "jobs": all_jobs,
            "timestamp": datetime.now().isoformat()
        }
    
    async def monitor_keywords(self, keywords: List[str]) -> Dict[str, List[JobOffer]]:
        """Monitorea múltiples keywords y retorna ofertas para cada una"""
        results = {}
        
        async with OCCScraper() as scraper:
            for keyword in keywords:
                filters = SearchFilters(keyword=keyword, sort_by="date")
                jobs, _ = await scraper.search_jobs(filters)
                results[keyword] = jobs
                
                # Delay entre búsquedas
                await asyncio.sleep(3)
        
        return results
    
    async def get_new_jobs_for_profile(self, user_profile: Dict[str, any]) -> List[JobOffer]:
        """
        Obtiene nuevas ofertas que coincidan con el perfil del usuario
        """
        # Extraer keywords del perfil del usuario
        keywords = user_profile.get("skills", []) + user_profile.get("interests", [])
        location = user_profile.get("preferred_location")
        
        all_matches = []
        
        for keyword in keywords[:5]:  # Limitar a 5 keywords principales
            filters = SearchFilters(
                keyword=keyword,
                location=location,
                sort_by="date"
            )
            
            async with OCCScraper() as scraper:
                jobs, _ = await scraper.search_jobs(filters)
                
                # Filtrar solo trabajos nuevos (últimos 3 días)
                recent_jobs = [
                    job for job in jobs 
                    if any(term in job.publication_date.lower() 
                          for term in ["hoy", "ayer", "hace 1", "hace 2", "hace 3"])
                ]
                
                all_matches.extend(recent_jobs)
                await asyncio.sleep(2)
        
        # Eliminar duplicados basándose en job_id
        unique_jobs = {}
        for job in all_matches:
            if job.job_id not in unique_jobs:
                unique_jobs[job.job_id] = job
        
        return list(unique_jobs.values())


# Funciones de utilidad para integración con FastAPI
async def search_jobs_service(filters: SearchFilters) -> Tuple[List[JobOffer], int]:
    """Servicio para búsqueda de empleos - para usar en endpoints"""
    async with OCCScraper() as scraper:
        return await scraper.search_jobs(filters)


async def get_job_details_service(job_id: str) -> Optional[JobOffer]:
    """Servicio para obtener detalles de un empleo específico"""
    async with OCCScraper() as scraper:
        return await scraper.get_job_details(job_id)


async def monitor_user_interests(user_id: str, keywords: List[str]) -> Dict[str, any]:
    """Monitorea keywords de interés para un usuario específico"""
    tracker = OCCJobTracker(next(get_session()))
    results = await tracker.monitor_keywords(keywords)
    
    return {
        "user_id": user_id,
        "monitored_keywords": keywords,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }
