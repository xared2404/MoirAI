"""
Test de integración para validar el endpoint upload_resume
Prueba el flujo completo: crear estudiante y actualizar su perfil
"""
import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Datos de prueba
TEST_API_KEY = "kFJ4ZLOhnpfakVMgbeb1Mw_4SZWMLaqcxGIavmu-VxnWf-q69HhwIn0Hj-BPhnbCxA"
HEADERS = {
    "accept": "application/json",
    "x-api-key": TEST_API_KEY
}

TEST_CV_CONTENT = """
HENRY SPARK
henryspark+test@gmail.com

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
"""


@pytest.fixture
def test_cv_file(tmp_path):
    """Crear archivo de CV de prueba"""
    cv_path = tmp_path / "test_cv.txt"
    cv_path.write_text(TEST_CV_CONTENT)
    return cv_path


class TestUploadResumeEndpoint:
    """Suite de tests para el endpoint upload_resume"""
    
    def test_upload_resume_create_new_student(self, test_cv_file):
        """Test: Crear nuevo estudiante al subir CV"""
        with open(test_cv_file, "rb") as f:
            files = {
                "meta": (None, json.dumps({
                    "name": "Henry Test",
                    "email": "henrytest_new@example.com"
                })),
                "file": ("test_cv.txt", f, "text/plain")
            }
            
            response = client.post(
                "/api/v1/students/upload_resume",
                headers=HEADERS,
                files=files
            )
        
        # Validaciones
        assert response.status_code == 200, f"Esperado 200, obtenido {response.status_code}"
        
        data = response.json()
        assert "student" in data
        assert "extracted_skills" in data
        assert "extracted_soft_skills" in data
        assert "extracted_projects" in data
        assert "analysis_confidence" in data
        
        student = data["student"]
        assert student["name"] == "Henry Test"
        assert student["email"] == "henrytest_new@example.com"
        assert student["is_active"] == True
        
        # Validar extracción NLP
        skills = data["extracted_skills"]
        assert len(skills) > 0, "Debe extraer al menos una habilidad técnica"
        assert any("Python" in s or "python" in s.lower() for s in skills), "Debe detectar Python"
        
        soft_skills = data["extracted_soft_skills"]
        assert len(soft_skills) > 0, "Debe extraer al menos una habilidad blanda"
        
        projects = data["extracted_projects"]
        assert len(projects) > 0, "Debe extraer al menos un proyecto"
        
        confidence = data["analysis_confidence"]
        assert 0.0 <= confidence <= 1.0, "Confianza debe estar entre 0 y 1"
        
        return student["id"], student["email"]
    
    def test_upload_resume_update_existing_student(self, test_cv_file):
        """Test: Actualizar perfil al subir CV con email existente"""
        email = "henrytest_update@example.com"
        
        # 1️⃣ Primer upload - crear estudiante
        with open(test_cv_file, "rb") as f:
            files = {
                "meta": (None, json.dumps({
                    "name": "Henry Original",
                    "email": email
                })),
                "file": ("test_cv.txt", f, "text/plain")
            }
            
            response1 = client.post(
                "/api/v1/students/upload_resume",
                headers=HEADERS,
                files=files
            )
        
        assert response1.status_code == 200
        student1 = response1.json()["student"]
        original_id = student1["id"]
        original_skills_count = len(response1.json()["extracted_skills"])
        
        # 2️⃣ Segundo upload - actualizar estudiante
        with open(test_cv_file, "rb") as f:
            files = {
                "meta": (None, json.dumps({
                    "name": "Henry Updated",
                    "email": email  # Mismo email
                })),
                "file": ("test_cv.txt", f, "text/plain")
            }
            
            response2 = client.post(
                "/api/v1/students/upload_resume",
                headers=HEADERS,
                files=files
            )
        
        # Validaciones
        assert response2.status_code == 200, f"Esperado 200 en actualización, obtenido {response2.status_code}"
        
        student2 = response2.json()["student"]
        
        # El ID debe ser el mismo (mismo estudiante)
        assert student2["id"] == original_id, "El ID debe ser el mismo después de actualización"
        
        # El nombre debe estar actualizado
        assert student2["name"] == "Henry Updated", "El nombre debe haberse actualizado"
        
        # Las habilidades deben haberse analizado nuevamente
        skills2 = response2.json()["extracted_skills"]
        assert len(skills2) > 0, "Debe extraer habilidades en la actualización"
    
    def test_upload_resume_invalid_metadata(self, test_cv_file):
        """Test: Rechazar metadata inválida"""
        with open(test_cv_file, "rb") as f:
            files = {
                "meta": (None, "invalid json{"),  # JSON inválido
                "file": ("test_cv.txt", f, "text/plain")
            }
            
            response = client.post(
                "/api/v1/students/upload_resume",
                headers=HEADERS,
                files=files
            )
        
        assert response.status_code == 400, "Debe rechazar metadata inválida"
    
    def test_upload_resume_insufficient_permissions(self, test_cv_file):
        """Test: Rechazar acceso sin permisos suficientes"""
        # Usar headers sin API key o inválida
        headers_invalid = {"accept": "application/json"}
        
        with open(test_cv_file, "rb") as f:
            files = {
                "meta": (None, json.dumps({
                    "name": "Henry",
                    "email": "henry@example.com"
                })),
                "file": ("test_cv.txt", f, "text/plain")
            }
            
            response = client.post(
                "/api/v1/students/upload_resume",
                headers=headers_invalid,
                files=files
            )
        
        # Debe rechazar por falta de autenticación
        assert response.status_code in [401, 403, 500], "Debe rechazar sin credenciales válidas"
    
    def test_nlp_analysis_completeness(self, test_cv_file):
        """Test: Validar que el análisis NLP extrae todos los componentes"""
        with open(test_cv_file, "rb") as f:
            files = {
                "meta": (None, json.dumps({
                    "name": "Test User",
                    "email": "nlp_test@example.com"
                })),
                "file": ("test_cv.txt", f, "text/plain")
            }
            
            response = client.post(
                "/api/v1/students/upload_resume",
                headers=HEADERS,
                files=files
            )
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Validar estructura completa
        assert "student" in data
        assert "extracted_skills" in data
        assert "extracted_soft_skills" in data
        assert "extracted_projects" in data
        assert "analysis_confidence" in data
        
        # Validar que los datos se guardaron en el estudiante
        student = data["student"]
        assert len(student["skills"]) == len(data["extracted_skills"])
        assert len(student["soft_skills"]) == len(data["extracted_soft_skills"])
        assert len(student["projects"]) == len(data["extracted_projects"])


if __name__ == "__main__":
    # Ejecutar tests con pytest
    pytest.main([__file__, "-v", "--tb=short"])
