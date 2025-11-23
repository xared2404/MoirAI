"""
Tests de integración para HTML Parser
Pruebas end-to-end de parseo + validación + almacenamiento

✅ Ejecución: pytest tests/integration/test_html_parser_integration.py -v
"""

import pytest
from datetime import datetime
from app.services.html_parser_service import HTMLParserService, JobItem


@pytest.fixture
def parser():
    """Obtener instancia de parser"""
    return HTMLParserService()


@pytest.fixture
def sample_occ_style_html():
    """HTML realista estilo OCC.com.mx con separadores proper"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Data Engineer | OCC</title></head>
    <body>
        <h1 class="job-title">Data Engineer Senior</h1>
        <div class="company-name">Google Mexico</div>
        <div class="location">Mexico City, CDMX</div>
        <div id="job-main">
            <article class="job-description">
                <p>We are looking for a Senior Data Engineer to join our team.</p>
                
                <p><strong>Responsabilidades:</strong></p>
                <p>Design and build data pipelines using Apache Spark.</p>
                <p>Work with Python, Scala, and SQL.</p>
                <p>Manage PostgreSQL and MongoDB databases.</p>
                <p>Docker and Kubernetes for deployment.</p>
                <p>AWS and GCP experience required.</p>
                
                <p><strong>Requisitos:</strong></p>
                <p>5+ years of data engineering experience.</p>
                <p>Strong Python and SQL skills.</p>
                <p>Machine Learning basics.</p>
                <p>Experience with BigQuery and Spark.</p>
                
                <p><strong>Tipo de Posición:</strong> Full-time</p>
                <p><strong>Modalidad:</strong> Trabajo remoto y presencial (Híbrido)</p>
                <p><strong>Salario:</strong> $120,000 a $180,000 MXN por mes</p>
                <p><strong>Contacto:</strong> careers@google-mexico.com | +52 55 9876 5432</p>
            </article>
        </div>
    </body>
    </html>
    """


def test_full_parsing_pipeline(parser, sample_occ_style_html):
    """Test pipeline completo de parseo"""
    job = parser.parse_job_listing(
        sample_occ_style_html,
        external_job_id="occ_12345",
        source="occ.com.mx"
    )
    
    # Verificar campos básicos
    assert job.external_job_id == "occ_12345"
    assert job.title == "Data Engineer Senior"
    assert job.company == "Google Mexico"
    assert job.source == "occ.com.mx"
    
    # Verificar fields extraídos
    assert job.work_mode == "híbrido"
    assert job.job_type == "full-time"
    assert job.salary_min == 120000
    assert job.salary_max == 180000
    
    # Verificar skills extraídas
    expected_skills = ["Python", "Sql", "Spark", "Docker", "Kubernetes", 
                      "Aws", "Gcp", "Postgresql", "Mongodb", "Scala"]
    for skill in expected_skills:
        assert skill in job.skills, f"Skill {skill} no encontrada en {job.skills}"
    
    # Verificar contacto
    assert job.email == "careers@google-mexico.com"
    assert "+52" in job.phone


def test_parsing_and_validation_workflow(parser, sample_occ_style_html):
    """Test flujo completo: parseo + validación"""
    # Parsear
    job = parser.parse_job_listing(sample_occ_style_html, external_job_id="job_test")
    
    # Validar
    is_valid = parser.validate_job_item(job)
    
    assert is_valid is True


def test_parse_multiple_jobs_sequentially(parser, sample_occ_style_html):
    """Test parsear múltiples jobs secuencialmente"""
    jobs = []
    
    for i in range(5):
        job = parser.parse_job_listing(
            sample_occ_style_html,
            external_job_id=f"job_{i}",
        )
        jobs.append(job)
    
    # Verificar que se crearon 5 jobs
    assert len(jobs) == 5
    
    # Verificar que todos son válidos
    for job in jobs:
        assert parser.validate_job_item(job)
    
    # Verificar que los IDs son únicos
    ids = [job.external_job_id for job in jobs]
    assert len(ids) == len(set(ids))


def test_job_item_can_be_serialized(parser, sample_occ_style_html):
    """Test que JobItem se puede serializar a JSON para almacenamiento"""
    job = parser.parse_job_listing(sample_occ_style_html, external_job_id="serial_test")
    
    # Serializar a dict
    job_dict = job.model_dump(by_alias=True)
    
    # Verificar que se puede acceder a todos los campos
    assert job_dict["external_job_id"]
    assert job_dict["title"]
    assert job_dict["company"]
    assert job_dict["skills"]
    assert isinstance(job_dict["skills"], list)
    
    # Verificar que no hay valores None críticos
    assert job_dict["description"] is not None


def test_error_handling_malformed_html(parser):
    """Test manejo de errores con HTML malformado"""
    malformed_html = "<html><head><title>Bad HTML</title>"
    
    with pytest.raises(ValueError) as exc_info:
        parser.parse_job_listing(malformed_html)
    
    assert "Campos requeridos faltantes" in str(exc_info.value)


def test_job_item_pydantic_validation():
    """Test que Pydantic valida correctamente el modelo"""
    # Crear job válido
    valid_job = JobItem(
        external_job_id="valid_123",
        title="Software Engineer",
        company="Tech Corp",
        location="Remote",
        description="Join our engineering team and build amazing products"
    )
    
    assert valid_job is not None
    assert valid_job.source == "occ.com.mx"  # Default
    assert isinstance(valid_job.published_at, datetime)
    assert isinstance(valid_job.skills, list)


def test_skills_deduplication(parser):
    """Test que skills duplicadas se deduplican"""
    description = """
    We need Python developers. 
    Python is essential. 
    Experience with Python required. 
    Must know Docker and Python testing.
    """
    
    skills = parser.extract_skills_from_description(description)
    
    # Python debe aparecer una sola vez
    python_count = sum(1 for s in skills if "python" in s.lower())
    assert python_count == 1


def test_salary_extraction_edge_cases(parser):
    """Test extracción de salarios con casos extremos"""
    test_cases = [
        ("$100 a $200", 100, 200),
        ("$5,000 – $10,000", 5000, 10000),
        ("Rango: $50,000 a $100,000 MXN", 50000, 100000),
        ("No salary info", None, None),
    ]
    
    for text, expected_min, expected_max in test_cases:
        min_sal, max_sal = parser.extract_salary_range(text)
        assert min_sal == expected_min, f"Min mismatch for: {text}"
        assert max_sal == expected_max, f"Max mismatch for: {text}"


def test_work_mode_priority_hybrid_over_remote(parser):
    """Test que 'híbrido' tiene prioridad sobre 'remoto' en detección"""
    text = "Este es un trabajo remoto pero también presencial. Trabajo híbrido."
    
    mode = parser._detect_work_mode(text)
    
    # Debe detectar híbrido (que aparece explícitamente) en lugar de solo remoto
    assert mode == "híbrido"
