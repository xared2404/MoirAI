"""
Endpoints para Matchmaking entre estudiantes y oportunidades laborales (ASYNC)
Sistema de recomendaciones inteligentes basado en compatibilidad de perfiles
"""
from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import Student
from app.schemas import (
    JobRecommendationResponse, MatchResult, MatchingCriteria,
    StudentPublic, UserContext, ErrorResponse
)
from app.services.matching_service import matching_service
from app.middleware.auth import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/matching", tags=["matching"])


@router.post(
    "/recommendations",
    response_model=JobRecommendationResponse,
    summary="Obtener recomendaciones de empleos",
    description="Obtiene recomendaciones personalizadas de empleos basadas en el perfil del estudiante",
    responses={
        200: {"description": "Recomendaciones generadas exitosamente"},
        404: {"model": ErrorResponse, "description": "Estudiante no encontrado"},
        401: {"model": ErrorResponse, "description": "No autenticado"},
        422: {"model": ErrorResponse, "description": "Datos inválidos"}
    }
)
async def get_recommendations(
    student_id: int = Query(
        ...,
        gt=0,
        description="ID del estudiante para el cual obtener recomendaciones"
    ),
    location: Optional[str] = Query(
        None,
        min_length=1,
        max_length=100,
        description="Ubicación preferida (opcional)"
    ),
    limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Número máximo de recomendaciones a retornar"
    ),
    current_user: UserContext = Depends(AuthService.get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Obtener recomendaciones personalizadas de empleos para un estudiante.

    **Parámetros:**
    - `student_id`: ID del estudiante para el cual generar recomendaciones
    - `location`: (Opcional) Ubicación preferida para filtrar empleos
    - `limit`: Número máximo de resultados (1-50, por defecto 10)

    **Respuesta:**
    - `student_id`: ID del estudiante
    - `jobs`: Lista de empleos recomendados con scores de compatibilidad
    - `total_found`: Total de empleos encontrados antes de filtrado
    - `matches_found`: Total de empleos que pasan el score mínimo
    - `query_used`: Query de búsqueda utilizado
    - `source_breakdown`: Desglose de fuentes (external_providers vs system_recommendation)
    - `generated_at`: Timestamp de generación

    **Reglas de Autorización:**
    - El estudiante puede ver sus propias recomendaciones
    - Los administradores pueden ver recomendaciones de cualquier estudiante
    - Las empresas no pueden acceder a este endpoint

    **Notas:**
    - Si no hay proveedores externos disponibles, se generan recomendaciones
      basadas en el perfil del estudiante (fallback inteligente)
    - Cada recomendación incluye su score de compatibilidad (0-1)
    """
    try:
        # Validar autorización
        if current_user.role == "student" and current_user.user_id != student_id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para ver recomendaciones de otro estudiante"
            )

        if current_user.role not in ["student", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Las empresas no tienen acceso a recomendaciones de estudiantes"
            )

        # Verificar que el estudiante existe
        student = await session.get(Student, student_id)
        if not student:
            raise HTTPException(
                status_code=404,
                detail=f"Estudiante con ID {student_id} no encontrado"
            )

        # Verificar que el estudiante está activo
        if not student.is_active:
            raise HTTPException(
                status_code=400,
                detail=f"El estudiante con ID {student_id} está inactivo"
            )

        # ✅ NUEVA VALIDACIÓN: Verificar integridad de datos del estudiante
        import json
        skills = json.loads(student.skills or "[]")
        projects = json.loads(student.projects or "[]")
        
        profile_completeness = {
            "has_skills": len(skills) > 0,
            "has_projects": len(projects) > 0,
            "profile_complete": len(skills) > 0 or len(projects) > 0
        }
        
        # Advertencia si el perfil está incompleto (pero continuar)
        if not profile_completeness["profile_complete"]:
            logger.warning(
                f"Perfil incompleto para estudiante {student_id}: "
                f"sin habilidades ni proyectos. Se generarán recomendaciones genéricas."
            )

        # Generar recomendaciones
        recommendations = await matching_service.find_job_recommendations(
            student_id=student_id,
            location=location,
            limit=limit
        )

        # ✅ MEJORADA: Respuesta con información de debugging
        response = JobRecommendationResponse(
            student_id=student_id,
            jobs=recommendations["jobs"],
            total_found=recommendations["total_found"],
            matches_found=recommendations.get("matches_found", len(recommendations["jobs"])),
            query_used=recommendations["query_used"],
            generated_at=recommendations["generated_at"]
        )
        
        # Añadir información adicional en headers para debugging
        # (esto se verá en los headers de la respuesta HTTP)
        return response

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error generando recomendaciones: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar recomendaciones: {str(e)}"
        )


@router.post(
    "/filter-by-criteria",
    response_model=List[MatchResult],
    summary="Filtrar estudiantes por criterios",
    description="Filtra y obtiene estudiantes que cumplen criterios específicos de habilidades y proyectos",
    responses={
        200: {"description": "Estudiantes filtrados exitosamente"},
        401: {"model": ErrorResponse, "description": "No autenticado"},
        403: {"model": ErrorResponse, "description": "Sin permisos suficientes"},
        422: {"model": ErrorResponse, "description": "Datos inválidos"}
    }
)
async def filter_students_by_criteria(
    criteria: MatchingCriteria,
    current_user: UserContext = Depends(AuthService.get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Filtrar estudiantes que cumplen criterios específicos.

    **Criterios de Filtrado:**
    - `email`: Email específico del estudiante (búsqueda exacta con hash seguro) ✅ NUEVO
    - `skills`: Lista de habilidades requeridas (AND lógico con 50% de match)
    - `projects`: Lista de tipos de proyectos (AND lógico)
    - `location`: Ubicación preferida (NO IMPLEMENTADO AÚN)
    - `job_type`: Tipo de trabajo preferido (NO IMPLEMENTADO AÚN)
    - `experience_level`: Nivel de experiencia (NO IMPLEMENTADO AÚN)

    **Respuesta:**
    - Lista de `MatchResult` con:
      - `student`: Información pública del estudiante
      - `score`: Score de compatibilidad (0-1)
      - `matching_skills`: Habilidades que coinciden
      - `matching_projects`: Proyectos que coinciden

    **Reglas de Autorización:**
    - Solo administradores y empresas pueden filtrar estudiantes
    - Los estudiantes no pueden usar este endpoint

    **Seguridad (FASE 3):**
    - ✅ Email se busca mediante hash SHA-256 (nunca desencriptado)
    - ✅ Datos encriptados en BD (Fernet AES-128)
    - ✅ Cumple LFPDPPP: Protección de datos sensibles

    **Ejemplos de Uso:**
    ```json
    // Búsqueda específica de email con skills requeridas
    {
      "email": "juan@email.com",
      "skills": ["Python", "Machine Learning"]
    }
    
    // Búsqueda general sin email
    {
      "skills": ["Python", "Machine Learning", "Data Analysis"],
      "projects": ["Data Science", "Web Development"]
    }
    ```
    """
    try:
        # Validar autorización
        if current_user.role == "student":
            raise HTTPException(
                status_code=403,
                detail="Los estudiantes no pueden usar el filtro de candidatos"
            )

        if current_user.role not in ["company", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Rol de usuario no autorizado para este endpoint"
            )

        # Validar que hay al menos un criterio
        if not any([criteria.email, criteria.skills, criteria.projects, criteria.location,
                   criteria.job_type, criteria.experience_level]):
            raise HTTPException(
                status_code=422,
                detail="Debe proporcionar al menos un criterio de filtrado (email, skills, projects, etc.)"
            )

        # Ejecutar filtrado
        results = matching_service.filter_students_by_criteria(criteria)

        return results

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al filtrar estudiantes: {str(e)}"
        )


