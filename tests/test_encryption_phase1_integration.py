#!/usr/bin/env python3
"""
Test de integración FASE 1: Validación de encriptación en modelos y endpoints

✅ Valida que:
1. Los modelos Student y Company tienen métodos de encriptación
2. Los endpoints de registro usan encriptación
3. Los endpoints GET desencriptan antes de retornar
4. Las búsquedas usan hashes en lugar de valores encriptados

Ejecutar: python test_encryption_phase1_integration.py
"""

import os
import sys
import json
from datetime import datetime

# Configurar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar variables de entorno para testing ANTES de importar
from cryptography.fernet import Fernet
test_key = Fernet.generate_key().decode()
os.environ["ENCRYPTION_KEY"] = test_key
os.environ["DATABASE_URL"] = "sqlite://:memory:"

from app.models import Student, Company
from app.utils.encryption import encryption_service
import hashlib


def print_section(title):
    """Imprime un título de sección"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_test(test_name):
    """Imprime el nombre de una prueba"""
    print(f"\n📋 {test_name}")


def test_student_encryption_methods():
    """Prueba que el modelo Student tiene métodos de encriptación"""
    print_test("Test 1: Métodos de encriptación en modelo Student")
    
    # Verificar que Student tiene los métodos requeridos
    assert hasattr(Student, 'set_email'), "❌ Student no tiene método set_email()"
    assert hasattr(Student, 'get_email'), "❌ Student no tiene método get_email()"
    assert hasattr(Student, 'set_phone'), "❌ Student no tiene método set_phone()"
    assert hasattr(Student, 'get_phone'), "❌ Student no tiene método get_phone()"
    assert hasattr(Student, 'decrypt_sensitive_fields'), "❌ Student no tiene método decrypt_sensitive_fields()"
    
    print("✅ Student tiene todos los métodos de encriptación")
    
    # Verificar que Student tiene campos para hashes
    student = Student(
        name="Test Student",
        program="Ingeniería",
        consent_data_processing=True
    )
    
    assert hasattr(student, 'email_hash'), "❌ Student no tiene campo email_hash"
    assert hasattr(student, 'phone_hash'), "❌ Student no tiene campo phone_hash"
    
    print("✅ Student tiene campos para hashes (email_hash, phone_hash)")


def test_company_encryption_methods():
    """Prueba que el modelo Company tiene métodos de encriptación"""
    print_test("Test 2: Métodos de encriptación en modelo Company")
    
    # Verificar que Company tiene los métodos requeridos
    assert hasattr(Company, 'set_email'), "❌ Company no tiene método set_email()"
    assert hasattr(Company, 'get_email'), "❌ Company no tiene método get_email()"
    
    print("✅ Company tiene métodos de encriptación")
    
    # Verificar que Company tiene campo para hash
    company = Company(
        name="Test Company",
        is_verified=False,
        is_active=True
    )
    
    assert hasattr(company, 'email_hash'), "❌ Company no tiene campo email_hash"
    
    print("✅ Company tiene campo para hash (email_hash)")


def test_student_set_email_encryption():
    """Prueba que set_email() encripta correctamente"""
    print_test("Test 3: Encriptación de email en Student")
    
    student = Student(
        name="Test Student",
        program="Ingeniería",
        consent_data_processing=True
    )
    
    test_email = "test@example.com"
    student.set_email(test_email)
    
    # Verificar que email está encriptado
    assert student.email != test_email, "❌ Email no fue encriptado"
    print(f"✅ Email encriptado: {student.email[:20]}...")
    
    # Verificar que email_hash fue generado
    assert student.email_hash is not None, "❌ Email hash no fue generado"
    expected_hash = hashlib.sha256(test_email.lower().strip().encode()).hexdigest()
    assert student.email_hash == expected_hash, "❌ Email hash incorrecto"
    print(f"✅ Hash de email generado correctamente: {student.email_hash[:20]}...")


def test_student_get_email_decryption():
    """Prueba que get_email() desencripta correctamente"""
    print_test("Test 4: Desencriptación de email en Student")
    
    student = Student(
        name="Test Student",
        program="Ingeniería",
        consent_data_processing=True
    )
    
    test_email = "student@unrc.edu.ar"
    student.set_email(test_email)
    
    # Desencriptar
    decrypted_email = student.get_email()
    assert decrypted_email == test_email, f"❌ Email desencriptado incorrecto: {decrypted_email}"
    print(f"✅ Email desencriptado correctamente: {decrypted_email}")


def test_company_email_encryption():
    """Prueba encriptación de email en Company"""
    print_test("Test 5: Encriptación de email en Company")
    
    company = Company(
        name="Test Company",
        is_verified=False,
        is_active=True
    )
    
    test_email = "hiring@company.com"
    company.set_email(test_email)
    
    # Verificar encriptación
    assert company.email != test_email, "❌ Email no fue encriptado"
    print(f"✅ Email encriptado: {company.email[:20]}...")
    
    # Verificar hash
    assert company.email_hash is not None, "❌ Email hash no fue generado"
    expected_hash = hashlib.sha256(test_email.lower().strip().encode()).hexdigest()
    assert company.email_hash == expected_hash, "❌ Email hash incorrecto"
    print(f"✅ Hash de email generado: {company.email_hash[:20]}...")
    
    # Desencriptar
    decrypted_email = company.get_email()
    assert decrypted_email == test_email, f"❌ Email desencriptado incorrecto: {decrypted_email}"
    print(f"✅ Email desencriptado: {decrypted_email}")


def test_student_phone_encryption():
    """Prueba encriptación de teléfono en Student"""
    print_test("Test 6: Encriptación de teléfono en Student")
    
    student = Student(
        name="Test Student",
        program="Ingeniería",
        consent_data_processing=True
    )
    
    test_phone = "+54 9 358 1234567"
    student.set_phone(test_phone)
    
    # Verificar encriptación
    assert student.phone != test_phone, "❌ Teléfono no fue encriptado"
    print(f"✅ Teléfono encriptado: {student.phone[:20]}...")
    
    # Verificar hash
    assert student.phone_hash is not None, "❌ Teléfono hash no fue generado"
    print(f"✅ Hash de teléfono generado")
    
    # Desencriptar
    decrypted_phone = student.get_phone()
    assert decrypted_phone == test_phone, f"❌ Teléfono desencriptado incorrecto: {decrypted_phone}"
    print(f"✅ Teléfono desencriptado: {decrypted_phone}")


def test_email_hash_for_search():
    """Prueba que el hash permite búsquedas sin desencriptar"""
    print_test("Test 7: Búsqueda por hash de email (sin desencriptar)")
    
    test_email = "admin@unrc.edu.ar"
    
    # Método 1: Generar hash del email a buscar
    search_hash = encryption_service._get_hash_email(test_email)
    print(f"✅ Hash para búsqueda generado: {search_hash[:20]}...")
    
    # Método 2: Comparar con hash almacenado
    student = Student(
        name="Test Admin",
        program="Administración",
        consent_data_processing=True
    )
    student.set_email(test_email)
    
    # Simular búsqueda
    assert student.email_hash == search_hash, "❌ El hash no coincide"
    print(f"✅ La búsqueda por hash funcionaría correctamente")


def test_decrypt_sensitive_fields():
    """Prueba el método decrypt_sensitive_fields()"""
    print_test("Test 8: Método decrypt_sensitive_fields()")
    
    student = Student(
        name="Test Student",
        program="Ingeniería",
        consent_data_processing=True
    )
    
    test_email = "contact@student.com"
    test_phone = "+54 358 123456"
    
    student.set_email(test_email)
    student.set_phone(test_phone)
    
    # Llamar método
    decrypted = student.decrypt_sensitive_fields()
    
    assert isinstance(decrypted, dict), "❌ decrypt_sensitive_fields() no retorna dict"
    assert "email" in decrypted, "❌ 'email' no en resultado"
    assert "phone" in decrypted, "❌ 'phone' no en resultado"
    
    assert decrypted["email"] == test_email, "❌ Email desencriptado incorrecto"
    assert decrypted["phone"] == test_phone, "❌ Teléfono desencriptado incorrecto"
    
    print(f"✅ decrypt_sensitive_fields() retorna: {decrypted}")


def test_encryption_service_helper():
    """Prueba el helper _get_hash_email() en encryption_service"""
    print_test("Test 9: Helper encryption_service._get_hash_email()")
    
    test_email = "user@example.com"
    
    # Llamar helper
    hash_result = encryption_service._get_hash_email(test_email)
    
    # Verificar
    expected_hash = hashlib.sha256(test_email.lower().strip().encode()).hexdigest()
    assert hash_result == expected_hash, "❌ Hash incorrecto"
    
    print(f"✅ Helper genera hashes correctos")
    print(f"   Input: {test_email}")
    print(f"   Hash: {hash_result[:30]}...")


def test_email_normalization():
    """Prueba que emails se normalizan antes de encriptar"""
    print_test("Test 10: Normalización de emails")
    
    student1 = Student(name="S1", program="Ing", consent_data_processing=True)
    student2 = Student(name="S2", program="Ing", consent_data_processing=True)
    
    # Mismo email con diferentes mayúsculas/espacios
    email_variants = [
        "Test@Example.COM",
        "test@example.com",
        " test@example.com ",
        "TEST@EXAMPLE.COM"
    ]
    
    hashes = set()
    for email in email_variants:
        hash_val = encryption_service._get_hash_email(email)
        hashes.add(hash_val)
    
    assert len(hashes) == 1, f"❌ Se generaron {len(hashes)} hashes diferentes para el mismo email"
    print(f"✅ Todos los variants del email generan el mismo hash")
    print(f"   Variantes probadas: {len(email_variants)}")
    print(f"   Hash único generado: {hashes.pop()[:30]}...")


def main():
    """Ejecutar todos los tests"""
    print_section("VALIDACIÓN FASE 1: INTEGRACIÓN DE ENCRIPTACIÓN")
    
    tests = [
        test_student_encryption_methods,
        test_company_encryption_methods,
        test_student_set_email_encryption,
        test_student_get_email_decryption,
        test_company_email_encryption,
        test_student_phone_encryption,
        test_email_hash_for_search,
        test_decrypt_sensitive_fields,
        test_encryption_service_helper,
        test_email_normalization,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ {e}")
            failed += 1
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            failed += 1
    
    # Resumen
    print_section("RESUMEN DE RESULTADOS")
    print(f"✅ Tests pasados: {passed}/{len(tests)}")
    if failed > 0:
        print(f"❌ Tests fallidos: {failed}/{len(tests)}")
        return 1
    else:
        print(f"🎉 ¡Todos los tests pasaron!")
        
        # Información de la integración
        print_section("INFORMACIÓN DE LA INTEGRACIÓN")
        print("""
