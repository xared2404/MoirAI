#!/usr/bin/env python3
"""
Demo Interactiva: Uso de Encriptación de Campos Sensibles
Muestra cómo funciona la encriptación en MoirAI
"""

import os
import json
from app.utils.encryption import EncryptionService, encryption_service, get_encryption_service

def print_section(title: str):
    """Imprimir sección con formato"""
    print(f"\n{'='*70}")
    print(f"  🔐 {title}")
    print(f"{'='*70}\n")

def demo_1_generar_claves():
    """Demo 1: Generar claves de encriptación"""
    print_section("DEMO 1: Generar Claves de Encriptación")
    
    print("1️⃣  Opción A: Clave aleatoria")
    key1 = EncryptionService.generate_key()
    print(f"   Clave generada: {key1[:50]}...")
    print(f"   Longitud: {len(key1)} caracteres")
    print(f"   ℹ️  Esta clave es ÚNICA y segura")
    
    print("\n2️⃣  Opción B: Clave desde contraseña")
    password = "mi_contraseña_super_segura_123"
    key2, salt = EncryptionService.generate_key_from_password(password)
    print(f"   Contraseña: {password}")
    print(f"   Clave derivada: {key2[:50]}...")
    print(f"   Salt: {salt}")
    print(f"   ℹ️  Misma contraseña + salt = misma clave (reproducible)")
    
    print("\n3️⃣  Cómo guardar la clave")
    print(f'   Agregar a .env: ENCRYPTION_KEY="{key1}"')
    print(f"   ✅ Ahora el servicio la usará automáticamente")

def demo_2_encriptacion_basica():
    """Demo 2: Encriptación básica"""
    print_section("DEMO 2: Encriptación Básica de Texto")
    
    # Crear instancia del servicio
    service = get_encryption_service()
    
    test_data = [
        "información sensible",
        "juan.perez@example.com",
        "+1 (555) 123-4567",
        "Calle Principal 123, Apartamento 456",
        "12-345-6789",
        "Contraseña temporal: P@ssw0rd123"
    ]
    
    for i, plaintext in enumerate(test_data, 1):
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        print(f"{i}. Dato original:")
        print(f"   {plaintext}")
        print(f"   Encriptado: {encrypted[:60]}...")
        print(f"   Desencriptado: {decrypted}")
        print(f"   ✅ Match: {plaintext == decrypted}\n")

def demo_3_campos_especializados():
    """Demo 3: Encriptación de campos especializados"""
    print_section("DEMO 3: Métodos Especializados")
    
    service = get_encryption_service()
    
    print("📧 Encriptación de EMAILS:")
    emails = ["student@university.edu", "USER@COMPANY.COM", "admin@UNRC.EDU.AR"]
    for email in emails:
        encrypted = service.encrypt_email(email)
        decrypted = service.decrypt_email(encrypted)
        print(f"   • {email} → {encrypted[:50]}... → {decrypted}")
    
    print("\n📱 Encriptación de TELÉFONOS:")
    phones = ["+1 (555) 123-4567", "555-1234", "(011) 4567-8900"]
    for phone in phones:
        encrypted = service.encrypt_phone(phone)
        decrypted = service.decrypt_phone(encrypted)
        print(f"   • {phone} → {encrypted[:50]}... → {decrypted}")

def demo_4_valores_opcionales():
    """Demo 4: Valores opcionales (None-safe)"""
    print_section("DEMO 4: Encriptación de Valores Opcionales (None-safe)")
    
    service = get_encryption_service()
    
    print("Escenario: Algunos estudiantes pueden no tener teléfono\n")
    
    test_values = [
        ("juan@example.com", "+1-555-1234"),
        ("maria@example.com", None),
        ("pedro@example.com", None),
    ]
    
    for email, phone in test_values:
        encrypted_email = service.encrypt_email(email)
        encrypted_phone = service.encrypt_optional(phone)  # None-safe
        
        print(f"Estudiante: {email}")
        print(f"  Email encriptado: {encrypted_email[:50]}...")
        print(f"  Teléfono encriptado: {encrypted_phone}")
        print(f"  ✅ Sin errores aunque phone sea None\n")

