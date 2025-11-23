"""
Módulo para inicialización de usuario admin desde configuración.
Se ejecuta al iniciar la aplicación si INIT_DEFAULT_ADMIN=true en .env
"""

import logging
import hashlib
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models import Admin
from app.services.api_key_service import api_key_service
from app.schemas import ApiKeyCreate
from datetime import datetime

logger = logging.getLogger(__name__)


async def init_default_admin(session: AsyncSession) -> Optional[int]:
    """
    Inicializa el usuario admin por defecto desde .env
    
    Se ejecuta SOLO si:
    1. INIT_DEFAULT_ADMIN=true en .env
    2. No existe un admin con el email configurado
    
    El admin es creado en la tabla 'admin' con email y contraseña,
    y luego se le asigna una API key para usos internos de firma.
    
    Args:
        session: Sesión de base de datos (ASYNC)
        
    Returns:
        int: ID del usuario admin creado, o None si no se creó
    """
    
    # Verificar si está habilitada la inicialización de admin
    if not settings.INIT_DEFAULT_ADMIN:
        logger.debug("✓ Inicialización de admin deshabilitada (INIT_DEFAULT_ADMIN=false)")
        return None
    
    # Validar configuración requerida
    if not all([
        settings.ADMIN_DEFAULT_EMAIL,
        settings.ADMIN_DEFAULT_PASSWORD,
        settings.ADMIN_DEFAULT_NAME
    ]):
        logger.warning(
            "⚠️  INIT_DEFAULT_ADMIN=true pero valores en blanco en .env "
            "(ADMIN_DEFAULT_EMAIL, ADMIN_DEFAULT_PASSWORD, ADMIN_DEFAULT_NAME)"
        )
        return None
    
    try:
        # Verificar si el admin ya existe (ASYNC)
        email_hash = hashlib.sha256(settings.ADMIN_DEFAULT_EMAIL.lower().strip().encode()).hexdigest()
        result = await session.execute(
            select(Admin).where(Admin.email_hash == email_hash)
        )
        existing_admin = result.scalars().first()
        
        if existing_admin:
            logger.info(
                f"✓ Admin ya existe: {settings.ADMIN_DEFAULT_EMAIL} "
                "(cambiar INIT_DEFAULT_ADMIN=false en .env para evitar intentos repetidos)"
            )
            return existing_admin.id
        
        # Crear nuevo admin en la tabla admin
        logger.info(f"🔧 Creando usuario admin por defecto: {settings.ADMIN_DEFAULT_NAME}")
        
        # Hash de la contraseña (SHA256)
        password_hash = hashlib.sha256(settings.ADMIN_DEFAULT_PASSWORD.encode()).hexdigest()
        
        # Crear instancia de Admin
        new_admin = Admin(
            name=settings.ADMIN_DEFAULT_NAME,
            email=settings.ADMIN_DEFAULT_EMAIL,
            email_hash=email_hash,
            hashed_password=password_hash,
            is_active=True
        )
        
        session.add(new_admin)
        await session.flush()  # Obtener el ID generado
        await session.commit()
        await session.refresh(new_admin)
        
        admin_id = new_admin.id
        
        logger.info(
            f"✅ Admin creado exitosamente:\n"
            f"   ID: {admin_id}\n"
            f"   Name: {settings.ADMIN_DEFAULT_NAME}\n"
            f"   Email: {settings.ADMIN_DEFAULT_EMAIL}"
        )
        
        # Crear API key para el admin (para usos internos de firma)
        try:
            api_key_data = ApiKeyCreate(
                name="Clave principal - Admin Sistema",
                description="API key generada automáticamente al iniciar para firma de cambios",
                expires_days=365
            )
            
            api_key_response = await api_key_service.create_api_key(
                session=session,
                user_id=admin_id,
                user_type="admin",
                user_email=settings.ADMIN_DEFAULT_EMAIL,
                key_data=api_key_data
            )
            
            logger.info(
                f"✅ API Key generada para admin:\n"
                f"   Prefix: {api_key_response.key_info.key_prefix}\n"
                f"   ⚠️  Usar para firma de cambios y acceso interno"
            )
        except Exception as e:
            logger.warning(f"⚠️  No se pudo generar API key para admin: {str(e)}")
            logger.warning(f"   Pero el admin fue creado correctamente con email/password")
        
        return admin_id
        
    except Exception as e:
        logger.error(
            f"❌ Error inicializando admin por defecto: {type(e).__name__}: {str(e)}"
        )
        import traceback
        traceback.print_exc()
        return None


def verify_admin_access_configured() -> bool:
    """
    Verifica que haya al menos una forma de acceder como admin
    
    Returns:
        bool: True si hay acceso admin disponible
    """
    # Opción 1: Admin por defecto en .env
    if settings.INIT_DEFAULT_ADMIN and settings.ADMIN_DEFAULT_EMAIL:
        return True
    
    # Opción 2: API keys de admin configuradas
    if settings.ADMIN_API_KEYS and len(settings.ADMIN_API_KEYS) > 0:
        return True
    
    logger.warning(
        "⚠️  NO HAY ACCESO ADMIN CONFIGURADO:\n"
        "   • INIT_DEFAULT_ADMIN=false en .env\n"
        "   • No hay ADMIN_API_KEYS configuradas\n"
        "   Use: INIT_DEFAULT_ADMIN=true y configure ADMIN_DEFAULT_* en .env"
    )
    return False
