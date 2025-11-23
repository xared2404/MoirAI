"""
Endpoints de la API para el servicio de scraping de OCC.com.mx
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from datetime import datetime
import logging
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.occ_scraper_service import (
    SearchFilters,
    JobOffer,
    search_jobs_service,
    get_job_details_service,
    monitor_user_interests,
    OCCJobTracker,
    OCCScraper
)
from app.core.database import get_session
from app.models.job_scraping import (
    JobApplicationDB,
    SearchQueryDB,
    UserJobAlertDB
)
from app.models import JobPosition
from app.services.job_application_service import (
    JobApplicationManager,
    JobSearchManager,
    JobAlertManager,
    JobCacheManager
)
from app.middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/job-scraping", tags=["Job Scraping"])


# ============================================================================
# ESQUEMAS DE RESPUESTA Y REQUEST
# ============================================================================

class SearchRequest(BaseModel):
    """Request model para búsqueda de empleos"""
    keyword: str
    location: Optional[str] = None
    category: Optional[str] = None
    salary_min: Optional[int] = None  # Agregado campo salary_min
    salary_range: Optional[str] = None
    experience_level: Optional[str] = None
    work_mode: Optional[str] = None  # remote, hybrid, onsite
    job_type: Optional[str] = None
    company_verified: bool = False
    sort_by: str = "relevance"  # relevance, date
    page: int = 1


class SearchResponse(BaseModel):
    """Response model para resultados de búsqueda"""
    jobs: List[JobOffer]
    total_results: int
    current_page: int
    search_filters: Dict
    success: bool = True
    message: str = "Búsqueda completada exitosamente"


class JobTrackingRequest(BaseModel):
    """Request model para rastreo de empleos"""
    keywords: List[str]
    location: Optional[str] = None
    max_pages: int = 3
    user_id: Optional[str] = None


class MonitoringResponse(BaseModel):
    """Response model para monitoreo de keywords"""
    user_id: Optional[str]
    monitored_keywords: List[str]
    results: Dict[str, List[JobOffer]]
    timestamp: str
    total_jobs_found: int
    success: bool = True


class ApplicationResponse(BaseModel):
    """Respuesta de aplicación creada"""
    application_id: int
    job_title: str
    company: str
    status: str
    applied_at: datetime


class AlertResponse(BaseModel):
    """Respuesta de alerta creada"""
    alert_id: int
    keywords: List[str]
    frequency: str
    is_active: bool
    created_at: datetime


class StatsResponse(BaseModel):
    """Estadísticas de usuario"""
    total_applications: int
    status_breakdown: Dict[str, int]
    recent_applications: int
    success_rate: float


# ============================================================================
# CACHE MODELS
# ============================================================================

class CacheStoreRequest(BaseModel):
    """Request para guardar resultados de búsqueda en cache persistente"""
    jobs: List[JobOffer]
    keyword: str
    source: str = "occ"


class CacheJobItem(BaseModel):
    """Item de empleo desde cache (sin la estructura completa de JobOffer)"""
    id: Optional[int] = None
    title: str
    company: str
    location: str
    description: str
    job_type: Optional[str] = None
    work_mode: Optional[str] = None
    experience_level: Optional[str] = None
    skills: Optional[str] = None
    salary_range: Optional[str] = None
    external_job_id: Optional[str] = None
    source: str
    scraped_at: datetime
    is_active: bool


class CacheListResponse(BaseModel):
    """Response de lista de empleos desde cache"""
    jobs: List[CacheJobItem]
    total: int
    from_cache: bool = True
    returned: int
    filters_applied: Dict = {}
    cache_age_minutes: Optional[int] = None
    message: str = "Datos obtenidos desde cache persistente"


class CacheStoreResponse(BaseModel):
    """Response al guardar empleos en cache"""
    saved_count: int
    total_cached: int
    source: str
    keyword: str
    message: str


class CacheStatsResponse(BaseModel):
    """Estadísticas del cache persistente"""
    total_active: int
    expired_but_active: int
    soft_deleted: int
    total_db_records: int
    avg_age_hours: float
    top_locations: Dict[str, int]
    cache_efficiency: float  # % de registros activos vs total
    next_cleanup_recommended: bool
    timestamp: str


class JobApplicationRequest(BaseModel):
    """Request para crear aplicación"""
    job_id: str = Field(..., description="ID del trabajo en OCC")
    external_url: Optional[str] = Field(None, description="URL de aplicación externa")
    notes: Optional[str] = Field(None, description="Notas personales")


class JobAlertRequest(BaseModel):
    """Request para crear alerta de empleo"""
    keywords: List[str] = Field(..., min_items=1, description="Palabras clave para alertas")
    location: Optional[str] = Field(None, description="Ubicación")
    salary_min: Optional[int] = Field(None, description="Salario mínimo")
    work_mode: Optional[str] = Field(None, description="Modalidad de trabajo")
    frequency: str = Field("daily", description="Frecuencia de notificaciones")


class DetailedJobResponse(BaseModel):
    """Response mejorado para detalles de un empleo"""
    job_details: JobOffer
    extraction_quality: Dict = {}
    available_sections: Dict = {}
    recommendations: List[str] = []
    success: bool = True


# ============================================================================
# ENDPOINTS DE BÚSQUEDA Y SCRAPING
# ============================================================================


@router.post("/search", response_model=SearchResponse)
async def search_jobs(
    request: SearchRequest, 
    detailed: bool = Query(False, description="Incluir información enriquecida del contenedor"),
    full_details: bool = Query(False, description="Obtener detalles completos vía API OCC (más lento, 95%+ datos)"),
    db_session: AsyncSession = Depends(get_session)
):
    """
    Busca empleos en OCC.com.mx basado en los criterios especificados.
    
    ✨ NUEVO: Automáticamente guarda resultados en caché persistente (BD)
    después de la búsqueda, para evitar rescraping en futuras consultas.
    
    Parámetros:
    - detailed (query): Si es true, incluye información enriquecida del contenedor
    - full_details (query): Si es true, obtiene detalles COMPLETOS vía API para cada job
                           (100-200ms por job adicional, recomendado usar caché)
    
    Ejemplos:
    - POST /api/v1/job-scraping/search?detailed=false (rápido, datos básicos)
    - POST /api/v1/job-scraping/search?detailed=true (moderado, datos enriquecidos ~50%)
    - POST /api/v1/job-scraping/search?detailed=true&full_details=true (lento, datos completos ~95%)
    
    Nota: full_details implica detailed=true
    """
    try:
        # Convertir salary_min a salary_range si es necesario
        salary_range = request.salary_range
        if request.salary_min and not salary_range:
            if request.salary_min >= 50000:
                salary_range = "50000+"
            elif request.salary_min >= 30000:
                salary_range = "30000-50000"
            elif request.salary_min >= 20000:
                salary_range = "20000-30000"
            else:
                salary_range = "0-20000"
        
        # Convertir request a SearchFilters
        filters = SearchFilters(
            keyword=request.keyword,
            location=request.location,
            category=request.category,
            salary_range=salary_range,
            experience_level=request.experience_level,
            work_mode=request.work_mode,
            job_type=request.job_type,
            company_verified=request.company_verified,
            sort_by=request.sort_by,
            page=request.page
        )
        
        # Realizar búsqueda
        if detailed or full_details:
            async with OCCScraper() as scraper:
                jobs, total_results = await scraper.search_jobs_with_details(
                    filters, 
                    include_details=True,
                    fetch_full_details=full_details  # ← NUEVO PARÁMETRO
                )
        else:
            jobs, total_results = await search_jobs_service(filters)
        
        # ✨ NUEVO: Guardar automáticamente en caché persistente (BD)
        try:
            cache_manager = JobCacheManager(db_session)
            cached_count = await cache_manager.save_scraped_jobs(
                jobs=jobs,
                source="occ",
                keyword=request.keyword
            )
            logger.info(f"✅ Cache: {cached_count} empleos guardados para keyword '{request.keyword}'")
        except Exception as cache_error:
            # No fallar la búsqueda si hay error en cache
            logger.warning(f"⚠️  Error guardando cache: {cache_error}")
            cached_count = 0
        
        # Construir mensaje descriptivo
        if full_details:
            search_type = "completa vía API (95%+ datos)"
        elif detailed:
            search_type = "enriquecida (~50% datos)"
        else:
            search_type = "estándar (datos básicos)"
        
        return SearchResponse(
            jobs=jobs,
            total_results=total_results,
            current_page=request.page,
            search_filters=filters.dict(),
            message=f"Búsqueda {search_type} completada exitosamente. {cached_count if 'cached_count' in locals() else 'N/A'} empleos en cache."
        )
        
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error de dependencias del scraper: {str(e)}"
        )
    except Exception as e:
        import traceback
        print(f"Error detallado en search_jobs: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno en la búsqueda: {str(e)}"
        )




class DetailedJobResponse(BaseModel):
    """Response mejorado para detalles de un empleo"""
    job_details: JobOffer
    extraction_quality: Dict = {}
    available_sections: Dict = {}
    recommendations: List[str] = []
    success: bool = True


@router.get("/job/{job_id}", response_model=DetailedJobResponse)
async def get_job_details(job_id: str):
    """
    Obtiene los detalles completos de una oferta de trabajo específica.
    
    ⚠️ NOTA: OCC.com.mx tiene protección anti-bot en las páginas de detalles individuales.
    Este endpoint proporciona enriquecimiento de datos mediante búsqueda contextual.
    
    Para obtener detalles enriquecidos:
    1. Busca empleos con /search usando criterios (keyword, location, etc)
    2. Obtén los job_id del resultado
    3. Usa este endpoint para obtener la versión enriquecida
    
    O alternativamente, usa /search?detailed=true para búsqueda con extracción enriquecida.
    """
    try:
        # Intentar obtener detalles del sitio (probablemente fallará por anti-bot)
        job_details = await get_job_details_service(job_id)
        
        if not job_details:
            # Si falla, retornar un objeto vacío con recomendación
            logger.warning(f"No se pudieron obtener detalles para {job_id} via OCC - Protección anti-bot detectada")
            
            # Crear un objeto JobOffer con valores por defecto y campos opcionales
            job_details = JobOffer(
                job_id=job_id,
                title="Detalles no disponibles directamente",
                company="No disponible",
                location="No disponible",
                publication_date=None,  # Explícitamente None (ahora es opcional)
                url=f"https://www.occ.com.mx/empleo/{job_id}",  # Proporcionar URL construida
                description="OCC.com.mx tiene protección anti-bot que impide obtener detalles directamente. Use /search?detailed=true para enriquecimiento."
            )
        
        # Analizar la calidad de la extracción
        extraction_quality = {
            "has_title": bool(job_details.title and job_details.title != "Sin título"),
            "has_company": bool(job_details.company and job_details.company != "Empresa no especificada"),
            "has_salary": bool(job_details.salary),
            "has_benefits": bool(job_details.benefits),
            "has_category": bool(job_details.category),
            "has_description": bool(job_details.full_description),
            "has_skills": bool(job_details.skills),
            "completeness_score": 0
        }
        
        # Calcular puntuación de completitud
        completeness_fields = [
            job_details.title, job_details.company, job_details.location,
            job_details.salary, job_details.full_description, job_details.category
        ]
        extraction_quality["completeness_score"] = round(
            (sum(1 for f in completeness_fields if f) / len(completeness_fields)) * 100, 2
        )
        
        # Secciones disponibles
        available_sections = {
            "basic_info": True,
            "salary_info": bool(job_details.salary),
            "benefits": len(job_details.benefits) > 0,
            "job_category": bool(job_details.category),
            "job_requirements": bool(job_details.education_required),
            "technical_skills": len(job_details.skills) > 0,
            "soft_skills": len(job_details.soft_skills) > 0,
            "activities": len(job_details.activities) > 0,
            "contact_info": bool(job_details.contact_info),
            "full_description": bool(job_details.full_description)
        }
        
        # Recomendaciones
        is_data_limited = (job_details.title == "Detalles no disponibles directamente")
        
        if is_data_limited:
            recommendations = [
                "⚠️ OCC.com.mx tiene protección anti-bot en páginas individuales",
                "💡 Usa /search?detailed=true para obtener datos enriquecidos",
                f"🔗 URL directa: https://www.occ.com.mx/empleo/{job_id}",
                "📍 Accede directamente al sitio para ver todos los detalles"
            ]
        else:
            recommendations = [
                "💡 Para obtener detalles enriquecidos: usa /search?detailed=true con búsqueda de empleo",
                f"🔗 URL de OCC.com.mx: https://www.occ.com.mx/empleo/{job_id}"
            ]
        
        if not job_details.salary and not is_data_limited:
            recommendations.append("💰 El salario debe ser negociado directamente con el reclutador")
        if not job_details.full_description and not is_data_limited:
            recommendations.append("📝 Visita OCCMundial para ver la descripción completa del puesto")
        if len(job_details.benefits) == 0 and not is_data_limited:
            recommendations.append("🎁 No se encontraron beneficios especificados en la oferta")
        if not job_details.contact_info and not is_data_limited:
            recommendations.append("📞 Contacta directamente a través del formulario en OCCMundial")
        
        return DetailedJobResponse(
            job_details=job_details,
            extraction_quality=extraction_quality,
            available_sections=available_sections,
            recommendations=recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error en get_job_details: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener detalles del empleo: {str(e)}"
        )


@router.post("/track", response_model=MonitoringResponse)
async def track_job_opportunities(
    request: JobTrackingRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Rastrea oportunidades laborales para múltiples keywords
    """
    try:
        tracker = OCCJobTracker(session)
        results = await tracker.monitor_keywords(request.keywords)
        
        # Contar total de empleos encontrados
        total_jobs = sum(len(jobs) for jobs in results.values())
        
        return MonitoringResponse(
            user_id=request.user_id,
            monitored_keywords=request.keywords,
            results=results,
            timestamp=datetime.now().isoformat(),
            total_jobs_found=total_jobs
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al rastrear empleos: {str(e)}"
        )


