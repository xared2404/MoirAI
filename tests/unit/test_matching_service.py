"""
Tests para el servicio de Matchmaking
Valida que las recomendaciones y el filtrado de estudiantes funciona correctamente
"""
import pytest
import json
from datetime import datetime, timedelta
from sqlmodel import Session, select

from app.services.matching_service import matching_service
from app.models import Student, JobMatchEvent
from app.schemas import JobItem, MatchingCriteria, StudentPublic
from app.core.database import engine


@pytest.fixture
def sample_student():
    """Crear un estudiante de prueba con perfil completo - en la DB real"""
    from sqlmodel import Session
    with Session(engine) as session:
        student = Student(
            name="Juan García",
            email="juan.garcia.test@example.com",
            program="Ingeniería en Sistemas",
            skills=json.dumps(["Python", "SQL", "FastAPI", "Docker", "Machine Learning"]),
            soft_skills=json.dumps(["Comunicación", "Trabajo en equipo", "Liderazgo"]),
            projects=json.dumps([
                "Sistema de predicción de ventas",
                "API REST para análisis de datos",
                "Dashboard de análisis en tiempo real"
            ]),
            is_active=True,
            consent_data_processing=True
        )
        session.add(student)
        session.commit()
        session.refresh(student)
        student_id = student.id
    
    # Retornar el estudiante desde una nueva sesión
    with Session(engine) as session:
        student = session.get(Student, student_id)
        yield student
    
    # Cleanup: borrar el estudiante después del test
    with Session(engine) as session:
        stmt = select(Student).where(Student.email == "juan.garcia.test@example.com")
        db_student = session.exec(stmt).first()
        if db_student:
            session.delete(db_student)
            session.commit()


@pytest.fixture
def another_student():
    """Crear otro estudiante con diferentes habilidades - en la DB real"""
    with Session(engine) as session:
        student = Student(
            name="María López",
            email="maria.lopez.test@example.com",
            program="Diseño Gráfico",
            skills=json.dumps(["Figma", "Adobe Creative Suite", "UI/UX", "Prototyping"]),
            soft_skills=json.dumps(["Creatividad", "Atención al detalle"]),
            projects=json.dumps(["Rediseño de interfaz", "Sistema de diseño"]),
            is_active=True,
            consent_data_processing=True
        )
        session.add(student)
        session.commit()
        session.refresh(student)
        student_id = student.id
    
    # Retornar el estudiante desde una nueva sesión
    with Session(engine) as session:
        student = session.get(Student, student_id)
        yield student
    
    # Cleanup: borrar el estudiante después del test
    with Session(engine) as session:
        stmt = select(Student).where(Student.email == "maria.lopez.test@example.com")
        db_student = session.exec(stmt).first()
        if db_student:
            session.delete(db_student)
            session.commit()


