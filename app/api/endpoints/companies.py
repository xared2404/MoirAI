"""
Endpoints para gestión de empresas colaboradoras - CRUD completo (ASYNC)
Incluye operaciones para crear, leer, actualizar y eliminar empresas
considerando acceso seguro a datos de estudiantes y verificación
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import json
from datetime import datetime

from app.core.database import get_session
from app.models import Company, Student, AuditLog
from app.schemas import (
    CompanyBase, CompanyCreate, CompanyProfile, UserContext, BaseResponse,
    StudentPublic
)
from app.middleware.auth import AuthService
from app.core.config import settings

router = APIRouter(prefix="/companies", tags=["companies"])

# Constantes
VALID_SIZES = {"startup", "pequeña", "mediana", "grande"}


async def _log_audit_action(session: AsyncSession, action: str, resource: str, 
                     actor: UserContext, success: bool = True, 
                     details: str = None, error_message: str = None):
    """Helper para registrar acciones de auditoría de forma asincrónica"""
    audit_log = AuditLog(
        actor_role=actor.role,
        actor_id=str(actor.user_id) if actor.user_id else actor.email,
        action=action,
        resource=resource,
        success=success,
        details=details,
        error_message=error_message
    )
    session.add(audit_log)
    await session.commit()


def _convert_to_company_profile(company: Company) -> CompanyProfile:
    """Convierte modelo Company a CompanyProfile"""
    return CompanyProfile(
        id=company.id,
        name=company.name,
        role="company",  # ✅ INCLUIR role para que frontend siempre sepa el rol
        email=company.get_email(),  # ✅ DESENCRIPTAR email antes de retornar
        industry=company.industry,
        size=company.size,
        location=company.location,
        is_verified=company.is_verified,
        is_active=company.is_active,
        created_at=company.created_at
    )


# ============================================================================
# CREATE - Crear Empresa
# ============================================================================

@router.post("/", response_model=CompanyProfile, status_code=201)
async def create_company(
    company_data: CompanyCreate,
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Crear nueva empresa colaboradora.
    
    Campos requeridos:
    - name: Nombre de la empresa (1-100 caracteres)
    - email: Email corporativo (único)
    
    Campos opcionales:
    - industry: Sector industrial (max 50 caracteres)
    - size: Tamaño (startup, pequeña, mediana, grande)
    - location: Ubicación (max 100 caracteres)
    
    La empresa se crea con is_verified=False y requiere validación de admin.
    """
    # Verificar permisos: solo admin y empresas sin autenticación
    if current_user.role not in ["admin", "anonymous"] and current_user.role != "company":
        raise HTTPException(
            status_code=403,
            detail="Solo administradores y empresas pueden crear perfiles"
        )
    
    # Validar tamaño si se proporciona
    if company_data.size and company_data.size not in VALID_SIZES:
        raise HTTPException(
            status_code=400,
            detail=f"Size debe ser uno de: {', '.join(VALID_SIZES)}"
        )
    
    # Verificar email único
    existing = await session.execute(
        select(Company).where(Company.email == company_data.email)
    ).first()
    
    if existing:
        await _log_audit_action(
            session, "CREATE_COMPANY", f"email:{company_data.email}",
            current_user, success=False, error_message="Email duplicado"
        )
        raise HTTPException(
            status_code=409,
            detail="Ya existe una empresa registrada con ese email"
        )
    
    # Crear empresa
    company = Company(
        name=company_data.name,
        email=company_data.email,
        industry=company_data.industry,
        size=company_data.size,
        location=company_data.location,
        is_verified=False,  # Requiere verificación de admin
        is_active=True
    )
    
    try:
        session.add(company)
        await session.commit()
        session.refresh(company)
        
        await _log_audit_action(
            session, "CREATE_COMPANY", f"company_id:{company.id}",
            current_user, details=f"Empresa {company.name} creada (email: {company.email})"
        )
        
        return _convert_to_company_profile(company)
        
    except Exception as e:
        session.rollback()
        await _log_audit_action(
            session, "CREATE_COMPANY", f"email:{company_data.email}",
            current_user, success=False, error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error creando empresa: {str(e)}"
        )


# ============================================================================
# READ - Listar Empresas
# ============================================================================

