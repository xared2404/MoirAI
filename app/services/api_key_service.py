"""
Servicio para gestión dinámica de API Keys (ASYNC)
Genera, valida y gestiona claves de API para usuarios autenticados
Completamente asincrónico con AsyncSession
"""
import secrets
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import ApiKey, Student, Company
from app.schemas import ApiKeyCreate, ApiKeyResponse, ApiKeyCreatedResponse


class ApiKeyService:
    """Servicio para gestión de API Keys"""
    
    # Prefijos por tipo de usuario
    KEY_PREFIXES = {
        "student": "stu_",
        "company": "com_", 
        "admin": "adm_"
    }
    
    # Permisos por defecto por rol
    DEFAULT_SCOPES = {
        "student": [
            "read:own_profile",
            "write:own_profile", 
            "read:jobs",
            "read:public_students"
        ],
        "company": [
            "read:students",
            "read:jobs",
            "write:jobs",
            "read:own_profile",
            "write:own_profile"
        ],
        "admin": [
            "read:all",
            "write:all", 
            "admin:all",
            "manage:users",
            "manage:api_keys"
        ]
    }
    
    @staticmethod
    def generate_api_key() -> tuple[str, str, str]:
        """
        Genera una nueva API key
        Returns: (full_key, key_id, key_hash)
        """
        # Generar componentes
        # Usar '-' como separador en lugar de '_' para evitar conflictos en parsing
        key_id = secrets.token_urlsafe(16).replace('_', '-')  # Asegurar que NO contiene '_'
        secret_part = secrets.token_urlsafe(32)
        
        # Clave completa: keyid_secret
        full_key = f"{key_id}_{secret_part}"
        
        # Hash para almacenamiento seguro
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        
        return full_key, key_id, key_hash
    
    @staticmethod
    async def create_api_key(
        session: AsyncSession,
        user_id: int,
        user_type: str,
        user_email: str,
        key_data: ApiKeyCreate
    ) -> ApiKeyCreatedResponse:
        """Crear nueva API key para usuario - ASYNC"""
        
        # Generar clave
        full_key, key_id, key_hash = ApiKeyService.generate_api_key()
        
        # Determinar prefijo
        prefix = ApiKeyService.KEY_PREFIXES.get(user_type, "key_")
        key_prefix = f"{prefix}{key_id[:8]}"
        
        # Determinar permisos
        scopes = key_data.scopes if key_data.scopes else ApiKeyService.DEFAULT_SCOPES.get(user_type, [])
        
        # Calcular expiración
        expires_at = None
        if key_data.expires_days:
            expires_at = datetime.utcnow() + timedelta(days=key_data.expires_days)
        
        # Crear registro
        api_key = ApiKey(
            key_id=key_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            user_id=user_id,
            user_type=user_type,
            user_email=user_email,
            name=key_data.name,
            description=key_data.description,
            scopes=json.dumps(scopes),
            allowed_ips=json.dumps(key_data.allowed_ips) if key_data.allowed_ips else None,
            rate_limit=key_data.rate_limit,
            expires_at=expires_at
        )
        
        session.add(api_key)
        await session.commit()
        await session.refresh(api_key)
        
        # Preparar respuesta
        key_info = ApiKeyResponse(
            key_id=api_key.key_id,
            name=api_key.name,
            description=api_key.description,
            key_prefix=api_key.key_prefix,
            scopes=json.loads(api_key.scopes),
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            last_used_at=api_key.last_used_at,
            usage_count=api_key.usage_count,
            expires_at=api_key.expires_at,
            rate_limit=api_key.rate_limit
        )
        
        return ApiKeyCreatedResponse(
            api_key=full_key,
            key_info=key_info
        )
    
    @staticmethod
    async def validate_api_key(session: AsyncSession, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validar API key y retornar información del usuario - ASYNC
        Returns: None si inválida, dict con info del usuario si válida
        """
        if not api_key or "_" not in api_key:
            return None
        
        # Extraer key_id (parte antes del primer '_')
        key_id = api_key.split("_")[0]
        
        # Buscar en BD
        from sqlalchemy import and_
        result = await session.execute(
            select(ApiKey).where(
                and_(
                    ApiKey.key_id == key_id,
                    ApiKey.is_active == True
                )
            )
        )
        db_key = result.scalars().first()
        
        if not db_key:
            return None
        
        # Verificar hash
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        if key_hash != db_key.key_hash:
            return None
        
        # Verificar expiración
        if db_key.expires_at and db_key.expires_at < datetime.utcnow():
            return None
        
        # Actualizar estadísticas de uso
        db_key.last_used_at = datetime.utcnow()
        db_key.usage_count += 1
        session.add(db_key)
        await session.commit()
        
        # Retornar información del usuario
        return {
            "user_id": db_key.user_id,
            "user_type": db_key.user_type,
            "user_email": db_key.user_email,
            "scopes": json.loads(db_key.scopes),
            "rate_limit": db_key.rate_limit,
            "key_id": db_key.key_id
        }
    
    @staticmethod
    async def get_user_api_keys(session: AsyncSession, user_id: int, user_type: str) -> List[ApiKeyResponse]:
        """Obtener todas las API keys de un usuario - ASYNC"""
        from sqlalchemy import and_
        result = await session.execute(
            select(ApiKey).where(
                and_(
                    ApiKey.user_id == user_id,
                    ApiKey.user_type == user_type
                )
            ).order_by(ApiKey.created_at.desc())
        )
        keys = result.scalars().all()
        
        return [
            ApiKeyResponse(
                key_id=key.key_id,
                name=key.name,
                description=key.description,
                key_prefix=key.key_prefix,
                scopes=json.loads(key.scopes),
                is_active=key.is_active,
                created_at=key.created_at,
                last_used_at=key.last_used_at,
                usage_count=key.usage_count,
                expires_at=key.expires_at,
                rate_limit=key.rate_limit
            )
            for key in keys
        ]
    
    @staticmethod
    async def revoke_api_key(session: AsyncSession, key_id: str, user_id: int) -> bool:
        """Revocar una API key específica - ASYNC"""
        from sqlalchemy import and_
        result = await session.execute(
            select(ApiKey).where(
                and_(
                    ApiKey.key_id == key_id,
                    ApiKey.user_id == user_id
                )
            )
        )
        api_key = result.scalars().first()
        
        if not api_key:
            return False
        
        api_key.is_active = False
        api_key.updated_at = datetime.utcnow()
        session.add(api_key)
        await session.commit()
        
        return True
    
    @staticmethod
    async def cleanup_expired_keys(session: AsyncSession) -> int:
        """Limpiar claves expiradas (tarea de mantenimiento) - ASYNC"""
        from sqlalchemy import and_
        result = await session.execute(
            select(ApiKey).where(
                and_(
                    ApiKey.expires_at < datetime.utcnow(),
                    ApiKey.is_active == True
                )
            )
        )
        expired_keys = result.scalars().all()
        
        count = 0
        for key in expired_keys:
            key.is_active = False
            key.updated_at = datetime.utcnow()
            session.add(key)
            count += 1
        
        await session.commit()
        return count


# Instancia del servicio
api_key_service = ApiKeyService()