def demo_5_diccionarios():
    """Demo 5: Encriptación de diccionarios"""
    print_section("DEMO 5: Encriptación de Diccionarios Completos")
    
    service = get_encryption_service()
    
    # Datos de un estudiante
    student_data = {
        "id": 1,
        "name": "Juan Pérez García",
        "email": "juan.perez@university.edu",
        "phone": "+1 (555) 123-4567",
        "address": "Calle Principal 123, Apto 456",
        "university": "UNRC",
        "program": "Ingeniería en Sistemas",
        "ssn": "12-345-6789",
        "birth_date": "1998-05-15"
    }
    
    print("📋 Datos ANTES (en claro):")
    print(json.dumps(student_data, indent=2, ensure_ascii=False))
    
    # Encriptar campos sensibles
    sensitive_fields = ["email", "phone", "address", "ssn", "birth_date"]
    encrypted_data = service.encrypt_dict(student_data, sensitive_fields)
    
    print(f"\n🔒 Datos ENCRIPTADOS (solo campos sensibles):")
    encrypted_display = encrypted_data.copy()
    for field in sensitive_fields:
        if encrypted_data[field]:
            encrypted_display[field] = encrypted_data[field][:50] + "..."
    print(json.dumps(encrypted_display, indent=2, ensure_ascii=False))
    
    # Desencriptar
    decrypted_data = service.decrypt_dict(encrypted_data, sensitive_fields)
    
    print(f"\n✅ Datos DESENCRIPTADOS (recuperados):")
    print(json.dumps(decrypted_data, indent=2, ensure_ascii=False))
    
    print(f"\n✔️  Verificación: Datos originales == Datos desencriptados")
    print(f"   {student_data == decrypted_data}")

def demo_6_flujo_completo():
    """Demo 6: Flujo completo de registro y lectura"""
    print_section("DEMO 6: Flujo Completo (Registro → BD → Lectura)")
    
    service = get_encryption_service()
    
    print("📝 PASO 1: Usuario se registra con sus datos")
    user_input = {
        "name": "María González",
        "email": "maria.gonzalez@university.edu",
        "phone": "+1 (555) 987-6543"
    }
    print(json.dumps(user_input, indent=2, ensure_ascii=False))
    
    print("\n🔐 PASO 2: API encripta datos antes de guardar en BD")
    bd_record = service.encrypt_dict(
        user_input,
        fields_to_encrypt=["email", "phone"]
    )
    print("En la base de datos se guarda:")
    for key, value in bd_record.items():
        if isinstance(value, str) and len(value) > 50:
            print(f"  {key}: {value[:50]}...")
        else:
            print(f"  {key}: {value}")
    
    print("\n📖 PASO 3: Usuario solicita su perfil")
    print(f"GET /api/v1/students/{1}")
    
    print("\n🔓 PASO 4: API desencripta antes de devolver")
    api_response = service.decrypt_dict(
        bd_record,
        fields_to_decrypt=["email", "phone"]
    )
    print("Respuesta API (usuario ve sus datos):")
    print(json.dumps(api_response, indent=2, ensure_ascii=False))
    
    print("\n✅ Nota: Los datos viajan encriptados en tránsito (TLS 1.3)")
    print("   ✅ Los datos se guardan encriptados en BD")
    print("   ✅ El usuario recibe sus datos legibles")

def demo_7_seguridad():
    """Demo 7: Validaciones de seguridad"""
    print_section("DEMO 7: Validaciones de Seguridad")
    
    service = get_encryption_service()
    
    print("1️⃣  Encriptaciones del mismo dato producen resultados diferentes:")
    plaintext = "secreto"
    enc1 = service.encrypt(plaintext)
    enc2 = service.encrypt(plaintext)
    print(f"   Encriptación 1: {enc1[:50]}...")
    print(f"   Encriptación 2: {enc2[:50]}...")
    print(f"   ¿Son iguales? {enc1 == enc2} ✅ (No = más seguro)")
    
    print(f"\n2️⃣  Pero ambos desencriptan al mismo valor:")
    dec1 = service.decrypt(enc1)
    dec2 = service.decrypt(enc2)
    print(f"   Desencriptación 1: {dec1}")
    print(f"   Desencriptación 2: {dec2}")
    print(f"   ¿Son iguales? {dec1 == dec2} ✅")
    
    print(f"\n3️⃣  Diferentes claves producen datos incompatibles:")
    key1 = EncryptionService.generate_key()
    key2 = EncryptionService.generate_key()
    service1 = EncryptionService(key1)
    service2 = EncryptionService(key2)
    
    encrypted_with_key1 = service1.encrypt("dato importante")
    try:
        service2.decrypt(encrypted_with_key1)
        print("   ❌ Service2 pudo desencriptar con key1 (PROBLEMA)")
    except Exception as e:
        print(f"   ✅ Service2 NO puede desencriptar (esperado)")
        print(f"   Error: {type(e).__name__}")