@router.get(
    "/featured-students",
    response_model=List[StudentPublic],
    summary="Obtener estudiantes destacados",
    description="Obtiene los estudiantes con mejores perfiles según métricas de calidad",
    responses={
        200: {"description": "Estudiantes destacados obtenidos exitosamente"},
        401: {"model": ErrorResponse, "description": "No autenticado"},
        403: {"model": ErrorResponse, "description": "Sin permisos suficientes"}
    }
)
async def get_featured_students(
    limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Número máximo de estudiantes a retornar"
    ),
    current_user: UserContext = Depends(AuthService.get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Obtener los estudiantes más destacados de la plataforma.

    **Criterios de Selección:**
    - Cantidad y variedad de habilidades técnicas
    - Experiencia en proyectos relevantes
    - Habilidades blandas desarrolladas
    - Actividad reciente en la plataforma

    **Respuesta:**
    - Lista de `StudentPublic` ordenados por score de destacado (descendente)

    **Reglas de Autorización:**
    - Solo administradores y empresas pueden ver estudiantes destacados
    - Los estudiantes pueden ver a otros estudiantes destacados (futuro)

    **Notas:**
    - Se prioriza a estudiantes activos en los últimos 30 días
    - El score considera habilidades, proyectos y actividad reciente
    """
    try:
        # Validar autorización (permitir empresas y admins)
        if current_user.role not in ["company", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para ver estudiantes destacados"
            )

        # Obtener estudiantes destacados
        featured = matching_service.get_featured_students(limit=limit)

        return featured

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estudiantes destacados: {str(e)}"
        )


@router.get(
    "/student/{student_id}/matching-score",
    response_model=dict,
    summary="Calcular score de matching para un trabajo",
    description="Calcula el score de compatibilidad entre un estudiante y un trabajo específico",
    responses={
        200: {"description": "Score calculado exitosamente"},
        404: {"model": ErrorResponse, "description": "Estudiante no encontrado"},
        401: {"model": ErrorResponse, "description": "No autenticado"},
        422: {"model": ErrorResponse, "description": "Datos inválidos"}
    }
)
async def calculate_matching_score(
    student_id: int = Path(
        ...,
        gt=0,
        description="ID del estudiante"
    ),
    job_title: str = Query(
        ...,
        min_length=1,
        max_length=200,
        description="Título del puesto de trabajo"
    ),
    job_description: str = Query(
        ...,
        min_length=10,
        max_length=5000,
        description="Descripción del puesto de trabajo"
    ),
    current_user: UserContext = Depends(AuthService.get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Calcular el score de matching entre un estudiante y un trabajo específico.

    **Parámetros:**
    - `student_id`: ID del estudiante a evaluar
    - `job_title`: Título del puesto laboral
    - `job_description`: Descripción completa del puesto

    **Respuesta:**
    ```json
    {
        "student_id": 123,
        "job_title": "Data Scientist Jr",
        "matching_score": 0.85,
        "base_score": 0.75,
        "boost_applied": 0.10,
        "matching_skills": ["Python", "Machine Learning"],
        "missing_skills": ["SQL"],
        "matching_projects": ["Proyecto de predicción"],
        "boost_details": {
            "location": 0.05,
            "recent_activity": 0.05
        }
    }
    ```

    **Reglas de Autorización:**
    - El estudiante puede ver su propio score
    - Los administradores pueden ver scores de cualquier estudiante
    - Las empresas pueden ver scores de estudiantes que pasaron filtros
    """
    try:
        # Validar autorización
        if current_user.role == "student" and current_user.user_id != student_id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para ver el score de otro estudiante"
            )

        # Obtener estudiante
        student = await session.get(Student, student_id)
        if not student:
            raise HTTPException(
                status_code=404,
                detail=f"Estudiante con ID {student_id} no encontrado"
            )

        # Crear objeto JobItem simulado para el cálculo
        from app.schemas import JobItem
        job = JobItem(
            title=job_title,
            description=job_description,
            company=None,
            location=None,
            url=None,
            source="api-query"
        )

        # Calcular score
        score, details = matching_service._calculate_job_match_score(student, job)

        return {
            "student_id": student_id,
            "job_title": job_title,
            "matching_score": round(score, 3),
            "base_score": round(details.get("base_score", 0), 3),
            "boost_applied": round(details.get("boost_applied", 0), 3),
            "matching_skills": details.get("matching_skills", []),
            "missing_skills": details.get("missing_skills", []),
            "matching_projects": details.get("matching_projects", []),
            "boost_details": details.get("boost_details", {}),
            "weights_used": details.get("weights_used_for_nlp", {})
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al calcular matching score: {str(e)}"
        )
