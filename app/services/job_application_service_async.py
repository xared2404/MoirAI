"""
Servicio para gestionar aplicaciones de empleo y seguimiento de solicitudes
Versión asincrónica para FastAPI/PostgreSQL con asyncpg
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import asyncio
import logging
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from ..core.database import get_session
from ..models.job_scraping import (
    JobApplicationDB, 
    SearchQueryDB,
    SearchResultDB,
    UserJobAlertDB,
    ScrapingLogDB
)
from ..models import JobPosition  # Usar modelo unificado
from .occ_scraper_service import OCCScraper, SearchFilters, JobOffer

logger = logging.getLogger(__name__)


class JobApplicationManager:
    """Gestiona las aplicaciones de empleo de los usuarios (Async)"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def save_job_offer(self, job_offer: JobOffer) -> JobPosition:
        """
        Guarda una oferta de trabajo en la base de datos usando el modelo unificado.
        
        ✨ MEJORADO: Mapeo completo de todos los campos disponibles
        - Convierte listas (skills, benefits) a JSON
        - Llena TODOS los campos disponibles en JobPosition
        - Maneja actualización y creación de registros
        """
        try:
            # Verificar si la oferta ya existe (ASYNC)
            # ✅ Usar first() en lugar de scalar_one_or_none() para evitar errores si hay duplicados
            result = await self.db_session.execute(
                select(JobPosition).where(JobPosition.external_job_id == job_offer.job_id)
            )
            existing_job = result.scalars().first()
            
            if existing_job:
                # ✅ ACTUALIZAR oferta existente con TODOS los campos
                existing_job.title = job_offer.title or existing_job.title
                existing_job.company = job_offer.company or existing_job.company
                existing_job.location = job_offer.location or existing_job.location
                existing_job.description = job_offer.description or existing_job.description
                existing_job.salary_range = job_offer.salary or existing_job.salary_range
                
                # ✅ Convertir listas a JSON
                existing_job.skills = json.dumps(job_offer.skills) if job_offer.skills else None
                existing_job.benefits = json.dumps(job_offer.benefits) if job_offer.benefits else None
                existing_job.requirements = json.dumps(job_offer.requirements) if job_offer.requirements else None
                
                # ✅ Mapear TODOS los campos disponibles (requirements ya convertido arriba)
                if job_offer.full_description:
                    existing_job.requirements = job_offer.full_description
                existing_job.work_mode = job_offer.work_mode or existing_job.work_mode
                existing_job.experience_level = job_offer.experience_level or existing_job.experience_level
                existing_job.category = job_offer.category or existing_job.category
                existing_job.job_type = job_offer.job_type or existing_job.job_type
                existing_job.education_required = job_offer.education_required or existing_job.education_required
                existing_job.company_verified = job_offer.company_verified if job_offer.company_verified else existing_job.company_verified
                existing_job.company_logo = job_offer.company_logo or existing_job.company_logo
                
                # ✅ publication_date: puede ser ISO 8601, "Hace 5 días", o fecha formateada
                # La BD ahora acepta strings, así que guardamos tal cual
                existing_job.publication_date = job_offer.publication_date or existing_job.publication_date
                
                existing_job.is_featured = job_offer.is_featured if job_offer.is_featured else existing_job.is_featured
                existing_job.external_url = job_offer.url or existing_job.external_url
                
                # ✅ Metadatos de cache
                existing_job.source = "occ"
                existing_job.scraped_at = datetime.utcnow()
                existing_job.is_active = True
                existing_job.expires_at = datetime.utcnow() + timedelta(days=7)
                existing_job.updated_at = datetime.utcnow()
                
                self.db_session.add(existing_job)
                # ✅ NO hacer commit aquí, lo hace save_scraped_jobs()
                return existing_job
            
            # ✅ CREAR nueva oferta con TODOS los campos mapeados
            job_db = JobPosition(
                external_job_id=job_offer.job_id,
                external_url=job_offer.url,
                title=job_offer.title or "Sin título",
                company=job_offer.company or "Sin empresa",
                location=job_offer.location or "No especificada",
                description=job_offer.description or job_offer.full_description or "",
                
                # ✅ Convertir listas a JSON strings
                skills=json.dumps(job_offer.skills) if job_offer.skills else None,
                benefits=json.dumps(job_offer.benefits) if job_offer.benefits else None,
                
                # ✅ Mapear TODOS los campos disponibles
                # Si hay full_description, la usamos como requirements principal; sino, JSON de lista
                salary_range=job_offer.salary,
                requirements=(job_offer.full_description if job_offer.full_description 
                            else json.dumps(job_offer.requirements) if job_offer.requirements else None),
                work_mode=job_offer.work_mode,
                experience_level=job_offer.experience_level,
                category=job_offer.category,
                job_type=job_offer.job_type,
                education_required=job_offer.education_required,
                company_verified=job_offer.company_verified,
                company_logo=job_offer.company_logo,
                
                # ✅ publication_date: puede ser ISO 8601, "Hace 5 días", o fecha formateada
                # La BD ahora acepta strings, así que guardamos tal cual
                publication_date=job_offer.publication_date,
                is_featured=job_offer.is_featured,
                
                # ✅ Metadatos de cache
                source="occ",
                scraped_at=datetime.utcnow(),
                is_active=True,
                expires_at=datetime.utcnow() + timedelta(days=7),
            )
            
            self.db_session.add(job_db)
            # ✅ NO hacer commit aquí, lo hace save_scraped_jobs()
            return job_db
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"❌ Error al guardar oferta de trabajo {job_offer.job_id}: {e}")
            raise
    
    async def create_application(self, user_id: int, job_position_id: int, 
                          external_url: Optional[str] = None,
                          notes: Optional[str] = None) -> JobApplicationDB:
        """Crea una nueva aplicación de empleo"""
        try:
            # Verificar si ya existe una aplicación para este usuario y trabajo (ASYNC)
            result = await self.db_session.execute(
                select(JobApplicationDB).where(
                    JobApplicationDB.user_id == user_id,
                    JobApplicationDB.job_position_id == job_position_id
                )
            )
            existing_app = result.scalar_one_or_none()
            
            if existing_app:
                raise ValueError("Ya existe una aplicación para este empleo")
            
            application = JobApplicationDB(
                user_id=user_id,
                job_position_id=job_position_id,
                status="applied",
                external_application_url=external_url,
                notes=notes
            )
            
            self.db_session.add(application)
            await self.db_session.commit()
            await self.db_session.refresh(application)
            return application
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error al crear aplicación: {e}")
            raise
    
    async def update_application_status(self, application_id: int, 
                                status: str, notes: Optional[str] = None) -> JobApplicationDB:
        """Actualiza el estatus de una aplicación"""
        try:
            # En AsyncSession, usamos select + execute
            result = await self.db_session.execute(
                select(JobApplicationDB).where(JobApplicationDB.id == application_id)
            )
            application = result.scalar_one_or_none()
            
            if not application:
                raise ValueError("Aplicación no encontrada")
            
            application.status = status
            application.updated_at = datetime.utcnow()
            if notes:
                application.notes = notes
            
            self.db_session.add(application)
            await self.db_session.commit()
            await self.db_session.refresh(application)
            return application
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error al actualizar aplicación: {e}")
            raise
    
    async def get_user_applications(self, user_id: int, 
                            status: Optional[str] = None) -> List[JobApplicationDB]:
        """Obtiene las aplicaciones de un usuario"""
        try:
            query = select(JobApplicationDB).where(JobApplicationDB.user_id == user_id)
            
            if status:
                query = query.where(JobApplicationDB.status == status)
            
            query = query.order_by(JobApplicationDB.created_at.desc())
            
            result = await self.db_session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error al obtener aplicaciones del usuario: {e}")
            raise
    
    async def get_application_statistics(self, user_id: int) -> Dict:
        """Obtiene estadísticas de aplicaciones para un usuario"""
        try:
            # Total de aplicaciones (ASYNC)
            total_query = select(func.count(JobApplicationDB.id)).where(
                JobApplicationDB.user_id == user_id
            )
            result = await self.db_session.execute(total_query)
            total_applications = result.scalar() or 0
            
            # Aplicaciones por estatus (ASYNC)
            status_query = select(
                JobApplicationDB.status,
                func.count(JobApplicationDB.id)
            ).where(
                JobApplicationDB.user_id == user_id
            ).group_by(JobApplicationDB.status)
            
            result = await self.db_session.execute(status_query)
            status_counts = dict(result.all())
            
            # Aplicaciones recientes (último mes) (ASYNC)
            last_month = datetime.utcnow() - timedelta(days=30)
            recent_query = select(func.count(JobApplicationDB.id)).where(
                JobApplicationDB.user_id == user_id,
                JobApplicationDB.created_at >= last_month
            )
            result = await self.db_session.execute(recent_query)
            recent_applications = result.scalar() or 0
            
            return {
                "total_applications": total_applications,
                "status_breakdown": status_counts,
                "recent_applications": recent_applications,
                "success_rate": round(
                    (status_counts.get("accepted", 0) / max(total_applications, 1)) * 100, 2
                )
            }
            
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            raise