@router.get("/", response_model=dict)
async def list_companies(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(20, ge=1, le=100, description="Límite de resultados"),
    industry: Optional[str] = Query(None, description="Filtrar por sector"),
    size: Optional[str] = Query(None, description="Filtrar por tamaño"),
    location: Optional[str] = Query(None, description="Filtrar por ubicación"),
    is_verified: Optional[bool] = Query(None, description="Filtrar por verificación"),
    sort_by: str = Query("name", description="Ordenar por: name, created_at"),
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Listar empresas con filtros y paginación.
    
    Control de acceso:
    - Admin: ve todas las empresas (activas + inactivas)
    - Company: solo empresas verificadas y activas
    - Student: solo empresas verificadas y activas
    - Anonymous: no tiene acceso
    """
    # Control de acceso: solo usuarios autenticados
    if current_user.role == "anonymous":
        raise HTTPException(
            status_code=401,
            detail="Debe estar autenticado para listar empresas"
        )
    
    # Construir query base según rol
    query = select(Company)
    
    if current_user.role != "admin":
        # No-admins solo ven empresas verificadas y activas
        query = query.where(
            Company.is_verified == True,
            Company.is_active == True
        )
    
    # Aplicar filtros
    if industry:
        query = query.where(Company.industry == industry)
    
    if size:
        if size not in VALID_SIZES:
            raise HTTPException(
                status_code=400,
                detail=f"Size debe ser uno de: {', '.join(VALID_SIZES)}"
            )
        query = query.where(Company.size == size)
    
    if location:
        query = query.where(Company.location.ilike(f"%{location}%"))
    
    if is_verified is not None:
        query = query.where(Company.is_verified == is_verified)
    
    # Ordenamiento
    if sort_by == "created_at":
        query = query.order_by(Company.created_at.desc())
    else:  # default: name
        query = query.order_by(Company.name)
    
    # Obtener total
    total = await session.execute(select(func.count(Company.id)).select_from(Company)).scalar_one()
    
    # Aplicar paginación
    companies = await session.execute(query.offset(skip).limit(limit)).scalars().all()
    
    # Convertir a perfiles
    data = [_convert_to_company_profile(c) for c in companies]
    
    await _log_audit_action(
        session, "LIST_COMPANIES", "companies",
        current_user, details=f"Listar empresas (skip={skip}, limit={limit})"
    )
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": data
    }


# ============================================================================
# ✅ NUEVO ENDPOINT CRÍTICO: GET /me
# Obtiene el perfil COMPLETO de la empresa autenticada desde BD
# Usado por frontend para sincronización de datos
# ============================================================================

@router.get("/me", response_model=CompanyProfile)
async def get_my_company_profile(
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    ✅ ENDPOINT CRÍTICO: Obtener perfil COMPLETO de la empresa autenticada
    
    Este es el endpoint que el frontend DEBE usar para obtener datos frescos de BD.
    
    Características:
    - ✅ No requiere parámetro de ID (usa usuario autenticado)
    - ✅ Retorna CompanyProfile completo
    - ✅ Sincronización de datos del usuario
    - ✅ Recuperación de datos si localStorage fue borrado
    
    Retorna: CompanyProfile con TODOS los campos:
    {
        "id": 1,
        "name": "Tech Solutions",
        "email": "contact@techsolutions.com",
        "industry": "Tecnología",
        "size": "mediana",
        "location": "México DF",
        "is_verified": true,
        "is_active": true,
        "created_at": "2025-11-19T10:30:00"
    }
    """
    try:
        # 🔍 DEBUGGING: Log detallado de la request
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 GET /me: current_user.role={current_user.role}, user_id={current_user.user_id}")
        
        # Verificar que es empresa
        if current_user.role != "company":
            logger.warning(f"⚠️  Acceso denegado: role={current_user.role} != 'company'")
            raise HTTPException(
                status_code=403,
                detail="Solo empresas pueden acceder a este endpoint"
            )
        
        # Buscar empresa por su ID
        logger.info(f"🔍 Buscando company con ID={current_user.user_id}")
        company = await session.get(Company, current_user.user_id)
        
        if not company:
            logger.error(f"❌ Empresa no encontrada: ID={current_user.user_id}")
            await _log_audit_action(
                session, "GET_PROFILE_ME", f"user_id:{current_user.user_id}",
                current_user, success=False, error_message="Empresa no encontrada"
            )
            raise HTTPException(
                status_code=404,
                detail="Empresa no encontrada"
            )
        
        logger.info(f"✅ Company encontrada: ID={company.id}, name={company.name}")
        
        # Convertir a profile
        logger.info(f"🔄 Convirtiendo a CompanyProfile...")
        profile = _convert_to_company_profile(company)
        logger.info(f"✅ CompanyProfile convertido exitosamente")
        
        await _log_audit_action(
            session, "GET_PROFILE_ME", f"company_id:{company.id}",
            current_user, details="Perfil completo de la empresa autenticada"
        )
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Error en GET /me: {type(e).__name__}: {str(e)}", exc_info=True)
        await _log_audit_action(
            session, "GET_PROFILE_ME", f"user_id:{current_user.user_id}",
            current_user, success=False, error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================================================
# READ - Obtener Empresa Específica
# ============================================================================

@router.get("/{company_id}", response_model=CompanyProfile)
async def get_company(
    company_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Obtener detalles de una empresa específica.
    
    Control de acceso:
    - Admin: acceso completo a cualquier empresa
    - Owner (company): acceso a su propia empresa
    - Company (otro): solo si está verificada
    - Student: solo si está verificada
    - Anonymous: no tiene acceso
    """
    company = await session.execute(
        select(Company).where(Company.id == company_id)
    ).first()
    
    if not company:
        await _log_audit_action(
            session, "GET_COMPANY", f"company_id:{company_id}",
            current_user, success=False, error_message="Empresa no encontrada"
        )
        raise HTTPException(
            status_code=404,
            detail="Empresa no encontrada"
        )
    
    # Control de acceso
    if current_user.role == "anonymous":
        raise HTTPException(
            status_code=401,
            detail="Debe estar autenticado para ver empresas"
        )
    
    if current_user.role not in ["admin"] and not company.is_active:
        raise HTTPException(
            status_code=404,
            detail="Empresa no disponible"
        )
    
    if current_user.role == "company" and current_user.user_id != company_id:
        # Company puede ver solo si la empresa está verificada
        if not company.is_verified:
            raise HTTPException(
                status_code=403,
                detail="Empresa no verificada"
            )
    
    await _log_audit_action(
        session, "GET_COMPANY", f"company_id:{company_id}",
        current_user, details=f"Obtener empresa: {company.name}"
    )
    
    return _convert_to_company_profile(company)


# ============================================================================
# READ - Buscar Candidatos Estudiantes
# ============================================================================

@router.get("/{company_id}/search-students", response_model=dict)
async def search_students(
    company_id: int,
    skills: Optional[List[str]] = Query(None, description="Habilidades técnicas"),
    soft_skills: Optional[List[str]] = Query(None, description="Habilidades blandas"),
    location: Optional[str] = Query(None, description="Ubicación"),
    program: Optional[str] = Query(None, description="Programa académico"),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(20, ge=1, le=100, description="Límite de resultados"),
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Buscar candidatos (estudiantes) que coincidan con criterios específicos.
    
    REQUISITO: La empresa DEBE estar verificada (is_verified=True)
    
    Parámetros de búsqueda (todos opcionales):
    - skills: List de habilidades técnicas
    - soft_skills: List de habilidades blandas
    - location: Ubicación del estudiante
    - program: Programa académico
    - skip/limit: Paginación
    
    Control de acceso:
    - Solo empresas verificadas pueden buscar
    - Solo empresas pueden acceder a este endpoint
    - Admin puede buscar desde cualquier empresa
    """
    # Verificar que el usuario es empresa o admin
    if current_user.role not in ["company", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Solo empresas verificadas pueden buscar candidatos"
        )
    
    # Obtener la empresa
    company = await session.execute(
        select(Company).where(Company.id == company_id)
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=404,
            detail="Empresa no encontrada"
        )
    
    # Verificar que la empresa está verificada
    if not company.is_verified:
        await _log_audit_action(
            session, "SEARCH_STUDENTS", f"company_id:{company_id}",
            current_user, success=False, error_message="Empresa no verificada"
        )
        raise HTTPException(
            status_code=403,
            detail="La empresa debe estar verificada para buscar candidatos"
        )
    
    # Verificar ownership (si no es admin, debe ser la propia empresa)
    if current_user.role == "company" and current_user.user_id != company_id:
        raise HTTPException(
            status_code=403,
            detail="Solo puedes buscar desde tu propia empresa"
        )
    
    # Construir query de búsqueda
    query = select(Student).where(Student.is_active == True)
    
    # Filtrar por habilidades técnicas (búsqueda en JSON)
    if skills:
        for skill in skills:
            query = query.where(Student.skills.ilike(f"%{skill}%"))
    
    # Filtrar por habilidades blandas (búsqueda en JSON)
    if soft_skills:
        for soft_skill in soft_skills:
            query = query.where(Student.soft_skills.ilike(f"%{soft_skill}%"))
    
    # Filtrar por ubicación
    if location:
        # Nota: En el modelo actual, location no está en Student
        # Se podría agregar en el futuro
        pass
    
    # Filtrar por programa
    if program:
        query = query.where(Student.program == program)
    
    # Obtener total
    total = await session.execute(select(func.count(Student.id)).select_from(Student)).scalar_one()
    
    # Aplicar paginación
    students = await session.execute(query.offset(skip).limit(limit)).scalars().all()
    
    # Convertir a StudentPublic (información pública)
    data = []
    for student in students:
        data.append({
            "id": student.id,
            "name": student.name,
            "program": student.program,
            "skills": json.loads(student.skills or "[]"),
            "soft_skills": json.loads(student.soft_skills or "[]"),
            "projects": json.loads(student.projects or "[]"),
        })
    
    await _log_audit_action(
        session, "SEARCH_STUDENTS", f"company_id:{company_id}",
        current_user, details=f"Búsqueda de estudiantes (skills={skills}, found={len(data)})"
    )
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": data
    }


# ============================================================================
# UPDATE - Actualizar Empresa
# ============================================================================

@router.put("/{company_id}", response_model=CompanyProfile)
async def update_company(
    company_id: int,
    company_data: CompanyCreate,
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Actualizar datos de una empresa.
    
    Campos actualizables:
    - name, industry, size, location
    
    Campos NO actualizables:
    - email (inmutable para auditoría)
    - is_verified (usar endpoint /verify)
    - is_active (usar endpoint /activate)
    
    Control de acceso:
    - Owner (company): puede actualizar su propia empresa
    - Admin: puede actualizar cualquier empresa
    """
    company = await session.execute(
        select(Company).where(Company.id == company_id)
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=404,
            detail="Empresa no encontrada"
        )
    
    # Control de acceso: owner o admin
    if current_user.role == "company" and current_user.user_id != company_id:
        raise HTTPException(
            status_code=403,
            detail="Solo puedes actualizar tu propia empresa"
        )
    
    if current_user.role not in ["company", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para actualizar empresas"
        )
    
    # Validar tamaño si se proporciona
    if company_data.size and company_data.size not in VALID_SIZES:
        raise HTTPException(
            status_code=400,
            detail=f"Size debe ser uno de: {', '.join(VALID_SIZES)}"
        )
    
    # Actualizar campos
    try:
        company.name = company_data.name
        company.industry = company_data.industry
        company.size = company_data.size
        company.location = company_data.location
        company.updated_at = datetime.utcnow()
        
        session.add(company)
        await session.commit()
        session.refresh(company)
        
        await _log_audit_action(
            session, "UPDATE_COMPANY", f"company_id:{company.id}",
            current_user, details=f"Empresa {company.name} actualizada"
        )
        
        return _convert_to_company_profile(company)
        
    except Exception as e:
        session.rollback()
        await _log_audit_action(
            session, "UPDATE_COMPANY", f"company_id:{company_id}",
            current_user, success=False, error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando empresa: {str(e)}"
        )


# ============================================================================
# PATCH - Verificar Empresa (Admin Only)
# ============================================================================

@router.patch("/{company_id}/verify", response_model=BaseResponse)
async def verify_company(
    company_id: int,
    is_verified: bool,
    reason: Optional[str] = Query(None, max_length=500),
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Verificar o rechazar empresa (SOLO ADMIN).
    
    Parámetros:
    - is_verified: true para verificar, false para rechazar
    - reason: Razón del rechazo (opcional)
    
    Solo administradores pueden ejecutar esta operación.
    """
    # Verificar que es admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden verificar empresas"
        )
    
    company = await session.execute(
        select(Company).where(Company.id == company_id)
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=404,
            detail="Empresa no encontrada"
        )
    
    try:
        company.is_verified = is_verified
        company.updated_at = datetime.utcnow()
        
        session.add(company)
        await session.commit()
        session.refresh(company)
        
        await _log_audit_action(
            session, "VERIFY_COMPANY", f"company_id:{company.id}",
            current_user, details=f"Empresa {company.name} verificada: {is_verified}, reason: {reason}"
        )
        
        return BaseResponse(
            success=True,
            message=f"Empresa {'verificada' if is_verified else 'rechazada'} exitosamente"
        )
        
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error verificando empresa: {str(e)}"
        )


# ============================================================================
# PATCH - Activar/Desactivar Empresa
# ============================================================================

@router.patch("/{company_id}/activate", response_model=BaseResponse)
async def activate_company(
    company_id: int,
    is_active: bool,
    reason: Optional[str] = Query(None, max_length=500),
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Activar o desactivar empresa (soft delete).
    
    Parámetros:
    - is_active: true para activar, false para desactivar
    - reason: Razón de desactivación (opcional)
    
    Control de acceso:
    - Owner: puede desactivar su propia empresa
    - Admin: puede activar/desactivar cualquier empresa
    """
    company = await session.execute(
        select(Company).where(Company.id == company_id)
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=404,
            detail="Empresa no encontrada"
        )
    
    # Control de acceso
    if current_user.role == "company" and current_user.user_id != company_id:
        raise HTTPException(
            status_code=403,
            detail="Solo puedes activar/desactivar tu propia empresa"
        )
    
    if current_user.role not in ["company", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para activar/desactivar empresas"
        )
    
    try:
        company.is_active = is_active
        company.updated_at = datetime.utcnow()
        
        session.add(company)
        await session.commit()
        session.refresh(company)
        
        await _log_audit_action(
            session, "ACTIVATE_COMPANY", f"company_id:{company.id}",
            current_user, details=f"Empresa {company.name} {'activada' if is_active else 'desactivada'}, reason: {reason}"
        )
        
        return BaseResponse(
            success=True,
            message=f"Empresa {'activada' if is_active else 'desactivada'} exitosamente"
        )
        
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error activando/desactivando empresa: {str(e)}"
        )


# ============================================================================
# DELETE - Eliminar Empresa
# ============================================================================

@router.delete("/{company_id}", response_model=BaseResponse)
async def delete_company(
    company_id: int,
    permanently: bool = Query(False, description="Hard delete (admin only)"),
    reason: Optional[str] = Query(None, max_length=500),
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Eliminar empresa (soft delete por defecto).
    
    Parámetros:
    - permanently: true para hard delete (SOLO ADMIN), false para soft delete (default)
    - reason: Razón de eliminación (requerida para hard delete)
    
    Comportamientos:
    - Soft delete: Marca como inactiva (reversible)
    - Hard delete: Elimina físicamente (solo admin, con razón)
    
    Control de acceso:
    - Owner: puede hacer soft delete de su empresa
    - Admin: puede hacer soft o hard delete
    """
    company = await session.execute(
        select(Company).where(Company.id == company_id)
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=404,
            detail="Empresa no encontrada"
        )
    
    # Control de acceso
    if current_user.role == "company" and current_user.user_id != company_id:
        raise HTTPException(
            status_code=403,
            detail="Solo puedes eliminar tu propia empresa"
        )
    
    if current_user.role not in ["company", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para eliminar empresas"
        )
    
    # Hard delete solo para admin
    if permanently and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden hacer eliminación permanente"
        )
    
    # Razón requerida para hard delete
    if permanently and not reason:
        raise HTTPException(
            status_code=422,
            detail="Se requiere razón para eliminación permanente"
        )
    
    try:
        if permanently:
            # Hard delete (eliminación física)
            await session.delete(company)
            await session.commit()
            
            await _log_audit_action(
                session, "DELETE_COMPANY_HARD", f"company_id:{company_id}",
                current_user, details=f"Empresa {company.name} eliminada permanentemente, reason: {reason}"
            )
            
            return BaseResponse(
                success=True,
                message="Empresa eliminada permanentemente"
            )
        else:
            # Soft delete (cambiar a inactiva)
            company.is_active = False
            company.updated_at = datetime.utcnow()
            
            session.add(company)
            await session.commit()
            session.refresh(company)
            
            await _log_audit_action(
                session, "DELETE_COMPANY_SOFT", f"company_id:{company_id}",
                current_user, details=f"Empresa {company.name} desactivada (soft delete), reason: {reason}"
            )
            
            return BaseResponse(
                success=True,
                message="Empresa desactivada (puede ser reactivada)"
            )
        
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando empresa: {str(e)}"
        )


