"""
Tests para el servicio de Encriptación
Valida que la encriptación/desencriptación funciona correctamente
"""
import pytest
from cryptography.fernet import InvalidToken

from app.utils.encryption import EncryptionService


class TestEncryptionService:
    """Tests del servicio de encriptación"""

    @pytest.fixture
    def encryption_service(self):
        """Crear instancia del servicio de encriptación"""
        return EncryptionService()

    def test_generate_key(self):
        """Prueba generación de clave"""
        key = EncryptionService.generate_key()

        assert isinstance(key, str)
        assert len(key) > 0
        # Las claves Fernet son strings base64-encoded
        assert len(key) >= 44  # Longitud mínima de clave Fernet codificada

    def test_generate_key_from_password(self):
        """Prueba generación de clave desde contraseña"""
        password = "my_secure_password_123"
        key, salt = EncryptionService.generate_key_from_password(password)

        assert isinstance(key, str)
        assert isinstance(salt, str)
        assert len(key) > 0
        assert len(salt) > 0

    def test_generate_key_from_password_same_password(self):
        """Prueba que misma contraseña + salt genera misma clave"""
        password = "test_password"
        salt = "dGVzdA=="  # base64 encoded "test"

        key1, _ = EncryptionService.generate_key_from_password(password, salt)
        key2, _ = EncryptionService.generate_key_from_password(password, salt)

        assert key1 == key2

    def test_encrypt_decrypt(self, encryption_service):
        """Prueba encriptación y desencriptación básica"""
        plaintext = "This is a secret message"
        
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)

        assert encrypted != plaintext
        assert decrypted == plaintext
        assert isinstance(encrypted, str)

    def test_encrypt_email(self, encryption_service):
        """Prueba encriptación específica de email"""
        email = "user@example.com"
        
        encrypted = encryption_service.encrypt_email(email)
        decrypted = encryption_service.decrypt_email(encrypted)

        assert decrypted == email.lower()

    def test_encrypt_email_uppercase(self, encryption_service):
        """Prueba que emails se normalizan a minúsculas"""
        email = "USER@EXAMPLE.COM"
        
        encrypted = encryption_service.encrypt_email(email)
        decrypted = encryption_service.decrypt_email(encrypted)

        assert decrypted == email.lower()

    def test_encrypt_phone(self, encryption_service):
        """Prueba encriptación de teléfono"""
        phone = "+1 (555) 123-4567"
        
        encrypted = encryption_service.encrypt_phone(phone)
        decrypted = encryption_service.decrypt_phone(encrypted)

        # El teléfono original se mantiene (aunque se normaliza en el encriptado)
        assert encrypted != phone
        assert isinstance(decrypted, str)

    def test_encrypt_optional_none(self, encryption_service):
        """Prueba encriptación opcional con None"""
        result = encryption_service.encrypt_optional(None)
        assert result is None

    def test_encrypt_optional_value(self, encryption_service):
        """Prueba encriptación opcional con valor"""
        value = "sensitive_data"
        
        encrypted = encryption_service.encrypt_optional(value)
        
        assert encrypted is not None
        assert encrypted != value

    def test_decrypt_optional_none(self, encryption_service):
        """Prueba desencriptación opcional con None"""
        result = encryption_service.decrypt_optional(None)
        assert result is None

    def test_decrypt_optional_value(self, encryption_service):
        """Prueba desencriptación opcional con valor"""
        value = "sensitive_data"
        
        encrypted = encryption_service.encrypt_optional(value)
        decrypted = encryption_service.decrypt_optional(encrypted)
        
        assert decrypted == value

    def test_encrypt_dict(self, encryption_service):
        """Prueba encriptación de diccionario"""
        data = {
            "id": 1,
            "name": "John",
            "email": "john@example.com",
            "phone": "555-1234"
        }
        
        encrypted = encryption_service.encrypt_dict(
            data,
            fields_to_encrypt=["email", "phone"]
        )

        assert encrypted["id"] == 1  # No encriptado
        assert encrypted["name"] == "John"  # No encriptado
        assert encrypted["email"] != data["email"]  # Encriptado
        assert encrypted["phone"] != data["phone"]  # Encriptado

    def test_decrypt_dict(self, encryption_service):
        """Prueba desencriptación de diccionario"""
        original_data = {
            "id": 1,
            "name": "Jane",
            "email": "jane@example.com"
        }
        
        encrypted = encryption_service.encrypt_dict(
            original_data,
            fields_to_encrypt=["email"]
        )
        
        decrypted = encryption_service.decrypt_dict(
            encrypted,
            fields_to_decrypt=["email"]
        )

        assert decrypted["id"] == original_data["id"]
        assert decrypted["name"] == original_data["name"]
        assert decrypted["email"] == original_data["email"]

    def test_encrypt_invalid_type(self, encryption_service):
        """Prueba que encriptar tipo inválido lanza error"""
        with pytest.raises(TypeError):
            encryption_service.encrypt(123)

    def test_decrypt_invalid_token(self, encryption_service):
        """Prueba que desencriptar token inválido lanza error"""
        with pytest.raises(InvalidToken):
            encryption_service.decrypt("invalid_encrypted_data")

    def test_encrypt_empty_string(self, encryption_service):
        """Prueba encriptación de string vacío"""
        plaintext = ""
        
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypt_unicode(self, encryption_service):
        """Prueba encriptación de caracteres Unicode"""
        plaintext = "Hola mundo! 你好 مرحبا 🎉"
        
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypt_long_string(self, encryption_service):
        """Prueba encriptación de strings largos"""
        plaintext = "A" * 10000
        
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)

        assert decrypted == plaintext

    def test_different_keys_different_results(self):
        """Prueba que diferentes claves producen diferentes resultados"""
        plaintext = "secret"
        
        service1 = EncryptionService()
        service2 = EncryptionService(EncryptionService.generate_key())

        encrypted1 = service1.encrypt(plaintext)
        encrypted2 = service2.encrypt(plaintext)

        # Aunque el plaintext es igual, los cifertexts son diferentes
        assert encrypted1 != encrypted2

    def test_multiple_encryptions_same_service(self, encryption_service):
        """Prueba que múltiples encriptaciones del mismo valor producen diferentes resultados"""
        plaintext = "test_data"
        
        encrypted1 = encryption_service.encrypt(plaintext)
        encrypted2 = encryption_service.encrypt(plaintext)

        # Fernet incluye IV y timestamp, así que nunca son iguales
        assert encrypted1 != encrypted2
        
        # Pero ambos desencriptan al mismo valor
        assert encryption_service.decrypt(encrypted1) == plaintext
        assert encryption_service.decrypt(encrypted2) == plaintext
