"""
Modelo JobPosting con Encriptación Integrada

Cumplimiento LFPDPPP ✅:
- Email y teléfono encriptados con Fernet AES-128
- Hashes SHA-256 para búsquedas sin desencriptar
- Datos sensibles protegidos en tránsito y almacenamiento

Diseño:
- Almacenar valores encriptados en BD
- Métodos set_email/get_email para transparencia
- Hash en índice único para búsquedas eficientes
"""

from sqlmodel import SQLModel, Field, Index
from datetime import datetime
from typing import Optional, List
import json
import logging

logger = logging.getLogger(__name__)


class JobPosting(SQLModel, table=True):
    """
    Modelo de Job Posting con soporte para encriptación.
    
    Atributos:
    -----------
    id : int
        ID único en la base de datos (PK)
    external_job_id : str
        ID único de la fuente (e.g., OCC.com.mx)
    title : str
        Título del puesto de trabajo
    company : str
        Nombre de la empresa
    location : str
        Ubicación del trabajo
    description : str
        Descripción completa del puesto
    email : str
        Email de contacto (ENCRIPTADO en BD)
    email_hash : str
        Hash SHA-256 del email (para búsquedas sin desencriptar)
    phone : Optional[str]
        Teléfono de contacto (ENCRIPTADO en BD)
    phone_hash : Optional[str]
        Hash SHA-256 del teléfono
    skills : str
        Array JSON de habilidades extraídas
    work_mode : str
        presencial | remoto | híbrido
    job_type : str
        full-time | part-time | temporal | freelance
    salary_min : Optional[float]
        Salario mínimo en MXN
    salary_max : Optional[float]
        Salario máximo en MXN
    currency : str
        Moneda (default: MXN)
    published_at : datetime
        Fecha de publicación original
    created_at : datetime
        Fecha de creación en BD
    updated_at : datetime
        Fecha de última actualización
    source : str
        Fuente de datos (occ.com.mx, etc.)
    
    Security Notes:
    ---------------
    - Email y phone se almacenan encriptados
    - Los hashes permiten búsquedas sin desencriptar
    - Methods set_email/get_email manejan automáticamente
    - Compatible con LFPDPPP (protección PII)
    """
    
    __tablename__ = "job_postings"
    
    # ========================================================================
    # Primary Keys & IDs
    # ========================================================================
    
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="ID único en BD"
    )
    
    external_job_id: str = Field(
        unique=True,
        index=True,
        description="ID único de fuente (OCC.com.mx, LinkedIn, etc.)"
    )
    
    # ========================================================================
    # Core Fields
    # ========================================================================
    
    title: str = Field(
        index=True,
        min_length=4,
        max_length=200,
        description="Título del puesto"
    )
    
    company: str = Field(
        min_length=1,
        max_length=150,
        description="Nombre de la empresa"
    )
    
    location: str = Field(
        index=True,
        min_length=1,
        max_length=200,
        description="Ubicación (ciudad, estado)"
    )
    
    description: str = Field(
        min_length=10,
        max_length=5000,
        description="Descripción completa del puesto"
    )
    
    # ========================================================================
    # Encrypted Fields (LFPDPPP Compliance)
    # ========================================================================
    
    email: str = Field(
        description="Email de contacto - ENCRIPTADO CON FERNET en BD"
    )
    
    email_hash: str = Field(
        unique=True,
        index=True,
        description="Hash SHA-256 del email - para búsquedas sin desencriptar"
    )
    
    phone: Optional[str] = Field(
        default=None,
        description="Teléfono de contacto - ENCRIPTADO CON FERNET en BD"
    )
    
    phone_hash: Optional[str] = Field(
        default=None,
        index=True,
        description="Hash SHA-256 del teléfono"
    )
    
    # ========================================================================
    # Parsed Data (from HTML Parser)
    # ========================================================================
    
    skills: str = Field(
        default="[]",
        description="Array JSON de habilidades extraídas: ['Python', 'JavaScript']"
    )
    
    work_mode: str = Field(
        default="hybrid",
        description="Modalidad: presencial | remoto | híbrido"
    )
    
    job_type: str = Field(
        default="full-time",
        description="Tipo: full-time | part-time | temporal | freelance"
    )
    
    salary_min: Optional[float] = Field(
        default=None,
        description="Salario mínimo en MXN"
    )
    
    salary_max: Optional[float] = Field(
        default=None,
        description="Salario máximo en MXN"
    )
    
    currency: str = Field(
        default="MXN",
        description="Moneda del salario"
    )
    
    # ========================================================================
    # Metadata
    # ========================================================================
    
    published_at: datetime = Field(
        description="Fecha de publicación original"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        index=True,
        description="Fecha de creación en BD"
    )
    
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Fecha de última actualización"
    )
    
    source: str = Field(
        default="occ.com.mx",
        description="Fuente de datos"
    )
    
    # ========================================================================
    # Composite Indexes for Performance
    # ========================================================================
    
    __table_args__ = (
        Index('idx_location_skills', 'location', 'skills'),
        Index('idx_source_published', 'source', 'published_at'),
    )
    
    # ========================================================================
    # Methods for Encryption
    # ========================================================================
    
    def set_email(self, plaintext: str) -> None:
        """
        Encriptar y almacenar email.
        
        Args:
            plaintext: Email en texto plano
            
        Nota:
            Automáticamente genera el hash para búsquedas
        """
        from app.utils.encryption import get_encryption_service
        
        encryption = get_encryption_service()
        self.email = encryption.encrypt_email(plaintext)
        self.email_hash = encryption._get_hash_email(plaintext)
        
        logger.debug("Email encriptado y hash generado")
    
    def get_email(self) -> str:
        """
        Desencriptar y retornar email.
        
        Returns:
            Email en texto plano
        """
        from app.utils.encryption import get_encryption_service
        
        encryption = get_encryption_service()
        return encryption.decrypt_email(self.email)
    
    def set_phone(self, plaintext: Optional[str]) -> None:
        """
        Encriptar y almacenar teléfono.
        
        Args:
            plaintext: Teléfono en texto plano o None
        """
        from app.utils.encryption import get_encryption_service
        
        if not plaintext:
            self.phone = None
            self.phone_hash = None
            return
        
        encryption = get_encryption_service()
        self.phone = encryption.encrypt_phone(plaintext)
        self.phone_hash = encryption._get_hash_email(plaintext)
        
        logger.debug("Teléfono encriptado y hash generado")
    
    def get_phone(self) -> Optional[str]:
        """
        Desencriptar y retornar teléfono.
        
        Returns:
            Teléfono en texto plano o None
        """
        if not self.phone:
            return None
        
        from app.utils.encryption import get_encryption_service
        
        encryption = get_encryption_service()
        return encryption.decrypt_phone(self.phone)
    
    def get_skills(self) -> List[str]:
        """
        Parsear y retornar array de skills.
        
        Returns:
            Lista de skills
        """
        try:
            return json.loads(self.skills or "[]")
        except json.JSONDecodeError:
            logger.warning(f"Invalid skills JSON: {self.skills}")
            return []
    
    def set_skills(self, skills: List[str]) -> None:
        """
        Serializar y almacenar skills como JSON.
        
        Args:
            skills: Lista de skills
        """
        self.skills = json.dumps(skills)
    
    @classmethod
    def from_job_item(cls, job_item, encryption_service=None):
        """
        Crear JobPosting desde JobItem (del HTMLParserService).
        
        Args:
            job_item: JobItem instance del parser HTML
            encryption_service: EncryptionService (opcional, usa default)
            
        Returns:
            JobPosting instance con encriptación aplicada
            
        Note:
            Automáticamente encripta email y phone
        """
        from app.utils.encryption import get_encryption_service
        
        if not encryption_service:
            encryption_service = get_encryption_service()
        
        posting = cls(
            external_job_id=job_item.external_job_id,
            title=job_item.title,
            company=job_item.company,
            location=job_item.location,
            description=job_item.description,
            work_mode=job_item.work_mode or "hybrid",
            job_type=job_item.job_type or "full-time",
            salary_min=job_item.salary_min,
            salary_max=job_item.salary_max,
            currency=job_item.currency,
            published_at=job_item.published_at,
            source=job_item.source,
            email="",  # Será seteado abajo
            email_hash=""  # Será seteado abajo
        )
        
        # Encriptar email (requerido)
        if job_item.email:
            posting.set_email(job_item.email)
        else:
            # Email debe ser requerido pero asignamos placeholder
            posting.email = encryption_service.encrypt("no-email@placeholder.com")
            posting.email_hash = encryption_service._get_hash_email("no-email@placeholder.com")
        
        # Encriptar phone (opcional)
        if job_item.phone:
            posting.set_phone(job_item.phone)
        
        # Skills
        posting.set_skills(job_item.skills)
        
        logger.info(f"✅ JobPosting creado desde JobItem: {posting.title}")
        
        return posting
    
    def to_dict_public(self) -> dict:
        """
        Retornar representación pública sin datos encriptados.
        
        Returns:
            Dict con información pública (sin email/phone desencriptados)
        """
        return {
            "id": self.id,
            "external_job_id": self.external_job_id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "description": self.description[:200] + "...",  # Truncado
            "skills": self.get_skills(),
            "work_mode": self.work_mode,
            "job_type": self.job_type,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "currency": self.currency,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "source": self.source,
        }
