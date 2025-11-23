"""
Endpoints para autenticación y gestión de usuarios
Incluye registro, login y gestión de API keys
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json
import hashlib
import logging

from app.core.database import get_session
from app.models import Student, Company, Admin, ApiKey, AuditLog
from app.schemas import (
    UserRegister, UserLoginResponse, ApiKeyCreate, ApiKeyCreatedResponse,
    ApiKeyResponse, ApiKeysList, UserContext, BaseResponse, LoginRequest
)
from app.services.api_key_service import api_key_service
from app.services.auth_service import auth_service
from app.middleware.auth import AuthService
from app.utils.encryption import EncryptionService

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger(__name__)

# ✅ Instancia global del servicio de encriptación (reutilizable)
_encryption_service = None

def get_encryption_service() -> EncryptionService:
    """Obtener instancia singleton del servicio de encriptación"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


def encrypt_email_generic(email: str) -> tuple[str, str]:
    """
    Encriptar email de forma genérica para cualquier rol
    
    Retorna:
        (email_encriptado, email_hash)
    """
    try:
        encryption_service = get_encryption_service()
        email_lower = email.lower().strip()
        encrypted_email = encryption_service.encrypt(email_lower)
        email_hash = hashlib.sha256(email_lower.encode()).hexdigest()
        return encrypted_email, email_hash
    except Exception as e:
        logger.error(f"Error encriptando email: {e}")
        # Fallback: devolver email sin encriptar pero con hash
        email_lower = email.lower().strip()
        email_hash = hashlib.sha256(email_lower.encode()).hexdigest()
        return email_lower, email_hash


@router.post("/register", response_model=UserLoginResponse, status_code=201)
async def register_user(user_data: UserRegister):
    """
    ✅ UNIFIED Registration: Funciona para STUDENT y COMPANY sin duplicación
    - Encriptación genérica del email para ambos roles
    - Crea su propia sesión para controlar el ciclo de vida completo
    """
    import secrets
    from app.core.database import async_session
    
    # ✅ Crear sesión propia para controlar el ciclo de vida
    async with async_session() as session:
        try:
            # Validar rol
            if user_data.role not in ["student", "company"]:
                raise HTTPException(
                    status_code=400,
                    detail="El rol debe ser 'student' o 'company'"
                )
            
            # ✅ Verificar si el email ya existe
            email_lower = user_data.email.lower().strip()
            email_hash = hashlib.sha256(email_lower.encode()).hexdigest()
            
            result = await session.execute(
                select(Student).where(Student.email_hash == email_hash)
            )
            if result.scalars().first():
                raise HTTPException(status_code=409, detail="Email ya registrado en estudiantes")
            
            result = await session.execute(
                select(Company).where(Company.email_hash == email_hash)
            )
            if result.scalars().first():
                raise HTTPException(status_code=409, detail="Email ya registrado en empresas")
            
            # ✅ Encriptar email (GENÉRICO para ambos roles)
            encrypted_email, email_hash_final = encrypt_email_generic(user_data.email)
            password_hash = hashlib.sha256(user_data.password.encode()).hexdigest()
            
            # ✅ Crear usuario (Student o Company)
            if user_data.role == "student":
                user = Student(
                    name=user_data.name,
                    email=encrypted_email,
                    email_hash=email_hash_final,
                    hashed_password=password_hash,
                    program=getattr(user_data, "program", None),
                    is_active=True
                )
            else:  # company
                user = Company(
                    name=user_data.name,
                    email=encrypted_email,
                    email_hash=email_hash_final,
                    hashed_password=password_hash,
                    industry=getattr(user_data, "industry", None),
                    size=getattr(user_data, "company_size", None),
                    location=getattr(user_data, "location", None),
                    is_active=True
                )
            
            session.add(user)
            await session.flush()  # Get user.id
            
            # ✅ Generar API key
            # Usar '-' como separador en lugar de '_' para evitar conflictos
            key_id = secrets.token_urlsafe(16).replace('_', '-')  # Asegurar que NO contiene '_'
            secret_part = secrets.token_urlsafe(32)
            full_key = f"{key_id}_{secret_part}"
            key_hash = hashlib.sha256(full_key.encode()).hexdigest()
            
            prefix_map = {"student": "stu_", "company": "com_", "admin": "adm_"}
            key_prefix = f"{prefix_map.get(user_data.role, 'key_')}{key_id[:8]}"
            
            api_key_record = ApiKey(
                key_id=key_id,
                key_hash=key_hash,
                key_prefix=key_prefix,
                user_id=user.id,
                user_type=user_data.role,
                user_email=email_lower,
                name=f"Registration API Key - {user_data.name}",
                scopes=json.dumps(["read", "write"]),
                is_active=True,
                expires_at=datetime.utcnow().replace(year=datetime.utcnow().year + 1)
            )
            session.add(api_key_record)
            
            # ✅ Commit final
            await session.commit()
            logger.info(f"✅ Registration completado: uid={user.id}, role={user_data.role}, key={key_id[:8]}...")
            
            return UserLoginResponse(
                user_id=user.id,
                name=user_data.name,
                email=user_data.email,
                role=user_data.role,
                api_key=full_key,
                key_id=key_id,
                expires_at=api_key_record.expires_at,
                scopes=json.loads(api_key_record.scopes)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error en registro: {type(e).__name__}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error en registro: {str(e)}"
            )