class JobSearchManager:
    """Gestiona búsquedas de empleo y resultados (Async)"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.app_manager = JobApplicationManager(db_session)
    
    async def perform_search_and_save(self, user_id: Optional[int], 
                                    filters: SearchFilters) -> Tuple[List[JobOffer], int]:
        """Realiza una búsqueda y guarda los resultados en la base de datos"""
        try:
            # Realizar búsqueda
            async with OCCScraper() as scraper:
                jobs, total_results = await scraper.search_jobs(filters)
            
            # Guardar consulta de búsqueda (ASYNC)
            search_query = SearchQueryDB(
                user_id=user_id,
                keyword=filters.keyword,
                location=filters.location,
                filters=filters.dict(exclude={'keyword', 'location'}),
                total_results=total_results
            )
            
            self.db_session.add(search_query)
            await self.db_session.commit()
            await self.db_session.refresh(search_query)
            
            # Guardar ofertas de trabajo y resultados (ASYNC)
            for position, job in enumerate(jobs, 1):
                # Guardar oferta
                job_db = await self.app_manager.save_job_offer(job)
                
                # Crear vinculación de resultado
                search_result = SearchResultDB(
                    search_query_id=search_query.id,
                    job_position_id=job_db.id,
                    position_in_results=position
                )
                
                self.db_session.add(search_result)
            
            await self.db_session.commit()
            
            # Log de la operación
            await self._log_scraping_operation(
                operation_type="search",
                search_keyword=filters.keyword,
                results_count=len(jobs),
                success=True
            )
            
            return jobs, total_results
            
        except Exception as e:
            await self.db_session.rollback()
            await self._log_scraping_operation(
                operation_type="search",
                search_keyword=filters.keyword,
                results_count=0,
                success=False,
                error_message=str(e)
            )
            logger.error(f"Error en búsqueda y guardado: {e}")
            raise
    
    async def get_search_history(self, user_id: int, limit: int = 10) -> List[SearchQueryDB]:
        """Obtiene el historial de búsquedas de un usuario"""
        try:
            query = select(SearchQueryDB).where(
                SearchQueryDB.user_id == user_id
            ).order_by(SearchQueryDB.created_at.desc()).limit(limit)
            
            result = await self.db_session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error al obtener historial de búsquedas: {e}")
            raise
    
    async def get_popular_searches(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """Obtiene las búsquedas más populares en los últimos días"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = select(
                SearchQueryDB.keyword,
                func.count(SearchQueryDB.id).label("search_count")
            ).where(
                SearchQueryDB.created_at >= start_date
            ).group_by(SearchQueryDB.keyword).order_by(
                func.count(SearchQueryDB.id).desc()
            ).limit(limit)
            
            result = await self.db_session.execute(query)
            results = result.all()
            
            return [
                {"keyword": keyword, "search_count": count}
                for keyword, count in results
            ]
            
        except Exception as e:
            logger.error(f"Error al obtener búsquedas populares: {e}")
            raise
    
    async def _log_scraping_operation(self, operation_type: str, 
                               search_keyword: Optional[str] = None,
                               results_count: int = 0,
                               success: bool = True,
                               error_message: Optional[str] = None):
        """Registra operaciones de scraping en el log"""
        try:
            log_entry = ScrapingLogDB(
                operation_type=operation_type,
                search_keyword=search_keyword,
                results_count=results_count,
                success=success,
                error_message=error_message
            )
            
            self.db_session.add(log_entry)
            await self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error al registrar log: {e}")