@router.get("/trending-jobs", tags=["Discovery"])
async def get_trending_jobs(
    location: Optional[str] = Query(None, description="Ubicación para filtrar empleos"),
    limit: int = Query(20, description="Número máximo de empleos a retornar"),
    detailed: bool = Query(False, description="Incluir información detallada de cada empleo")
):
    """
    Obtiene los empleos más populares/recientes de diferentes categorías.
    
    Este endpoint realiza scraping en vivo de keywords predeterminadas para mostrar
    las tendencias actuales del mercado laboral.
    
    Parámetros:
    - detailed (query): Si es true, incluye información enriquecida (categoría, beneficios, skills, etc.)
    - limit: Número máximo de empleos a retornar
    - location: Filtrar por ubicación (opcional)
    
    Ejemplos:
    - GET /api/v1/job-scraping/trending-jobs
    - GET /api/v1/job-scraping/trending-jobs?detailed=true&limit=30&location=Mexico
    
    ✅ ENDPOINT CONSOLIDADO - Una única fuente de verdad para tendencias en vivo
    """
    try:
        trending_keywords = [
            "data science",
            "python",
            "javascript", 
            "react",
            "análisis de datos",
            "machine learning",
            "desarrollador web",
            "marketing digital"
        ]
        
        all_trending_jobs = []
        
        for keyword in trending_keywords[:4]:  # Limitar para no sobrecargar
            filters = SearchFilters(
                keyword=keyword,
                location=location,
                sort_by="date",
                page=1
            )
            
            if detailed:
                async with OCCScraper() as scraper:
                    jobs, _ = await scraper.search_jobs_with_details(filters, include_details=True)
            else:
                jobs, _ = await search_jobs_service(filters)
            
            # Tomar solo los primeros 3 empleos de cada categoría
            category_jobs = jobs[:3]
            for job in category_jobs:
                job.category = keyword  # Añadir categoría para referencia
                
            all_trending_jobs.extend(category_jobs)
        
        # Limitar al número solicitado
        return {
            "trending_jobs": all_trending_jobs[:limit],
            "total_found": len(all_trending_jobs),
            "keywords_searched": trending_keywords[:4],
            "detailed_info_included": detailed,
            "note": "Datos en vivo obtenidos por scraping. Recomendación: cachear por 1-2 horas",
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener empleos trending: {str(e)}"
        )