@router.post("/login", response_model=UserLoginResponse, status_code=200)
async def login_user(
    credentials: LoginRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Login con email y contraseña (ASYNC version).
    
    Valida las credenciales del usuario (student, company, o admin) 
    y retorna su API key principal.
    Lógica unificada para todos los roles (evita duplicación y conflictos).
    """
    try:
        # ✅ ASYNC: Buscar usuario en tabla de estudiantes
        email_hash = hashlib.sha256(credentials.email.lower().strip().encode()).hexdigest()
        result = await session.execute(
            select(Student).where(Student.email_hash == email_hash)
        )
        user = result.scalars().first()
        user_type = "student"
        
        # Si no es estudiante, buscar en empresas
        if not user:
            result = await session.execute(
                select(Company).where(Company.email_hash == email_hash)
            )
            user = result.scalars().first()
            user_type = "company"
        
        # Si no es empresa, buscar en admins
        if not user:
            result = await session.execute(
                select(Admin).where(Admin.email_hash == email_hash)
            )
            user = result.scalars().first()
            user_type = "admin"
        
        # Si no encontró usuario en ninguna tabla
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Email o contraseña incorrectos"
            )
        
        # ✅ Validar contraseña
        password_hash = hashlib.sha256(credentials.password.encode()).hexdigest()
        if password_hash != user.hashed_password:
            raise HTTPException(
                status_code=401,
                detail="Email o contraseña incorrectos"
            )
        
        # ✅ SOLUCIÓN DEFINITIVA: Generar NUEVA API key en cada login
        # Esto garantiza que siempre hay una clave disponible para retornar
        # Las claves antiguas siguen siendo válidas (no se revocan)
        import secrets
        
        try:
            # Generar componentes de la clave
            # Usar '-' como separador en lugar de '_' para evitar conflictos en parsing
            key_id = secrets.token_urlsafe(16).replace('_', '-')  # Asegurar que NO contiene '_'
            secret_part = secrets.token_urlsafe(32)
            full_key = f"{key_id}_{secret_part}"
            key_hash = hashlib.sha256(full_key.encode()).hexdigest()
            
            # Determinar prefijo según tipo de usuario
            prefix_map = {"student": "stu_", "company": "com_", "admin": "adm_"}
            prefix = prefix_map.get(user_type, "key_")
            key_prefix = f"{prefix}{key_id[:8]}"
            
            # Crear registro de API key
            api_key_record = ApiKey(
                key_id=key_id,
                key_hash=key_hash,
                key_prefix=key_prefix,
                user_id=user.id,
                user_type=user_type,
                user_email=credentials.email,
                name=f"Sesión - {user.name} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                description="API key generada en login",
                scopes=json.dumps(["read", "write"]),
                is_active=True,
                expires_at=datetime.utcnow().replace(year=datetime.utcnow().year + 1)
            )
            session.add(api_key_record)
            await session.commit()
            await session.refresh(api_key_record)
            
            # Retornar la clave completa
            api_key_to_return = full_key
            
        except Exception as e:
            print(f"⚠️ Error generando clave en login: {e}")
            # Fallback: buscar una clave existente
            result = await session.execute(
                select(ApiKey).where(
                    (ApiKey.user_id == user.id) & (ApiKey.user_type == user_type)
                ).order_by(ApiKey.created_at.desc())
            )
            api_key_record = result.scalars().first()
            
            if not api_key_record:
                raise HTTPException(
                    status_code=500,
                    detail="No se pudo generar clave de API"
                )
            
            api_key_to_return = ""  # No retornar clave antigua
        
        # Retornar confirmación de login con API key
        return UserLoginResponse(
            user_id=user.id,
            name=user.name,
            email=credentials.email,
            role=user_type,
            api_key=api_key_to_return,
            key_id=api_key_record.key_id,
            expires_at=api_key_record.expires_at,
            scopes=json.loads(api_key_record.scopes) if api_key_record.scopes else []
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en login: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Error en login: {str(e)}"
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error en login: {str(e)}"
        )


@router.post("/logout", response_model=BaseResponse, status_code=200)
async def logout_user(
    current_user: UserContext = Depends(AuthService.get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Logout del usuario.
    
    Registra el logout para auditoría. La API key sigue siendo válida
    para futuras sesiones (reutilizable).
    Lógica unificada para estudiantes y empresas.
    """
    if current_user.role == "anonymous":
        raise HTTPException(
            status_code=401,
            detail="No hay sesión activa"
        )
    
    try:
        # Registrar logout en auditoría usando servicio unificado
        await auth_service.log_audit(
            session=session,
            actor_role=current_user.role,
            actor_id=current_user.email or str(current_user.user_id),
            action="logout",
            resource="auth",
            success=True,
            details=f"Logout exitoso para {current_user.role}"
        )
        
        return BaseResponse(
            success=True,
            message="Sesión cerrada exitosamente"
        )
        
    except Exception as e:
        print(f"❌ Error en logout: {type(e).__name__}: {str(e)}")
        
        await auth_service.log_audit(
            session=session,
            actor_role=current_user.role,
            actor_id=current_user.email or str(current_user.user_id),
            action="logout",
            resource="auth",
            success=False,
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error en logout: {str(e)}"
        )


@router.get("/me", response_model=dict)
async def get_current_user_profile(
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    ✅ UNIFIED ENDPOINT: Obtener perfil del usuario autenticado
    
    Retorna:
    - StudentProfile si el usuario es un estudiante
    - CompanyProfile si el usuario es una empresa
    - AdminProfile si el usuario es admin
    
    SIEMPRE retorna el role en la response para que el frontend sepa qué es el usuario.
    """
    from app.models import Student, Company
    from app.schemas import StudentProfile, CompanyProfile
    
    if current_user.role == "anonymous":
        raise HTTPException(
            status_code=401,
            detail="Debe autenticarse para acceder a su perfil"
        )
    
    try:
        if current_user.role == "student":
            # Obtener perfil de estudiante
            student = await session.get(Student, current_user.user_id)
            
            if not student:
                raise HTTPException(
                    status_code=404,
                    detail="Perfil de estudiante no encontrado"
                )
            
            # ✅ Conversión segura a StudentProfile
            # Maneja casos donde algunos campos podrían no existir en BD antigua
            
            # Helper para parsear listas de JSON de forma segura
            def safe_parse_list(value):
                """Parsear lista de JSON con fallback seguro"""
                try:
                    if isinstance(value, list):
                        return value
                    if isinstance(value, str) and value:
                        return json.loads(value)
                    return []
                except (json.JSONDecodeError, ValueError):
                    return []
            
            # ✅ Desencriptar email de forma segura, manejando excepciones
            student_email = None
            if hasattr(student, 'get_email') and callable(student.get_email):
                try:
                    student_email = student.get_email()
                except Exception as e:
                    logger.warning(f"⚠️ Error desencriptando email del estudiante {student.id}: {str(e)}")
                    # Fallback: usar email encriptado o marcar como indisponible
                    student_email = "[Email no disponible]"
            else:
                student_email = student.email

            # ✅ Desencriptar teléfono de forma segura
            student_phone = None
            if hasattr(student, 'get_phone') and callable(student.get_phone):
                try:
                    student_phone = student.get_phone()
                except Exception as e:
                    logger.warning(f"⚠️ Error desencriptando teléfono del estudiante {student.id}: {str(e)}")
                    student_phone = None

            profile = {
                "id": student.id,
                "name": student.name,
                "role": "student",
                "first_name": getattr(student, 'first_name', None),
                "last_name": getattr(student, 'last_name', None),
                "email": student_email,
                "phone": student_phone,
                "bio": getattr(student, 'bio', None),
                "program": student.program,
                "career": getattr(student, 'career', None),
                "year": getattr(student, 'year', None),
                "skills": safe_parse_list(getattr(student, 'skills', None)),
                "soft_skills": safe_parse_list(getattr(student, 'soft_skills', None)),
                "projects": safe_parse_list(getattr(student, 'projects', None)),
                "cv_uploaded": student.cv_uploaded or False,
                "cv_filename": student.cv_filename,
                "cv_upload_date": student.cv_upload_date,
                # ✅ Harvard CV Fields (NEW)
                "objective": getattr(student, 'objective', None),
                "education": safe_parse_list(getattr(student, 'education', None)),
                "experience": safe_parse_list(getattr(student, 'experience', None)),
                "certifications": safe_parse_list(getattr(student, 'certifications', None)),
                "languages": safe_parse_list(getattr(student, 'languages', None)),
                "created_at": student.created_at.isoformat() if student.created_at else None,
                "last_active": student.last_active.isoformat() if student.last_active else None,
                "is_active": student.is_active or True,
            }
            
        elif current_user.role == "company":
            # Obtener perfil de empresa
            company = await session.get(Company, current_user.user_id)
            
            if not company:
                raise HTTPException(
                    status_code=404,
                    detail="Perfil de empresa no encontrado"
                )
            
            # ✅ Desencriptar email de forma segura, manejando excepciones
            company_email = None
            if hasattr(company, 'get_email') and callable(company.get_email):
                try:
                    company_email = company.get_email()
                except Exception as e:
                    logger.warning(f"⚠️ Error desencriptando email de la empresa {company.id}: {str(e)}")
                    company_email = "[Email no disponible]"
            else:
                company_email = company.email

            # ✅ Conversión segura a CompanyProfile
            profile = {
                "id": company.id,
                "name": company.name,
                "role": "company",
                "email": company_email,
                "industry": company.industry,
                "size": company.size,
                "location": company.location,
                "is_verified": company.is_verified or False,
                "is_active": company.is_active or True,
                "created_at": company.created_at.isoformat() if company.created_at else None,
            }
            
        else:
            # Admin o rol desconocido - retornar contexto básico
            profile = {
                "id": current_user.user_id,
                "role": current_user.role,
                "email": current_user.email,
                "permissions": current_user.permissions
            }
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en GET /auth/me: {type(e).__name__}: {str(e)}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo perfil: {str(e)}"
        )


@router.api_route("/authenticate", methods=["POST"])
async def authenticate_session(
    credentials: LoginRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Endpoint adicional para autenticación basada en contraseña.
    Retorna token/API key para la sesión.
    """
    # Redirigir a /login
    return await login_user(credentials, session)


@router.post("/api-keys", response_model=ApiKeyCreatedResponse)
async def create_api_key(
    key_data: ApiKeyCreate,
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Crear nueva API key para el usuario autenticado
    
    Permite a los usuarios generar claves adicionales con diferentes permisos.
    """
    if current_user.role == "anonymous":
        raise HTTPException(
            status_code=401,
            detail="Debe autenticarse para crear API keys"
        )
    
    if not current_user.user_id:
        raise HTTPException(
            status_code=400,
            detail="No se pudo identificar el usuario"
        )
    
    # Verificar límite de claves por usuario
    result = await session.execute(
        select(ApiKey).where(
            (ApiKey.user_id == current_user.user_id) &
            (ApiKey.user_type == current_user.role) &
            (ApiKey.is_active == True)
        )
    )
    existing_keys = result.scalars().all()
    
    if len(existing_keys) >= 10:  # Máximo 10 claves activas por usuario
        raise HTTPException(
            status_code=400,
            detail="Ha alcanzado el límite máximo de API keys (10)"
        )
    
    api_key_response = await api_key_service.create_api_key(
        session=session,
        user_id=current_user.user_id,
        user_type=current_user.role,
        user_email=current_user.email,
        key_data=key_data
    )
    
    # Registrar en auditoría
    audit_log = AuditLog(
        actor_role=current_user.role,
        actor_id=current_user.email,
        action="create_api_key",
        resource=f"key_id:{api_key_response.key_info.key_id}",
        success=True,
        details=f"Nueva API key creada: {key_data.name}"
    )
    session.add(audit_log)
    await session.commit()
    
    return api_key_response


@router.get("/api-keys", response_model=ApiKeysList)
async def list_api_keys(
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Listar todas las API keys del usuario autenticado
    
    Muestra información de las claves sin exponer los valores secretos.
    """
    if current_user.role == "anonymous" or not current_user.user_id:
        raise HTTPException(
            status_code=401,
            detail="Debe autenticarse para ver sus API keys"
        )
    
    keys = await api_key_service.get_user_api_keys(
        session=session,
        user_id=current_user.user_id,
        user_type=current_user.role
    )
    
    return ApiKeysList(
        keys=keys,
        total=len(keys)
    )


@router.delete("/api-keys/{key_id}", response_model=BaseResponse)
async def revoke_api_key(
    key_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Revocar una API key específica
    
    Desactiva permanentemente la clave especificada.
    """
    if current_user.role == "anonymous" or not current_user.user_id:
        raise HTTPException(
            status_code=401,
            detail="Debe autenticarse para revocar API keys"
        )
    
    success = await api_key_service.revoke_api_key(
        session=session,
        key_id=key_id,
        user_id=current_user.user_id
    )
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="API key no encontrada o no pertenece al usuario"
        )
    
    # Registrar en auditoría
    audit_log = AuditLog(
        actor_role=current_user.role,
        actor_id=current_user.email,
        action="revoke_api_key",
        resource=f"key_id:{key_id}",
        success=True,
        details="API key revocada por el usuario"
    )
    session.add(audit_log)
    await session.commit()
    
    return BaseResponse(
        success=True,
        message="API key revocada exitosamente"
    )


@router.get("/me", response_model=dict)
async def get_current_user_info(
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Obtener información del usuario autenticado
    
    Retorna el contexto y permisos del usuario actual.
    """
    if current_user.role == "anonymous":
        raise HTTPException(
            status_code=401,
            detail="Debe autenticarse para ver su información"
        )
    
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "name": getattr(current_user, 'name', None) or current_user.email.split('@')[0],
        "role": current_user.role,
        "permissions": current_user.permissions
    }


@router.post("/cleanup-expired-keys", response_model=BaseResponse)
async def cleanup_expired_keys(
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Limpiar claves expiradas (solo admin)
    
    Tarea de mantenimiento para desactivar claves vencidas.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden ejecutar tareas de limpieza"
        )
    
    cleaned_count = await api_key_service.cleanup_expired_keys(session)
    
    # Registrar en auditoría
    audit_log = AuditLog(
        actor_role=current_user.role,
        actor_id=current_user.email,
        action="cleanup_expired_keys",
        resource="system",
        success=True,
        details=f"Limpiadas {cleaned_count} claves expiradas"
    )
    session.add(audit_log)
    await session.commit()
    
    return BaseResponse(
        success=True,
        message=f"Se desactivaron {cleaned_count} claves expiradas"
    )
