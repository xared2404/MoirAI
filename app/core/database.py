"""
Configuración y manejo de la base de datos
Soporta SQLite para desarrollo y PostgreSQL para producción (async)
"""
from sqlmodel import SQLModel, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Determine database type
is_sqlite = "sqlite" in settings.DATABASE_URL
is_postgresql = "postgresql" in settings.DATABASE_URL

# Engine configuration
engine_kwargs = {
    "echo": False,  # Cambiar a True para debug SQL
}

# Database-specific configurations
if is_sqlite:
    logger.warning("⚠️  SQLite no soporta async completamente. Para producción usa PostgreSQL.")
    # Convertir sqlite:// a sqlite+aiosqlite://
    db_url = settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite:///")
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    logger.info("📊 Using SQLite with async support (development)")
    
elif is_postgresql:
    # Convertir postgresql:// a postgresql+asyncpg://
    db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_recycle": settings.DB_POOL_RECYCLE,
        "pool_pre_ping": settings.DB_POOL_PRE_PING,
    })
    logger.info(f"📊 Using PostgreSQL with async (production)")
    logger.info(f"   Pool size: {settings.DB_POOL_SIZE}")
    logger.info(f"   Max overflow: {settings.DB_MAX_OVERFLOW}")
    logger.info(f"   Pool recycle: {settings.DB_POOL_RECYCLE}s")

# Create async engine
async_engine = create_async_engine(db_url, **engine_kwargs)

# Session factory para usar con async/await
async_session = sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def create_db_and_tables():
    """Crear todas las tablas de la base de datos (async)"""
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    """Dependency para obtener sesión de base de datos (async)"""
    async with async_session() as session:
        yield session