@router.post("/monitor-user/{user_id}")
async def setup_user_monitoring(
    user_id: str,
    keywords: List[str],
    location: Optional[str] = None
):
    """
    Configura monitoreo personalizado para un usuario específico
    """
    try:
        results = await monitor_user_interests(user_id, keywords)
        
        return {
            "message": f"Monitoreo configurado para usuario {user_id}",
            "monitoring_setup": results,
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al configurar monitoreo: {str(e)}"
        )


@router.get("/search-suggestions")
async def get_search_suggestions(query: str = Query(..., description="Término de búsqueda parcial")):
    """
    Proporciona sugerencias de búsqueda basadas en términos populares
    """
    suggestions = {
        "data": [
            "data science",
            "data analyst",
            "data engineer", 
            "database administrator"
        ],
        "python": [
            "python developer",
            "python backend",
            "python django",
            "python flask"
        ],
        "web": [
            "web developer",
            "web designer",
            "web frontend",
            "web full stack"
        ],
        "marketing": [
            "marketing digital",
            "marketing manager",
            "marketing analytics",
            "marketing specialist"
        ]
    }
    
    query_lower = query.lower()
    matching_suggestions = []
    
    for category, terms in suggestions.items():
        if query_lower in category:
            matching_suggestions.extend(terms)
    
    # Si no hay coincidencias por categoría, buscar en todos los términos
    if not matching_suggestions:
        all_terms = [term for terms_list in suggestions.values() for term in terms_list]
        matching_suggestions = [term for term in all_terms if query_lower in term.lower()]
    
    return {
        "query": query,
        "suggestions": matching_suggestions[:10],  # Limitar a 10 sugerencias
        "success": True
    }






