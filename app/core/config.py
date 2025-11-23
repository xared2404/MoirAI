"""
Configuración central de la aplicación MoirAI
Manejo de variables de entorno y configuraciones de seguridad
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Configuración principal de la aplicación"""
    
    # Base configuration
    PROJECT_NAME: str = "MoirAI - UNRC Job Matching Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database - Core Configuration
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/moirai",
        description="URL de conexión a la base de datos"
    )
    
    # Database - Connection Pooling (PostgreSQL)
    DB_POOL_SIZE: int = Field(
        default=20,
        description="Número de conexiones a mantener en el pool"
    )
    DB_MAX_OVERFLOW: int = Field(
        default=40,
        description="Conexiones adicionales permitidas cuando pool está full"
    )
    DB_POOL_RECYCLE: int = Field(
        default=3600,
        description="Tiempo en segundos para reciclar conexiones"
    )
    DB_POOL_PRE_PING: bool = Field(
        default=True,
        description="Probar conexión antes de usarla"
    )
    
    # Security
    SECRET_KEY: str = Field(
        ...,
        description="Clave secreta para JWT tokens"
    )
    ENCRYPTION_KEY: Optional[str] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Encryption
    ENCRYPTION_KEY: Optional[str] = Field(
        default=None,
        description="Clave Fernet para encriptar campos sensibles (auto-generada si no se proporciona)"
    )
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Job Search Providers
    JSEARCH_API_KEY: Optional[str] = None
    JSEARCH_HOST: str = "jsearch.p.rapidapi.com"
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".docx", ".txt"]
    
    # NLP Configuration
    SPACY_MODEL: str = "en_core_web_sm"
    MAX_SKILLS_EXTRACTED: int = 30
    MAX_SOFT_SKILLS_EXTRACTED: int = 20
    MAX_PROJECTS_EXTRACTED: int = 20
    
    # Text Vectorization Configuration
    NLP_MAX_TEXT_LENGTH: int = Field(
        default=50000,
        description="Máximo de caracteres a procesar en un documento"
    )
    NLP_MAX_TOKEN_LENGTH: int = Field(
        default=100,
        description="Máximo de caracteres por token"
    )
    NLP_MAX_VOCAB_SIZE: int = Field(
        default=5000,
        description="Máximo de tokens únicos en vocabulario"
    )
    NLP_MAX_NGRAM_SIZE: int = Field(
        default=3,
        description="Máximo tamaño de n-gramas (1=unigramas, 2=bigramas, etc.)"
    )
    NLP_MIN_TOKEN_LENGTH: int = Field(
        default=2,
        description="Longitud mínima de tokens válidos"
    )
    
    # Privacy and Security (LFPDPPP compliance)
    DATA_RETENTION_DAYS: int = 365
    REQUIRE_CONSENT: bool = True
    ENABLE_AUDIT_LOGGING: bool = True
    
    # Performance
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # API Keys por rol (desarrollo - reemplazar con OAuth2 en producción)
    ADMIN_API_KEYS: List[str] = []
    COMPANY_API_KEYS: List[str] = []
    STUDENT_API_KEYS: List[str] = []

    # Admin Configuration (SEGURIDAD)
    # Inicialización de admin por defecto desde .env
    INIT_DEFAULT_ADMIN: bool = Field(
        default=False,
        description="Si true, intenta crear admin por defecto al iniciar. Cambiar a false después de crear."
    )
    ADMIN_DEFAULT_NAME: Optional[str] = Field(
        default=None,
        description="Nombre del admin por defecto (vacío = deshabilitado)"
    )
    ADMIN_DEFAULT_EMAIL: Optional[str] = Field(
        default=None,
        description="Email del admin por defecto (vacío = deshabilitado)"
    )
    ADMIN_DEFAULT_PASSWORD: Optional[str] = Field(
        default=None,
        description="Contraseña inicial del admin (vacío = deshabilitado)"
    )

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        env_file = ".env"
        case_sensitive = True

# Instancia global de configuración
settings = Settings()
