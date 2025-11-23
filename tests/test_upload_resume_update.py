"""
Test para validar que el endpoint upload_resume permite actualizar
perfiles existentes en lugar de rechazarlos con error 409
"""
import json
import requests
from pathlib import Path
import time

# Configuración
BASE_URL = "http://127.0.0.1:8000"
API_KEY = "kFJ4ZLOhnpfakVMgbeb1Mw_4SZWMLaqcxGIavmu-VxnWf-q69HhwIn0Hj-BPhnbCxA"

HEADERS = {
    "accept": "application/json",
    "x-api-key": API_KEY
}

# Datos del estudiante
STUDENT_DATA = {
    "name": "Henry",
    "email": "henryspark@gmail.com"
}

# Crear un archivo TXT de prueba con contenido de CV
CV_PATH = Path("/tmp/CV_Test.txt")

cv_content = """
HENRY SPARK
henryspark@gmail.com

PROFESSIONAL SUMMARY
Experienced Python Developer with expertise in JavaScript and team leadership

TECHNICAL SKILLS
- Python (Advanced)
- JavaScript (Expert)
- FastAPI
- PostgreSQL
- React
- Docker
- AWS

SOFT SKILLS
- Team Leadership
- Problem-solving
- Communication
- Project Management
- Adaptability

PROJECTS
- E-commerce Platform: Built a full-stack web application using Python/FastAPI and React
- NLP Service: Implemented natural language processing system for resume analysis
- Job Matching Algorithm: Developed machine learning model for candidate-job matching

EXPERIENCE
Senior Developer at Tech Company (2022-Present)
- Led team of 5 developers
- Designed system architecture
- Implemented CI/CD pipelines

Developer at StartUp (2020-2022)
- Built REST APIs with FastAPI
- Worked on microservices architecture
"""

CV_PATH.write_text(cv_content)

print("=" * 80)
print("TEST: Upload Resume con Actualización de Perfil Existente")
print("=" * 80)

# Test 1: Primer upload (crear nuevo)
print("\n[TEST 1] Primer upload - Crear nuevo estudiante")
print("-" * 80)

with open(CV_PATH, "rb") as f:
    files = {
        "meta": (None, json.dumps(STUDENT_DATA)),
        "file": ("CV_Test.txt", f, "text/plain")
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/students/upload_resume",
        headers=HEADERS,
        files=files
    )

print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 200:
    first_response = response.json()
    student_id = first_response.get("student", {}).get("id")
    initial_skills = first_response.get("extracted_skills", [])
    print(f"\n✅ Creación exitosa - Student ID: {student_id}")
    print(f"   Habilidades extraídas: {initial_skills}")
else:
    print(f"❌ Error en creación: {response.status_code}")
    exit(1)

# Esperar un poco
time.sleep(1)

# Test 2: Segundo upload (actualizar existente)
print("\n[TEST 2] Segundo upload - Actualizar estudiante existente")
print("-" * 80)

# Datos actualizados
UPDATED_STUDENT_DATA = {
    "name": "Henry Spark",
    "email": "henryspark@gmail.com"  # Mismo email
}

with open(CV_PATH, "rb") as f:
    files = {
        "meta": (None, json.dumps(UPDATED_STUDENT_DATA)),
        "file": ("CV_Test.txt", f, "text/plain")
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/students/upload_resume",
        headers=HEADERS,
        files=files
    )

print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 200:
    second_response = response.json()
    student_id_updated = second_response.get("student", {}).get("id")
    updated_name = second_response.get("student", {}).get("name")
    updated_skills = second_response.get("extracted_skills", [])
    
    print(f"\n✅ Actualización exitosa - Student ID: {student_id_updated}")
    print(f"   Nombre actualizado: {updated_name}")
    print(f"   Habilidades extraídas: {updated_skills}")
    
    if student_id_updated == student_id:
        print(f"   ✅ ID consistente (mismo estudiante actualizado)")
    else:
        print(f"   ❌ ID diferente (se creó nuevo estudiante)")
elif response.status_code == 409:
    print(f"❌ Error 409: El endpoint sigue rechazando el email duplicado")
    print("   La corrección no se aplicó correctamente")
else:
    print(f"❌ Error inesperado: {response.status_code}")

print("\n" + "=" * 80)
print("FIN DE TESTS")
print("=" * 80)