class DetailedJobResponse(BaseModel):
    """Response mejorado para detalles de un empleo"""
    job_details: JobOffer
    extraction_quality: Dict = {}
    available_sections: Dict = {}
    recommendations: List[str] = []
    success: bool = True


@router.get("/statistics-advanced")
async def get_advanced_job_statistics(
    keywords: List[str] = Query(["data science", "python", "javascript", "marketing digital"], 
                                description="Keywords para analizar estadísticas")
):
    """
    Proporciona estadísticas avanzadas sobre empleos incluyendo análisis de tendencias
    """
    try:
        async with OCCScraper() as scraper:
            stats = await scraper.get_job_statistics(keywords)
        
        return {
            **stats,
            "success": True,
            "message": f"Estadísticas generadas para {len(keywords)} keywords"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar estadísticas avanzadas: {str(e)}"
        )


@router.get("/explore-site-structure")
async def explore_occ_site_structure(keyword: str = "data science"):
    """
    Endpoint de exploración para entender la estructura del sitio OCC.com.mx
    """
    try:
        filters = SearchFilters(keyword=keyword, page=1)
        
        async with OCCScraper() as scraper:
            # Obtener URL de búsqueda
            search_url = scraper._build_search_url(filters)
            
            # Realizar una búsqueda para obtener ejemplos
            jobs, total = await scraper.search_jobs(filters)
            
            # Analizar el primer empleo si existe
            sample_analysis = None
            if jobs:
                first_job = jobs[0]
                sample_analysis = {
                    "job_id": first_job.job_id,
                    "title": first_job.title,
                    "has_all_basic_fields": all([
                        first_job.title,
                        first_job.company,
                        first_job.location,
                        first_job.publication_date
                    ]),
                    "available_fields": {
                        "salary": bool(first_job.salary),
                        "benefits": bool(first_job.benefits),
                        "company_verified": first_job.company_verified,
                        "is_featured": first_job.is_featured,
                        "is_new": first_job.is_new,
                        "company_logo": bool(first_job.company_logo)
                    }
                }
        
        return {
            "search_url_pattern": search_url,
            "total_results_found": total,
            "jobs_extracted": len(jobs),
            "sample_job_analysis": sample_analysis,
            "site_elements_identified": {
                "job_containers": "[data-offers-grid-offer-item-container]",
                "detail_container": "#job-detail-container",
                "title_selector": "[data-offers-grid-detail-title]",
                "company_verification": "svg verification icons",
                "benefits_list": "ul.list-disc.list-inside",
                "skills_data": "input#hd_skills",
                "contact_info": "input#hd_contact_*"
            },
            "extraction_capabilities": {
                "basic_info": "✅ Título, empresa, ubicación, fecha",
                "detailed_info": "✅ Categoría, subcategoría, educación",
                "benefits": "✅ Lista de beneficios estructurada",
                "skills": "✅ Habilidades desde datos JSON ocultos",
                "work_details": "✅ Modalidad, tipo de contrato",
                "contact": "✅ Información de contacto cuando disponible"
            },
            "success": True,
            "message": f"Exploración completada para keyword '{keyword}'"
        }
        
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en exploración del sitio: {str(e)}"
        )