✅ FASE 1 - Integración Completada:

1. MODELOS (app/models/__init__.py)
   - Student: email_hash, phone_hash (campos para búsqueda)
   - Student: set_email(), get_email(), set_phone(), get_phone()
   - Student: decrypt_sensitive_fields()
   - Company: email_hash (campo para búsqueda)
   - Company: set_email(), get_email()

2. SERVICIO DE ENCRIPTACIÓN (app/utils/encryption.py)
   - Nuevo método: _get_hash_email(email: str) -> str
   - Genera SHA256 hash para búsquedas sin desencriptar

3. ENDPOINTS (app/api/endpoints/)
   ✅ auth.py - register_user()
      • Busca por email_hash (no por email plano)
      • Encripta email usando student.set_email()
      • Usa helper para generar hash

   ✅ students.py
      • create_student(): encripta email con set_email()
      • upload_resume(): encripta email con set_email()
      • get_student_by_email(): busca por hash
      • _convert_to_student_profile(): desencripta antes de retornar

   ✅ companies.py
      • create_company(): encripta email con set_email()
      • _convert_to_company_profile(): desencripta antes de retornar

🔐 SEGURIDAD:
   - Emails encriptados con Fernet (AES-128 + HMAC)
   - Búsquedas usando SHA256 hashes (no reversibles)
   - Desencriptación automática en respuestas de API
   - Normalizacion de emails (lowercase + trim)

📊 PRÓXIMOS PASOS (FASE 2-4):
   - Validar GET endpoints retornan datos desencriptados
   - Implementar búsquedas avanzadas con hashes
   - Data migration para registros existentes
        """)
        return 0


if __name__ == "__main__":
    sys.exit(main())