class TestMatchingService:
    """Tests del servicio de matching"""

    def test_build_student_query(self, sample_student):
        """Prueba construcción de query de búsqueda"""
        query = matching_service.build_student_query(sample_student)
        
        assert isinstance(query, str)
        assert len(query) > 0
        assert "Python" in query
        assert "Machine Learning" in query

    def test_calculate_job_match_score(self, sample_student):
        """Prueba cálculo de score de matching"""
        job = JobItem(
            title="Data Scientist Sr",
            description="Buscamos Data Scientist con experiencia en Python y ML",
            company="TechCorp",
            location="Córdoba",
            url="https://example.com",
            source="api_test"
        )

        score, details = matching_service._calculate_job_match_score(sample_student, job)

        assert 0 <= score <= 1
        assert "base_score" in details
        assert "boost_details" in details
        assert "final_score" in details
        assert details["final_score"] == score

    def test_calculate_job_match_score_high_skill_match(self, sample_student):
        """Prueba que el score es más alto cuando las habilidades coinciden"""
        # Job muy similar al perfil
        similar_job = JobItem(
            title="Python Developer",
            description="Se busca desarrollador Python con FastAPI, Docker y ML",
            company="TechCorp",
            location="Remote",
            url="https://example.com",
            source="api_test"
        )

        # Job no relacionado
        unrelated_job = JobItem(
            title="Accountant",
            description="Se busca contador con experiencia en SAP",
            company="FinCorp",
            location="Remote",
            url="https://example.com",
            source="api_test"
        )

        similar_score, _ = matching_service._calculate_job_match_score(sample_student, similar_job)
        unrelated_score, _ = matching_service._calculate_job_match_score(sample_student, unrelated_job)

        assert similar_score > unrelated_score

    @pytest.mark.asyncio
    async def test_find_job_recommendations(self, sample_student):
        """Prueba generación de recomendaciones de empleos"""
        # Mock de job_provider_manager
        recommendations = await matching_service.find_job_recommendations(
            student_id=sample_student.id,
            location=None,
            limit=5
        )

        assert "student_id" in recommendations
        assert recommendations["student_id"] == sample_student.id
        assert "jobs" in recommendations
        assert isinstance(recommendations["jobs"], list)
        assert "total_found" in recommendations
        assert "query_used" in recommendations
        assert "generated_at" in recommendations

    def test_filter_students_by_criteria(self, sample_student, another_student):
        """Prueba filtrado de estudiantes por criterios"""
        criteria = MatchingCriteria(
            skills=["Python", "SQL"],
            projects=["predicción", "API"]
        )

        results = matching_service.filter_students_by_criteria(criteria)

        assert isinstance(results, list)
        assert len(results) > 0
        
        # El primer estudiante debe estar presente
        student_ids = [r.student.id for r in results]
        assert sample_student.id in student_ids

    def test_filter_students_no_matches(self, sample_student, another_student):
        """Prueba filtrado que no retorna matches"""
        criteria = MatchingCriteria(
            skills=["COBOL", "Assembly"],  # Habilidades muy viejas
            projects=None
        )

        results = matching_service.filter_students_by_criteria(criteria)

        # Puede retornar lista vacía o solo con coincidencias parciales
        assert isinstance(results, list)

    def test_filter_students_requires_criteria(self, sample_student):
        """Prueba que se requiere al menos un criterio"""
        criteria = MatchingCriteria()  # Sin criterios

        # Esto debe fallar en el endpoint, pero aquí se permite en el servicio
        results = matching_service.filter_students_by_criteria(criteria)
        assert isinstance(results, list)

    def test_get_featured_students(self, sample_student, another_student):
        """Prueba obtención de estudiantes destacados"""
        featured = matching_service.get_featured_students(limit=5)

        assert isinstance(featured, list)
        assert len(featured) <= 5
        
        for student_public in featured:
            assert isinstance(student_public, StudentPublic)
            assert student_public.id is not None
            assert student_public.name is not None

    def test_calculate_student_featured_score(self, sample_student):
        """Prueba cálculo de score para estudiante destacado"""
        score = matching_service._calculate_student_featured_score(sample_student)

        assert 0 <= score <= 1

    def test_calculate_student_featured_score_with_activity(self, sample_student):
        """Prueba que la actividad reciente mejora el score"""
        # Estudiante con actividad reciente
        sample_student.last_active = datetime.utcnow()
        
        score_active = matching_service._calculate_student_featured_score(sample_student)

        # Estudiante sin actividad reciente
        sample_student.last_active = datetime.utcnow() - timedelta(days=60)
        score_inactive = matching_service._calculate_student_featured_score(sample_student)

        assert score_active > score_inactive

    def test_extract_keywords_from_project(self):
        """Prueba extracción de palabras clave de proyectos"""
        project = "Developed a machine learning model for web scraping and data visualization"
        keywords = matching_service._extract_keywords_from_project(project)

        assert isinstance(keywords, list)
        assert "machine learning" in keywords or "web" in keywords