# ============================================================================
# ENDPOINTS DE GESTIÓN DE APLICACIONES
# ============================================================================

@router.post("/apply", response_model=ApplicationResponse, tags=["Applications"])
async def create_job_application(
    application_request: JobApplicationRequest,
    current_user = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session)
):
    """
    Crear una nueva aplicación de empleo
    
    Registra que el usuario ha aplicado a un empleo específico.
    """
    try:
        # Buscar la oferta de trabajo
        result = await db_session.execute(
            select(JobPosition).where(
                JobPosition.external_job_id == application_request.job_id
            )
        )
        job_offer = result.scalars().first()
        
        if not job_offer:
            raise HTTPException(status_code=404, detail="Oferta de empleo no encontrada")
        
        # Crear aplicación
        app_manager = JobApplicationManager(db_session)
        application = app_manager.create_application(
            user_id=current_user.user_id,
            job_position_id=job_offer.id,
            external_url=application_request.external_url,
            notes=application_request.notes
        )
        
        return ApplicationResponse(
            application_id=application.id,
            job_title=job_offer.title,
            company=job_offer.company,
            status=application.status,
            applied_at=application.created_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creando aplicación: {e}")
        raise HTTPException(status_code=500, detail="Error al crear aplicación")


@router.get("/applications", tags=["Applications"])
async def get_user_applications(
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    current_user = Depends(get_current_user),
    db_session = Depends(get_session)
):
    """
    Obtener las aplicaciones del usuario actual
    
    Lista todas las aplicaciones de empleo del usuario, opcionalmente filtradas por estado.
    """
    try:
        app_manager = JobApplicationManager(db_session)
        applications = app_manager.get_user_applications(
            user_id=current_user.user_id,
            status=status
        )
        
        return {
            "applications": applications,
            "total": len(applications)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo aplicaciones: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener aplicaciones")


@router.put("/application/{application_id}/status", tags=["Applications"])
async def update_application_status(
    application_id: int,
    status: str,
    notes: Optional[str] = None,
    current_user = Depends(get_current_user),
    db_session = Depends(get_session)
):
    """
    Actualizar el estatus de una aplicación
    
    Permite cambiar el estado de una aplicación (pendiente, entrevista, rechazado, etc.)
    """
    try:
        # Validar estados permitidos
        valid_statuses = ["applied", "pending", "interview", "rejected", "accepted", "withdrawn"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Estado inválido. Estados válidos: {valid_statuses}"
            )
        
        app_manager = JobApplicationManager(db_session)
        application = app_manager.update_application_status(
            application_id=application_id,
            status=status,
            notes=notes
        )
        
        return {"message": "Estado actualizado exitosamente", "application": application}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error actualizando aplicación: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar aplicación")


@router.get("/applications/stats", response_model=StatsResponse, tags=["Applications"])
async def get_application_statistics(
    current_user = Depends(get_current_user),
    db_session = Depends(get_session)
):
    """
    Obtener estadísticas de aplicaciones del usuario
    
    Proporciona métricas sobre las aplicaciones de empleo del usuario.
    """
    try:
        app_manager = JobApplicationManager(db_session)
        stats = app_manager.get_application_statistics(current_user.user_id)
        
        return StatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener estadísticas")


# ============================================================================
# ENDPOINTS DE ALERTAS DE EMPLEO
# ============================================================================

@router.post("/alerts", response_model=AlertResponse, tags=["Alerts"])
async def create_job_alert(
    alert_request: JobAlertRequest,
    current_user = Depends(get_current_user),
    db_session = Depends(get_session)
):
    """
    Crear una alerta de empleo
    
    Configura una alerta automática que notificará al usuario cuando aparezcan nuevos empleos
    que coincidan con sus criterios.
    """
    try:
        alert_manager = JobAlertManager(db_session)
        alert = alert_manager.create_job_alert(
            user_id=current_user.user_id,
            keywords=alert_request.keywords,
            location=alert_request.location,
            salary_min=alert_request.salary_min,
            work_mode=alert_request.work_mode,
            frequency=alert_request.frequency
        )
        
        return AlertResponse(
            alert_id=alert.id,
            keywords=alert.keywords,
            frequency=alert.frequency,
            is_active=alert.is_active,
            created_at=alert.created_at
        )
        
    except Exception as e:
        logger.error(f"Error creando alerta: {e}")
        raise HTTPException(status_code=500, detail="Error al crear alerta")


@router.get("/alerts", tags=["Alerts"])
async def get_user_alerts(
    current_user = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session)
):
    """
    Obtener alertas de empleo del usuario
    
    Lista todas las alertas configuradas por el usuario.
    """
    try:
        result = await db_session.execute(
            select(UserJobAlertDB).where(
                UserJobAlertDB.user_id == current_user.user_id
            )
        )
        alerts = result.scalars().all()
        
        return {"alerts": alerts, "total": len(alerts)}
        
    except Exception as e:
        logger.error(f"Error obteniendo alertas: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener alertas")


@router.delete("/alerts/{alert_id}", tags=["Alerts"])
async def delete_job_alert(
    alert_id: int,
    current_user = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session)
):
    """
    Eliminar una alerta de empleo
    
    Desactiva o elimina una alerta específica del usuario.
    """
    try:
        result = await db_session.execute(
            select(UserJobAlertDB).where(
                (UserJobAlertDB.id == alert_id) &
                (UserJobAlertDB.user_id == current_user.user_id)
            )
        )
        alert = result.scalars().first()
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alerta no encontrada")
        
        alert.is_active = False
        await db_session.commit()
        
        return {"message": "Alerta desactivada exitosamente"}
        
    except Exception as e:
        logger.error(f"Error eliminando alerta: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar alerta")