def demo_8_casos_uso():
    """Demo 8: Casos de uso en MoirAI"""
    print_section("DEMO 8: Casos de Uso en MoirAI")
    
    print("1️⃣  CASO: Registro de Estudiante")
    print("   • Estudiante ingresa email y teléfono")
    print("   • API encripta antes de guardar")
    print("   • En BD: datos encriptados")
    print("   • Al leer perfil: API desencripta")
    
    print("\n2️⃣  CASO: Matchmaking (búsqueda de candidatos)")
    print("   • Empresa busca por skills: 'Python, JavaScript'")
    print("   • API busca en campos NO sensibles (skills)")
    print("   • Retorna perfiles sin desencriptar datos personales")
    print("   • O desencripta solo si empresa tiene permiso")
    
    print("\n3️⃣  CASO: Admin Dashboard")
    print("   • Admin solicita reporte de estudiantes")
    print("   • API retorna: ID, nombre, carrera")
    print("   • Campos sensibles NO se incluyen (o anonimizados)")
    
    print("\n4️⃣  CASO: Auditoría y Cumplimiento")
    print("   • Logs guardan: usuario_id, acción, timestamp")
    print("   • NUNCA guardan: emails, teléfonos")
    print("   • Si se necesita, se guardan HASHES, no valores")
    
    print("\n5️⃣  CASO: GDPR/LFPDPPP - Derecho al olvido")
    print("   • Usuario solicita eliminar sus datos")
    print("   • Se eliminan registros completamente")
    print("   • Logs pueden mantener referencias anonimizadas")

def print_menu():
    """Imprimir menú de opciones"""
    print("\n" + "="*70)
    print("  🔐 DEMOS DE ENCRIPTACIÓN EN MOIRAI")
    print("="*70)
    print("\n¿Qué demo te gustaría ver?\n")
    print("  1. Generar claves de encriptación")
    print("  2. Encriptación básica de texto")
    print("  3. Métodos especializados (email, teléfono)")
    print("  4. Valores opcionales (None-safe)")
    print("  5. Encriptación de diccionarios")
    print("  6. Flujo completo (Registro → BD → Lectura)")
    print("  7. Validaciones de seguridad")
    print("  8. Casos de uso en MoirAI")
    print("  9. Ver todas las demos")
    print("  0. Salir")
    print()

def run_all_demos():
    """Ejecutar todas las demos"""
    demos = [
        demo_1_generar_claves,
        demo_2_encriptacion_basica,
        demo_3_campos_especializados,
        demo_4_valores_opcionales,
        demo_5_diccionarios,
        demo_6_flujo_completo,
        demo_7_seguridad,
        demo_8_casos_uso,
    ]
    
    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"\n❌ Error en demo: {e}")
            import traceback
            traceback.print_exc()
        
        input("\n[Presiona Enter para continuar...]")

def main():
    """Menú principal interactivo"""
    demos = {
        "1": ("Generar claves", demo_1_generar_claves),
        "2": ("Encriptación básica", demo_2_encriptacion_basica),
        "3": ("Métodos especializados", demo_3_campos_especializados),
        "4": ("Valores opcionales", demo_4_valores_opcionales),
        "5": ("Encriptación de diccionarios", demo_5_diccionarios),
        "6": ("Flujo completo", demo_6_flujo_completo),
        "7": ("Validaciones de seguridad", demo_7_seguridad),
        "8": ("Casos de uso en MoirAI", demo_8_casos_uso),
        "9": ("Ver todas", run_all_demos),
    }
    
    try:
        while True:
            print_menu()
            choice = input("Ingresa tu opción: ").strip()
            
            if choice == "0":
                print("\n👋 ¡Hasta luego!\n")
                break
            
            if choice in demos:
                title, demo_func = demos[choice]
                print(f"\n▶️  Ejecutando: {title}")
                try:
                    demo_func()
                except Exception as e:
                    print(f"\n❌ Error: {e}")
                    import traceback
                    traceback.print_exc()
                
                if choice != "9":
                    input("\n[Presiona Enter para volver al menú...]")
            else:
                print("❌ Opción no válida. Intenta de nuevo.")
    
    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego!\n")

if __name__ == "__main__":
    main()