# ============================================================================
# PHASE 2: NEW COMPANY ENDPOINTS
# ============================================================================

@router.get("/posted", response_model=List[dict])
async def get_company_posted_jobs(
    offset: int = Query(0),
    limit: int = Query(20),
    current_user: UserContext = Depends(AuthService.get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Obtener todos los empleos publicados por la empresa actual
    
    Parámetros:
    - offset: Número de registros a saltar (default: 0)
    - limit: Número de resultados por página (default: 20)
    
    Retorna:
    - Lista de empleos publicados por la empresa
    - Incluye cantidad de aplicantes y vistas
    - Ordenado por fecha de creación descendente
    """
    try:
        # Verificar que es empresa
        if current_user.role != "company":
            raise HTTPException(
                status_code=403,
                detail="Solo empresas pueden ver sus empleos publicados"
            )
        
        # Buscar empleos de la empresa
        from app.models import JobPosition
        from app.models import JobApplicationDB
        
        jobs = await session.execute(
            select(JobPosition)
            .where(JobPosition.company_id == current_user.user_id)
            .order_by(JobPosition.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        
        # Enriquecer con estadísticas
        result = []
        for job in jobs:
            applicant_count = await session.execute(
                select(func.count(JobApplicationDB.id))
                .where(JobApplicationDB.job_position_id == job.id)
            ).one()
            
            result.append({
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "status": "open" if job.is_active else "closed",
                "applicant_count": applicant_count,
                "views_count": getattr(job, 'views_count', 0),
                "created_at": job.created_at,
                "expires_at": job.expires_at
            })
        
        await _log_audit_action(
            session, "GET_COMPANY_JOBS", f"company_id:{current_user.user_id}",
            current_user, details=f"Obtenidos {len(result)} empleos publicados"
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting company jobs: {e}")
        await _log_audit_action(
            session, "GET_COMPANY_JOBS", f"company_id:{current_user.user_id}",
            current_user, success=False, error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create", response_model=dict, status_code=201)
async def create_job_posting(
    job_data: dict,
    current_user: UserContext = Depends(AuthService.get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Crear nuevo empleo/vacante para la empresa
    
    Campos requeridos en job_data:
    - title: Título del puesto (str)
    - description: Descripción completa (str, min 10 caracteres)
    - location: Ubicación (str)
    
    Campos opcionales:
    - requirements: Requisitos técnicos (str)
    - salary_range: Rango salarial (str)
    - job_type: Tipo de trabajo (full-time, part-time, etc.)
    - work_mode: Modalidad (presencial, remoto, híbrido)
    - skills: Lista de habilidades requeridas (list)
    
    Retorna:
    - Empleo creado con ID y timestamps
    """
    try:
        # Verificar que es empresa
        if current_user.role != "company":
            raise HTTPException(
                status_code=403,
                detail="Solo empresas pueden crear empleos"
            )
        
        from app.models import JobPosition
        
        # Validar campos requeridos
        if not job_data.get("title"):
            raise HTTPException(status_code=400, detail="Campo 'title' es requerido")
        if not job_data.get("description"):
            raise HTTPException(status_code=400, detail="Campo 'description' es requerido")
        if len(job_data.get("description", "")) < 10:
            raise HTTPException(status_code=400, detail="La descripción debe tener al menos 10 caracteres")
        if not job_data.get("location"):
            raise HTTPException(status_code=400, detail="Campo 'location' es requerido")
        
        # Obtener empresa
        company = await session.get(Company, current_user.user_id)
        if not company:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        
        # Crear empleo
        job = JobPosition(
            title=job_data.get("title"),
            company=company.name,
            company_id=company.id,
            location=job_data.get("location"),
            description=job_data.get("description"),
            requirements=job_data.get("requirements"),
            salary_range=job_data.get("salary_range"),
            job_type=job_data.get("job_type", "full-time"),
            work_mode=job_data.get("work_mode"),
            skills=json.dumps(job_data.get("skills", [])),
            is_active=True,
            publication_date=datetime.utcnow(),
            source="internal"
        )
        
        session.add(job)
        await session.commit()
        session.refresh(job)
        
        await _log_audit_action(
            session, "CREATE_JOB", f"job_id:{job.id}",
            current_user, details=f"Empleo '{job.title}' creado exitosamente"
        )
        
        return {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "status": "open",
            "created_at": job.created_at,
            "message": "Empleo creado exitosamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating job: {e}")
        await _log_audit_action(
            session, "CREATE_JOB", f"company_id:{current_user.user_id}",
            current_user, success=False, error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/applicants", response_model=List[dict])
async def get_job_applicants(
    job_id: int,
    sort_by: str = Query("match_score"),
    current_user: UserContext = Depends(AuthService.get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Obtener todos los candidatos que han aplicado a un empleo
    
    Parámetros:
    - job_id: ID del empleo
    - sort_by: Campo para ordenar (match_score, date, name)
    
    Retorna:
    - Lista de candidatos con información personal y score de compatibilidad
    - Ordenado según parámetro sort_by
    """
    try:
        # Verificar que es empresa
        if current_user.role != "company":
            raise HTTPException(
                status_code=403,
                detail="Solo empresas pueden ver candidatos"
            )
        
        from app.models import JobPosition, JobApplicationDB
        
        # Verificar que el empleo pertenece a la empresa
        job = await session.get(JobPosition, job_id)
        if not job or job.company_id != current_user.user_id:
            raise HTTPException(status_code=404, detail="Empleo no encontrado")
        
        # Obtener aplicaciones
        applications = await session.execute(
            select(JobApplicationDB)
            .where(JobApplicationDB.job_position_id == job_id)
        ).all()
        
        # Enriquecer con información del candidato
        applicants = []
        for app in applications:
            student = await session.get(Student, app.user_id)
            if student:
                applicants.append({
                    "application_id": app.id,
                    "student_id": student.id,
                    "name": student.name,
                    "program": student.program,
                    "skills": json.loads(student.skills or "[]"),
                    "soft_skills": json.loads(student.soft_skills or "[]"),
                    "status": app.status,
                    "applied_date": app.application_date,
                    "match_score": getattr(app, 'match_score', 0)
                })
        
        # Ordenar según parámetro
        if sort_by == "date":
            applicants.sort(key=lambda x: x["applied_date"], reverse=True)
        elif sort_by == "name":
            applicants.sort(key=lambda x: x["name"])
        else:  # match_score
            applicants.sort(key=lambda x: x["match_score"], reverse=True)
        
        await _log_audit_action(
            session, "GET_JOB_APPLICANTS", f"job_id:{job_id}",
            current_user, details=f"Obtenidos {len(applicants)} candidatos"
        )
        
        return applicants
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting applicants: {e}")
        await _log_audit_action(
            session, "GET_JOB_APPLICANTS", f"job_id:{job_id}",
            current_user, success=False, error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{job_id}/applicants/{app_id}/status", response_model=BaseResponse)
async def update_application_status(
    job_id: int,
    app_id: int,
    status_data: dict,
    current_user: UserContext = Depends(AuthService.get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Actualizar el estado de una aplicación
    
    Parámetros:
    - job_id: ID del empleo
    - app_id: ID de la aplicación
    - status_data: {"status": "accepted" | "rejected" | "pending"}
    
    Retorna:
    - Confirmación de actualización
    """
    try:
        # Verificar que es empresa
        if current_user.role != "company":
            raise HTTPException(
                status_code=403,
                detail="Solo empresas pueden actualizar estados de aplicaciones"
            )
        
        from app.models import JobPosition, JobApplicationDB
        
        # Verificar que el empleo pertenece a la empresa
        job = await session.get(JobPosition, job_id)
        if not job or job.company_id != current_user.user_id:
            raise HTTPException(status_code=404, detail="Empleo no encontrado")
        
        # Buscar aplicación
        app = await session.get(JobApplicationDB, app_id)
        if not app or app.job_position_id != job_id:
            raise HTTPException(status_code=404, detail="Aplicación no encontrada")
        
        # Validar nuevo estado
        valid_statuses = ["pending", "accepted", "rejected", "withdrawn"]
        new_status = status_data.get("status")
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Estado debe ser uno de: {', '.join(valid_statuses)}"
            )
        
        # Actualizar estado
        app.status = new_status
        app.updated_at = datetime.utcnow()
        session.add(app)
        await session.commit()
        
        await _log_audit_action(
            session, "UPDATE_APPLICATION_STATUS", f"app_id:{app_id}",
            current_user, details=f"Estado actualizado a '{new_status}'"
        )
        
        return BaseResponse(
            success=True,
            message=f"Estado actualizado a '{new_status}' exitosamente"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating application status: {e}")
        await _log_audit_action(
            session, "UPDATE_APPLICATION_STATUS", f"app_id:{app_id}",
            current_user, success=False, error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