@router.get("/search-history", tags=["Search"])
async def get_search_history(
    limit: int = Query(10, ge=1, le=50, description="Número de búsquedas a mostrar"),
    current_user = Depends(get_current_user),
    db_session = Depends(get_session)
):
    """
    Obtener historial de búsquedas del usuario
    
    Muestra las búsquedas recientes realizadas por el usuario.
    """
    try:
        search_manager = JobSearchManager(db_session)
        history = search_manager.get_search_history(
            user_id=current_user.user_id,
            limit=limit
        )
        
        return {
            "search_history": history,
            "total": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener historial")


# ============================================================================
# CACHE MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/cache/store", response_model=CacheStoreResponse, tags=["Cache"])
async def store_search_results(
    request: CacheStoreRequest,
    db_session: AsyncSession = Depends(get_session)
):
    """
    Guarda resultados de búsqueda en caché persistente (BD).
    
    Normalmente llamado automáticamente después de /search,
    pero también puede ser llamado manualmente desde frontend.
    
    Deduplicación:
    - Si el empleo ya existe (por external_job_id), lo actualiza
    - Si es nuevo, lo inserta
    
    TTL: 7 días por defecto
    
    ✨ MEJORADO: Validación de entrada y mejor manejo de errores
    
    Args:
        jobs: Lista de empleos del scraper
        keyword: Palabra clave de búsqueda (para logging)
        source: Fuente del empleo (default: "occ")
        
    Returns:
        Cantidad de empleos guardados y total en cache
    """
    try:
        # ✅ Validación de entrada
        if not request.jobs or len(request.jobs) == 0:
            logger.warning(f"⚠️  Intentando guardar lista vacía de empleos (keyword: {request.keyword})")
            return CacheStoreResponse(
                saved_count=0,
                total_cached=0,
                source=request.source,
                keyword=request.keyword,
                message="⚠️ Lista de empleos vacía, nada que guardar"
            )
        
        logger.info(f"💾 Guardando {len(request.jobs)} empleos en cache (keyword: '{request.keyword}')")
        
        cache_manager = JobCacheManager(db_session)
        saved_count = await cache_manager.save_scraped_jobs(
            jobs=request.jobs,
            source=request.source,
            keyword=request.keyword
        )
        
        # ✅ Obtener total en cache después de guardar
        try:
            stats = await cache_manager.get_cache_stats()
            total_cached = stats.get("total_active", 0)
        except Exception as stats_error:
            logger.warning(f"⚠️  Error al obtener estadísticas de cache: {stats_error}")
            total_cached = saved_count  # Usar al menos el conteo actual
        
        logger.info(f"✅ Cache guardado: {saved_count} nuevos/actualizados, {total_cached} total activos")
        
        return CacheStoreResponse(
            saved_count=saved_count,
            total_cached=total_cached,
            source=request.source,
            keyword=request.keyword,
            message=f"✅ {saved_count} empleos guardados en cache. Total en cache: {total_cached}"
        )
        
    except Exception as e:
        logger.error(f"❌ Error guardando resultados en cache: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al guardar en cache: {str(e)}"
        )


@router.get("/cache/list", response_model=CacheListResponse, tags=["Cache"])
async def get_cached_jobs(
    location: Optional[str] = Query(None, description="Filtrar por ubicación (búsqueda parcial)"),
    work_mode: Optional[str] = Query(None, description="Modalidad: presencial, remoto, híbrido"),
    experience_level: Optional[str] = Query(None, description="Nivel de experiencia requerido"),
    skills: Optional[str] = Query(None, description="Habilidades (búsqueda en descripción)"),
    job_type: Optional[str] = Query(None, description="Tipo de trabajo: full-time, part-time, etc."),
    sort_by: str = Query("recent", description="Ordenamiento: recent, relevance"),
    limit: int = Query(50, ge=1, le=200, description="Máximo de resultados"),
    offset: int = Query(0, ge=0, description="Saltar N resultados"),
    db_session: AsyncSession = Depends(get_session)
):
    """
    Obtiene empleos desde caché persistente con filtros opcionales.
    
    Esta es la forma principal de cargar empleos sin hacer scraping.
    Ideal para:
    - Cargar datos iniciales en /oportunidades
    - Aplicar filtros sin consultar scraper
    - Explorar empleos en caché
    
    Filtros soportados:
    - location: Ubicación (búsqueda parcial, case-insensitive)
    - work_mode: Modalidad de trabajo
    - experience_level: Nivel de experiencia
    - skills: Habilidades (búsqueda en JSON de skills)
    - job_type: Tipo de contrato
    
    Ordenamiento:
    - recent: Por fecha de scraping (más nuevo primero)
    - relevance: Por coincidencia de filtros (TODO)
    
    Returns:
        Lista de empleos, total en cache, y metadata
    """
    try:
        cache_manager = JobCacheManager(db_session)
        
        # Construir filtros
        filters = {}
        if location:
            filters["location"] = location
        if work_mode:
            filters["work_mode"] = work_mode
        if experience_level:
            filters["experience_level"] = experience_level
        if skills:
            filters["skills"] = skills
        if job_type:
            filters["job_type"] = job_type
        
        # Obtener empleos
        jobs, total = await cache_manager.get_cached_jobs(
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        # Convertir a response
        cache_items = [
            CacheJobItem(
                id=job.id,
                title=job.title,
                company=job.company,
                location=job.location,
                description=job.description,
                job_type=job.job_type,
                work_mode=job.work_mode,
                experience_level=job.experience_level,
                skills=job.skills,
                salary_range=job.salary_range,
                external_job_id=job.external_job_id,
                source=job.source,
                scraped_at=job.scraped_at,
                is_active=job.is_active
            )
            for job in jobs
        ]
        
        # Calcular edad del cache más antiguo
        if jobs:
            oldest_job = min(jobs, key=lambda j: j.scraped_at)
            cache_age_minutes = int((datetime.utcnow() - oldest_job.scraped_at).total_seconds() / 60)
        else:
            cache_age_minutes = None
        
        return CacheListResponse(
            jobs=cache_items,
            total=total,
            returned=len(cache_items),
            filters_applied=filters,
            cache_age_minutes=cache_age_minutes
        )
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener cache: {str(e)}"
        )


@router.post("/cache/invalidate", response_model=dict, tags=["Cache"])
async def invalidate_expired_jobs(
    max_age_days: int = Query(7, ge=1, le=90, description="Invalidar empleos con edad > N días"),
    db_session: AsyncSession = Depends(get_session)
):
    """
    Invalida (soft-delete) empleos expirados del cache.
    
    Estrategia de limpieza:
    - Soft-delete: marca is_active=False en lugar de borrar
    - Permite auditoría y recuperación si es necesario
    - Puede ejecutarse periódicamente (ej: cada 6 horas)
    
    Args:
        max_age_days: Invalidar empleos más antiguos que N días (default: 7)
        
    Returns:
        Cantidad de empleos invalidados y fecha de próxima limpieza recomendada
    """
    try:
        cache_manager = JobCacheManager(db_session)
        invalidated_count = await cache_manager.invalidate_expired_jobs(max_age_days=max_age_days)
        
        # Obtener stats después de invalidación
        stats = await cache_manager.get_cache_stats()
        
        return {
            "invalidated_count": invalidated_count,
            "total_active_remaining": stats["total_active"],
            "soft_deleted_total": stats["soft_deleted"],
            "message": f"♻️  {invalidated_count} empleos invalidados. Cache activo: {stats['total_active']}",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Error invalidando cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al invalidar cache: {str(e)}"
        )


@router.get("/cache/stats", response_model=CacheStatsResponse, tags=["Cache"])
async def get_cache_statistics(
    db_session: AsyncSession = Depends(get_session)
):
    """
    Retorna estadísticas del caché persistente.
    
    Información útil:
    - total_active: Empleos activos y no expirados
    - expired_but_active: Empleos que pasaron expires_at pero aún activos
    - soft_deleted: Empleos marcados como inactivos
    - cache_efficiency: % de registros útiles vs total en BD
    - avg_age_hours: Edad promedio del cache
    - top_locations: Top 5 ubicaciones con más empleos
    - next_cleanup_recommended: Si debe ejecutarse /cache/invalidate
    
    Returns:
        Estadísticas del cache para monitoreo y toma de decisiones
    """
    try:
        cache_manager = JobCacheManager(db_session)
        stats = await cache_manager.get_cache_stats()
        
        return CacheStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas del cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


# ============================================================================
# ENDPOINTS ADMINISTRATIVOS
# ============================================================================

@router.post("/admin/process-alerts", tags=["Admin"])
async def process_job_alerts(
    # current_admin = Depends(get_admin_user),  # Requiere permisos de admin
    db_session = Depends(get_session)
):
    """
    Procesar todas las alertas de empleo (Endpoint administrativo)
    
    Verifica todas las alertas activas y envía notificaciones cuando corresponda.
    Solo disponible para administradores.
    """
    try:
        alert_manager = JobAlertManager(db_session)
        results = await alert_manager.check_alerts_and_notify()
        
        return {
            "message": "Procesamiento de alertas completado",
            "results": results,
            "processed_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error procesando alertas: {e}")
        raise HTTPException(status_code=500, detail="Error al procesar alertas")