class JobAlertManager:
    """Gestiona alertas de empleo personalizadas (Async)"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.search_manager = JobSearchManager(db_session)
    
    async def create_job_alert(self, user_id: int, keywords: List[str],
                        location: Optional[str] = None,
                        salary_min: Optional[int] = None,
                        work_mode: Optional[str] = None,
                        frequency: str = "daily") -> UserJobAlertDB:
        """Crea una nueva alerta de empleo"""
        try:
            alert = UserJobAlertDB(
                user_id=user_id,
                keywords=keywords,
                location=location,
                salary_min=salary_min,
                work_mode=work_mode,
                frequency=frequency
            )
            
            self.db_session.add(alert)
            await self.db_session.commit()
            await self.db_session.refresh(alert)
            return alert
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error al crear alerta: {e}")
            raise
    
    async def check_alerts_and_notify(self) -> Dict[str, int]:
        """Verifica todas las alertas activas y genera notificaciones"""
        try:
            # Obtener alertas que necesitan verificación
            alerts = await self._get_alerts_to_check()
            
            notifications_sent = 0
            errors = 0
            
            for alert in alerts:
                try:
                    await self._process_single_alert(alert)
                    notifications_sent += 1
                except Exception as e:
                    logger.error(f"Error procesando alerta {alert.id}: {e}")
                    errors += 1
            
            return {
                "alerts_processed": len(alerts),
                "notifications_sent": notifications_sent,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error en verificación de alertas: {e}")
            raise
    
    async def _get_alerts_to_check(self) -> List[UserJobAlertDB]:
        """Obtiene alertas que necesitan ser verificadas"""
        now = datetime.utcnow()
        
        # Calcular tiempo mínimo desde última notificación según frecuencia
        daily_cutoff = now - timedelta(hours=24)
        weekly_cutoff = now - timedelta(days=7)
        
        query = select(UserJobAlertDB).where(
            UserJobAlertDB.is_active == True,
            (
                # Alertas diarias que no se han verificado en 24h
                (UserJobAlertDB.frequency == "daily") & 
                ((UserJobAlertDB.last_notification == None) | 
                 (UserJobAlertDB.last_notification <= daily_cutoff)) |
                
                # Alertas semanales que no se han verificado en 7 días
                (UserJobAlertDB.frequency == "weekly") & 
                ((UserJobAlertDB.last_notification == None) | 
                 (UserJobAlertDB.last_notification <= weekly_cutoff))
            )
        )
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def _process_single_alert(self, alert: UserJobAlertDB):
        """Procesa una alerta individual"""
        try:
            new_jobs = []
            
            # Buscar empleos para cada keyword
            for keyword in alert.keywords:
                filters = SearchFilters(
                    keyword=keyword,
                    location=alert.location,
                    work_mode=alert.work_mode,
                    sort_by="date",
                    page=1
                )
                
                jobs, _ = await self.search_manager.perform_search_and_save(
                    alert.user_id, filters
                )
                
                # Filtrar solo empleos nuevos (últimas 24h)
                recent_jobs = [
                    job for job in jobs 
                    if any(term in job.publication_date.lower() 
                          for term in ["hoy", "ayer"])
                ]
                
                new_jobs.extend(recent_jobs)
                
                # Delay para no sobrecargar el servidor
                await asyncio.sleep(2)
            
            # Actualizar última notificación (ASYNC)
            alert.last_notification = datetime.utcnow()
            self.db_session.add(alert)
            await self.db_session.commit()
            
            # Aquí podrías enviar notificación por email/push
            if new_jobs:
                logger.info(f"Enviando notificación a usuario {alert.user_id} con {len(new_jobs)} nuevos empleos")
            
        except Exception as e:
            logger.error(f"Error procesando alerta {alert.id}: {e}")
            raise


# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

class JobCacheManager:
    """
    Gestiona caché persistente de empleos scrapeados en la base de datos.
    
    Estrategia:
    - Guarda empleos scrapeados en tabla job_positions con source="occ"
    - Valida TTL (time-to-live) por edad de scraping
    - Deduplicación por external_job_id
    - Soft-delete por is_active flag en lugar de borrar
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.app_manager = JobApplicationManager(db_session)
        self.cache_ttl_days = 7  # 1 semana de vida máxima
    
    async def save_scraped_jobs(self, jobs: List[JobOffer], source: str = "occ", 
                         keyword: str = None) -> int:
        """
        Guarda lista de empleos scrapeados sin crear registros de búsqueda.
        
        Args:
            jobs: Lista de JobOffer del scraper
            source: Fuente del empleo (default: "occ")
            keyword: Palabra clave de búsqueda (solo para logging)
            
        Returns:
            Cantidad de empleos guardados o actualizados
        """
        try:
            saved_count = 0
            
            for job in jobs:
                try:
                    # Reutiliza save_job_offer() que ya hace deduplicación (ASYNC)
                    job_db = await self.app_manager.save_job_offer(job)
                    
                    # Actualizar campos de cache específicos
                    job_db.source = source
                    job_db.scraped_at = datetime.utcnow()
                    job_db.is_active = True
                    job_db.expires_at = datetime.utcnow() + timedelta(days=self.cache_ttl_days)
                    
                    self.db_session.add(job_db)
                    saved_count += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️  Error guardando job {job.job_id}: {e}")
                    continue
            
            # Commit una sola vez al final (ASYNC)
            try:
                await self.db_session.commit()
                logger.info(f"✅ {saved_count} empleos guardados en cache (keyword: {keyword})")
            except Exception as e:
                await self.db_session.rollback()
                logger.error(f"❌ Error al commitear empleos en cache: {e}")
                raise
            
            return saved_count
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error guardando empleos scrapeados: {e}")
            raise
    
    async def get_cached_jobs(self, filters: Optional[Dict] = None, 
                       limit: int = 100, offset: int = 0) -> Tuple[List[JobPosition], int]:
        """
        Obtiene empleos del cache con filtros aplicados.
        
        Filtros soportados:
        - location: Ubicación (búsqueda parcial)
        - work_mode: Modalidad (presencial, remoto, híbrido)
        - experience_level: Nivel de experiencia
        - skills: Habilidades requeridas (búsqueda en JSON)
        - job_type: Tipo de trabajo (full-time, part-time, etc.)
        
        Args:
            filters: Dict con filtros a aplicar (opcional)
            limit: Máximo número de resultados
            offset: Número de resultados a saltar
            
        Returns:
            Tupla (lista de empleos, total sin limit/offset)
        """
        try:
            filters = filters or {}
            
            # Query base: empleos activos, no expirados, de fuente OCC (ASYNC)
            query = select(JobPosition).where(
                JobPosition.source == "occ",
                JobPosition.is_active == True,
                JobPosition.expires_at > datetime.utcnow()
            )
            
            # Aplicar filtros
            if filters.get("location"):
                query = query.where(
                    JobPosition.location.ilike(f"%{filters['location']}%")
                )
            
            if filters.get("work_mode"):
                query = query.where(
                    JobPosition.work_mode == filters["work_mode"]
                )
            
            if filters.get("experience_level"):
                query = query.where(
                    JobPosition.experience_level == filters["experience_level"]
                )
            
            if filters.get("job_type"):
                query = query.where(
                    JobPosition.job_type == filters["job_type"]
                )
            
            if filters.get("skills"):
                # Búsqueda en JSON (simple búsqueda de texto)
                query = query.where(
                    JobPosition.skills.ilike(f"%{filters['skills']}%")
                )
            
            # Contar total sin paginación (ASYNC)
            count_query = select(func.count(JobPosition.id)).select_from(JobPosition).where(
                JobPosition.source == "occ",
                JobPosition.is_active == True,
                JobPosition.expires_at > datetime.utcnow()
            )
            
            # Aplicar los mismos filtros al conteo
            if filters.get("location"):
                count_query = count_query.where(
                    JobPosition.location.ilike(f"%{filters['location']}%")
                )
            if filters.get("work_mode"):
                count_query = count_query.where(JobPosition.work_mode == filters["work_mode"])
            if filters.get("experience_level"):
                count_query = count_query.where(JobPosition.experience_level == filters["experience_level"])
            if filters.get("job_type"):
                count_query = count_query.where(JobPosition.job_type == filters["job_type"])
            if filters.get("skills"):
                count_query = count_query.where(JobPosition.skills.ilike(f"%{filters['skills']}%"))
            
            result = await self.db_session.execute(count_query)
            total = result.scalar() or 0
            
            # Ordenar por más reciente primero
            query = query.order_by(JobPosition.scraped_at.desc())
            query = query.offset(offset).limit(limit)
            
            result = await self.db_session.execute(query)
            jobs = result.scalars().all()
            
            logger.info(f"📦 Cache query: total={total}, returned={len(jobs)}, filters={filters}")
            
            return jobs, total
            
        except Exception as e:
            logger.error(f"Error obteniendo empleos del cache: {e}")
            raise
    
    async def invalidate_expired_jobs(self, max_age_days: int = 7) -> int:
        """
        Marca como inactivos empleos más antiguos que max_age_days.
        
        Implementa soft-delete: solo marca is_active=False en lugar de borrar.
        
        Args:
            max_age_days: Edad máxima en días para considerar un empleo válido
            
        Returns:
            Cantidad de empleos invalidados
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
            
            # Query para encontrar empleos expirados (ASYNC)
            query = select(JobPosition).where(
                JobPosition.source == "occ",
                JobPosition.is_active == True,
                JobPosition.scraped_at < cutoff_date
            )
            
            result = await self.db_session.execute(query)
            expired_jobs = result.scalars().all()
            
            # Soft-delete: marcar como inactivos (ASYNC)
            for job in expired_jobs:
                job.is_active = False
                job.updated_at = datetime.utcnow()
                self.db_session.add(job)
            
            await self.db_session.commit()
            
            logger.info(f"♻️  {len(expired_jobs)} empleos invalidados (edad > {max_age_days} días)")
            
            return len(expired_jobs)
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error invalidando empleos expirados: {e}")
            raise
    
    async def get_cache_stats(self) -> Dict:
        """
        Retorna estadísticas del cache actual.
        
        Incluye:
        - Total de empleos en cache
        - Empleos expirados pero no invalidados
        - Distribución por fuente
        - Edad promedio
        - Próxima limpieza recomendada
        """
        try:
            # Total en cache (ASYNC)
            total_query = select(func.count(JobPosition.id)).where(
                JobPosition.is_active == True,
                JobPosition.source == "occ"
            )
            result = await self.db_session.execute(total_query)
            total_active = result.scalar() or 0
            
            # Empleos expirados (is_active=True pero expires_at < now) (ASYNC)
            expired_query = select(func.count(JobPosition.id)).where(
                JobPosition.is_active == True,
                JobPosition.source == "occ",
                JobPosition.expires_at <= datetime.utcnow()
            )
            result = await self.db_session.execute(expired_query)
            expired_count = result.scalar() or 0
            
            # Empleos inactivos (soft-deleted) (ASYNC)
            inactive_query = select(func.count(JobPosition.id)).where(
                JobPosition.is_active == False,
                JobPosition.source == "occ"
            )
            result = await self.db_session.execute(inactive_query)
            inactive_count = result.scalar() or 0
            
            # Distribución por location (top 5) (ASYNC)
            location_query = select(
                JobPosition.location,
                func.count(JobPosition.id).label("count")
            ).where(
                JobPosition.is_active == True,
                JobPosition.source == "occ"
            ).group_by(JobPosition.location).order_by(func.count(JobPosition.id).desc()).limit(5)
            
            result = await self.db_session.execute(location_query)
            top_locations = dict(result.all())
            
            # Edad promedio (ASYNC)
            avg_age_query = select(
                func.avg(func.extract('epoch', datetime.utcnow() - JobPosition.scraped_at))
            ).where(
                JobPosition.is_active == True,
                JobPosition.source == "occ"
            )
            result = await self.db_session.execute(avg_age_query)
            avg_age_seconds = result.scalar() or 0
            avg_age_hours = avg_age_seconds / 3600 if avg_age_seconds else 0
            
            return {
                "total_active": total_active,
                "expired_but_active": expired_count,
                "soft_deleted": inactive_count,
                "total_db_records": total_active + inactive_count,
                "avg_age_hours": round(avg_age_hours, 2),
                "top_locations": top_locations,
                "cache_efficiency": round((total_active / max(total_active + inactive_count, 1)) * 100, 2),
                "next_cleanup_recommended": expired_count > 100,  # Recomendar si hay >100 expirados
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de cache: {e}")
            raise
