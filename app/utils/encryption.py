"""
Servicio de encriptación para campos sensibles
Cumplimiento de LFPDPPP y protección de datos personales
"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Servicio centralizado para encriptación/desencriptación de campos sensibles.

    Utiliza el algoritmo Fernet (AES-128) que proporciona confidencialidad,
    integridad y autenticación de datos.

    **Campos que deben ser encriptados:**
    - Emails de usuarios
    - Números telefónicos
    - Direcciones
    - Datos bancarios/de pago
    - Documentos de identidad
    - Notas personales con PII

    **Seguridad:**
    - ✅ Encriptación simétrica (AES-128)
    - ✅ Integridad verificada (HMAC)
    - ✅ Autenticación de datos
    - ✅ Generación segura de claves
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Inicializar el servicio de encriptación.

        Args:
            encryption_key: Clave Fernet en base64. Si no se proporciona,
                          se intenta obtener de variable de entorno ENCRYPTION_KEY o settings
        """
        if encryption_key:
            self.key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        else:
            # Intentar obtener de variable de entorno primero
            env_key = os.getenv("ENCRYPTION_KEY")
            
            # Si no está en env, intentar obtener de settings
            if not env_key:
                try:
                    from app.core.config import settings
                    env_key = settings.ENCRYPTION_KEY
                except Exception as import_error:
                    logger.debug(f"No se pudo cargar settings: {import_error}")
            
            if not env_key:
                logger.warning(
                    "⚠️ ENCRYPTION_KEY no configurada. "
                    "Generando clave temporal (NO usar en producción)"
                )
                self.key = Fernet.generate_key()
            else:
                self.key = env_key.encode() if isinstance(env_key, str) else env_key

        try:
            self.cipher = Fernet(self.key)
        except Exception as e:
            logger.error(f"Error al inicializar Fernet: {e}")
            raise ValueError(f"Clave de encriptación inválida: {e}")

    @staticmethod
    def generate_key() -> str:
        """
        Generar una nueva clave Fernet segura.

        Returns:
            Clave en formato base64 string

        **Uso:**
        ```python
        key = EncryptionService.generate_key()
        print(f"ENCRYPTION_KEY={key}")
        # Guardar en .env o variable de entorno
        ```
        """
        key = Fernet.generate_key()
        return key.decode('utf-8')

    @staticmethod
    def generate_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple:
        """
        Generar clave Fernet a partir de una contraseña (PBKDF2).

        Args:
            password: Contraseña base
            salt: Salt para PBKDF2 (si None, se genera uno)

        Returns:
            (clave_base64, salt_base64) - tupla con clave y salt

        **Uso:**
        ```python
        key, salt = EncryptionService.generate_key_from_password("my_password")
        # Guardar salt de forma segura junto con la clave
        ```
        """
        if salt is None:
            salt = os.urandom(16)
        elif isinstance(salt, str):
            salt = base64.b64decode(salt)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        salt_b64 = base64.b64encode(salt).decode('utf-8')

        return key.decode('utf-8'), salt_b64

    def encrypt(self, plaintext: str) -> str:
        """
        Encriptar texto plano.

        Args:
            plaintext: Texto a encriptar (puede ser email, teléfono, dirección, etc.)

        Returns:
            Texto encriptado en formato base64 string

        Raises:
            TypeError: Si el texto no es string
            Exception: Si falla la encriptación

        **Ejemplo:**
        ```python
        service = EncryptionService()
        encrypted_email = service.encrypt("user@example.com")
        # Guardar en BD
        ```
        """
        if not isinstance(plaintext, str):
            raise TypeError(f"Se esperaba string, se recibió {type(plaintext)}")

        try:
            # Codificar a bytes y encriptar
            plaintext_bytes = plaintext.encode('utf-8')
            ciphertext = self.cipher.encrypt(plaintext_bytes)
            # Retornar en base64 para almacenar fácilmente en BD
            return ciphertext.decode('utf-8')
        except Exception as e:
            logger.error(f"Error al encriptar: {e}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        """
        Desencriptar texto.

        Args:
            ciphertext: Texto encriptado (obtenido de encrypt())

        Returns:
            Texto original desencriptado

        Raises:
            TypeError: Si el texto no es string
            Exception: Si falla la desencriptación (clave incorrecta, etc.)

        **Ejemplo:**
        ```python
        service = EncryptionService()
        email = service.decrypt(encrypted_email)
        # Usar email desencriptado
        ```
        """
        if not isinstance(ciphertext, str):
            raise TypeError(f"Se esperaba string, se recibió {type(ciphertext)}")

        try:
            # Decodificar desde base64 y desencriptar
            ciphertext_bytes = ciphertext.encode('utf-8')
            plaintext = self.cipher.decrypt(ciphertext_bytes)
            return plaintext.decode('utf-8')
        except Exception as e:
            logger.error(f"Error al desencriptar: {e}")
            raise

    def encrypt_optional(self, plaintext: Optional[str]) -> Optional[str]:
        """
        Encriptar de forma segura si el valor no es None.

        Args:
            plaintext: Valor a encriptar (puede ser None)

        Returns:
            Valor encriptado o None si era None

        **Ejemplo:**
        ```python
        encrypted_phone = service.encrypt_optional(student.phone)
        ```
        """
        return self.encrypt(plaintext) if plaintext else None

    def decrypt_optional(self, ciphertext: Optional[str]) -> Optional[str]:
        """
        Desencriptar de forma segura si el valor no es None.

        Args:
            ciphertext: Valor encriptado (puede ser None)

        Returns:
            Valor desencriptado o None si era None

        **Ejemplo:**
        ```python
        phone = service.decrypt_optional(encrypted_phone)
        ```
        """
        return self.decrypt(ciphertext) if ciphertext else None

    def encrypt_email(self, email: str) -> str:
        """
        Encriptar un email con validación adicional.

        Args:
            email: Email a encriptar

        Returns:
            Email encriptado

        Raises:
            ValueError: Si el email parece inválido
        """
        email_lower = email.lower().strip()
        if '@' not in email_lower or '.' not in email_lower.split('@')[1]:
            logger.warning(f"Email potencialmente inválido: {email_lower}")

        return self.encrypt(email_lower)

    def decrypt_email(self, encrypted_email: str) -> str:
        """
        Desencriptar un email.

        Args:
            encrypted_email: Email encriptado

        Returns:
            Email desencriptado en minúsculas
        """
        return self.decrypt(encrypted_email).lower()

    def encrypt_phone(self, phone: str) -> str:
        """
        Encriptar un número telefónico.

        Args:
            phone: Número telefónico (puede incluir espacios, guiones, etc.)

        Returns:
            Teléfono encriptado
        """
        # Normalizar: remover espacios y caracteres especiales
        phone_normalized = ''.join(filter(str.isdigit, phone))
        if len(phone_normalized) < 10:
            logger.warning(f"Teléfono corto: {phone}")

        return self.encrypt(phone)

    def decrypt_phone(self, encrypted_phone: str) -> str:
        """
        Desencriptar un número telefónico.

        Args:
            encrypted_phone: Teléfono encriptado

        Returns:
            Teléfono desencriptado
        """
        return self.decrypt(encrypted_phone)

    def encrypt_dict(self, data: dict, fields_to_encrypt: list) -> dict:
        """
        Encriptar campos específicos en un diccionario.

        Args:
            data: Diccionario con datos
            fields_to_encrypt: Lista de nombres de campos a encriptar

        Returns:
            Diccionario con campos encriptados

        **Ejemplo:**
        ```python
        student_data = {
            "id": 1,
            "name": "John",
            "email": "john@example.com",
            "phone": "555-1234"
        }
        encrypted = service.encrypt_dict(
            student_data,
            fields_to_encrypt=["email", "phone"]
        )
        # encrypted["email"] y encrypted["phone"] estarán encriptados
        ```
        """
        result = data.copy()
        for field in fields_to_encrypt:
            if field in result and result[field]:
                try:
                    result[field] = self.encrypt(str(result[field]))
                except Exception as e:
                    logger.error(f"Error encriptando campo {field}: {e}")
                    raise

        return result

    def decrypt_dict(self, data: dict, fields_to_decrypt: list) -> dict:
        """
        Desencriptar campos específicos en un diccionario.

        Args:
            data: Diccionario con datos encriptados
            fields_to_decrypt: Lista de nombres de campos a desencriptar

        Returns:
            Diccionario con campos desencriptados

        **Ejemplo:**
        ```python
        decrypted = service.decrypt_dict(
            encrypted_data,
            fields_to_decrypt=["email", "phone"]
        )
        ```
        """
        result = data.copy()
        for field in fields_to_decrypt:
            if field in result and result[field]:
                try:
                    result[field] = self.decrypt(str(result[field]))
                except Exception as e:
                    logger.error(f"Error desencriptando campo {field}: {e}")
                    raise

        return result
    
    @staticmethod
    def _get_hash_email(email: str) -> str:
        """
        Obtener hash SHA256 de un email normalizado.
        
        ✅ Usado para búsquedas de email sin desencriptar
        
        Args:
            email: Email en texto plano
            
        Returns:
            Hash SHA256 del email
        """
        import hashlib
        email_lower = email.lower().strip()
        return hashlib.sha256(email_lower.encode()).hexdigest()


# Instancia global del servicio de encriptación
def get_encryption_service() -> EncryptionService:
    """
    Obtener instancia del servicio de encriptación.

    Returns:
        Instancia de EncryptionService configurada con la clave del entorno

    **Uso:**
    ```python
    from app.utils.encryption import get_encryption_service
    encryption = get_encryption_service()
    encrypted = encryption.encrypt("sensitive@data.com")
    ```
    """
    return EncryptionService()


# Para uso directo si se necesita en tests o scripts
# La instancia se crea al momento de usar, asegurando que la clave esté disponible
encryption_service = EncryptionService()
