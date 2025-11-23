#!/usr/bin/env python3
"""
Test para verificar que el endpoint de recomendaciones funciona correctamente
después de las fixes implementadas
"""

import asyncio
import json
from app.services.matching_service import matching_service
from app.schemas import JobItem
from app.models import Student
from app.core.database import engine
from sqlmodel import Session, select
from datetime import datetime

# ============================================================================
# TEST 1: Verificar que MockProvider retorna empleos
# ============================================================================
async def test_mock_provider_enriched():
    """Test que MockProvider está enriquecido y retorna resultados"""
    print("\n" + "="*80)
    print("TEST 1: MockProvider Enriquecido")
    print("="*80)
    
    from app.providers import job_provider_manager
    
    # Verificar proveedores disponibles
    available = await job_provider_manager.get_available_providers()
    print(f"✓ Proveedores disponibles: {[p.name for p in available]}")
    
    # Test 1a: Búsqueda con "Python"
    print("\n1a) Búsqueda con query 'Python':")
    jobs = await job_provider_manager.search_all_providers("Python", limit_per_provider=5)
    print(f"   Encontrados: {len(jobs)} empleos")
    for job in jobs[:3]:
        print(f"   - {job.title} @ {job.company} ({job.location})")
    assert len(jobs) > 0, "❌ No se encontraron empleos con 'Python'"
    print("   ✓ PASS")
    
    # Test 1b: Búsqueda con "Data Science"
    print("\n1b) Búsqueda con query 'Data Science':")
    jobs = await job_provider_manager.search_all_providers("Data Science", limit_per_provider=5)
    print(f"   Encontrados: {len(jobs)} empleos")
    for job in jobs[:2]:
        print(f"   - {job.title} @ {job.company}")
    assert len(jobs) > 0, "❌ No se encontraron empleos con 'Data Science'"
    print("   ✓ PASS")
    
    # Test 1c: Búsqueda con ubicación
    print("\n1c) Búsqueda con query 'React' y location='Córdoba':")
    jobs = await job_provider_manager.search_all_providers("React", location="Córdoba", limit_per_provider=5)
    print(f"   Encontrados: {len(jobs)} empleos en Córdoba")
    for job in jobs[:2]:
        print(f"   - {job.title} @ {job.location}")
    assert len(jobs) > 0, "❌ No se encontraron empleos en Córdoba"
    print("   ✓ PASS")
    
    # Test 1d: Búsqueda vacía debe retornar variedad
    print("\n1d) Búsqueda vacía (sin query específica):")
    jobs = await job_provider_manager.search_all_providers("", limit_per_provider=5)
    print(f"   Encontrados: {len(jobs)} empleos")
    for job in jobs[:3]:
        print(f"   - {job.title}")
    assert len(jobs) > 0, "❌ No se retornó variedad de empleos con query vacía"
    print("   ✓ PASS")


# ============================================================================
# TEST 2: Verificar generación de recomendaciones por defecto
# ============================================================================
async def test_default_recommendations_generation():
    """Test que se generan recomendaciones por defecto cuando no hay proveedores"""
    print("\n" + "="*80)
    print("TEST 2: Generación de Recomendaciones Por Defecto")
    print("="*80)
    
    # Crear un estudiante de prueba
    with Session(engine) as session:
        test_student = Student(
            name="Test Student",
            email="test@example.com",
            program="Ingeniería en Sistemas",
            skills=json.dumps(["Python", "FastAPI", "PostgreSQL"]),
            projects=json.dumps(["API REST", "Dashboard Web"]),
            soft_skills=json.dumps(["Communication", "Teamwork"]),
            is_active=True
        )
        session.add(test_student)
        session.commit()
        session.refresh(test_student)
        student_id = test_student.id
        print(f"✓ Estudiante de prueba creado: ID={student_id}")
        print(f"  Skills: {test_student.skills}")
        print(f"  Projects: {test_student.projects}")
        
        # Test generación de recomendaciones
        print("\n2a) Generando recomendaciones por defecto:")
        recommendations = await matching_service.find_job_recommendations(
            student_id=student_id,
            location=None,
            limit=5
        )
        
        print(f"   Total encontrado: {recommendations['total_found']}")
        print(f"   Matches encontrados: {recommendations['matches_found']}")
        print(f"   Query usado: {recommendations['query_used']}")
        print(f"   Origen: {recommendations.get('source_breakdown', {})}")
        print(f"\n   Recomendaciones:")
        for i, job in enumerate(recommendations['jobs'][:3], 1):
            print(f"   {i}. {job.title}")
            print(f"      Empresa: {job.company}")
            print(f"      Location: {job.location}")
            if hasattr(job, 'match_score'):
                print(f"      Score: {job.match_score}")
        
        assert len(recommendations['jobs']) > 0, "❌ No se generaron recomendaciones"
        assert recommendations['matches_found'] > 0, "❌ No hay matches"
        print("\n   ✓ PASS - Recomendaciones generadas exitosamente")
        
        # Limpiar
        session.delete(test_student)
        session.commit()


# ============================================================================
# TEST 3: Verificar método de construcción de queries
# ============================================================================
def test_query_building():
    """Test que build_student_query genera queries significativas"""
    print("\n" + "="*80)
    print("TEST 3: Construcción de Queries")
    print("="*80)
    
    with Session(engine) as session:
        # Test 3a: Estudiante con skills y proyectos
        print("\n3a) Estudiante con skills y proyectos:")
        student1 = Student(
            name="Test1",
            email="test1@example.com",
            program="Ingeniería en Sistemas",
            skills=json.dumps(["Python", "FastAPI", "PostgreSQL", "Docker"]),
            projects=json.dumps(["API REST", "Dashboard Web"]),
            soft_skills=json.dumps([]),
            is_active=True
        )
        query1 = matching_service.build_student_query(student1)
        print(f"   Query generada: '{query1}'")
        assert "Python" in query1, "❌ Query no contiene Python"
        assert "FastAPI" in query1, "❌ Query no contiene FastAPI"
        print("   ✓ PASS")
        
        # Test 3b: Estudiante sin skills ni proyectos
        print("\n3b) Estudiante sin skills ni proyectos:")
        student2 = Student(
            name="Test2",
            email="test2@example.com",
            program="Ingeniería en Computación",
            skills=json.dumps([]),
            projects=json.dumps([]),
            soft_skills=json.dumps([]),
            is_active=True
        )
        query2 = matching_service.build_student_query(student2)
        print(f"   Query generada: '{query2}'")
        assert len(query2) > 0, "❌ Query está vacía"
        assert any(term in query2 for term in ["intern", "junior", "trainee", "computación"]), \
               "❌ Query no contiene términos por defecto"
        print("   ✓ PASS")


# ============================================================================
# TEST 4: Verificar métodos auxiliares
# ============================================================================
def test_helper_methods():
    """Test métodos auxiliares de generación de recomendaciones"""
    print("\n" + "="*80)
    print("TEST 4: Métodos Auxiliares")
    print("="*80)
    
    # Test 4a: _get_seniority_level
    print("\n4a) Test _get_seniority_level:")
    levels = [
        matching_service._get_seniority_level(0),
        matching_service._get_seniority_level(1),
        matching_service._get_seniority_level(2),
        matching_service._get_seniority_level(5),
    ]
    print(f"   Levels: {levels}")
    assert levels[0] == "Junior", "❌ Índice 0 debe ser Junior"
    assert levels[1] == "Mid-Level", "❌ Índice 1 debe ser Mid-Level"
    assert levels[2] == "Senior", "❌ Índice 2 debe ser Senior"
    assert levels[3] == "Senior", "❌ Índice 5 debe ser Senior (max)"
    print("   ✓ PASS")
    
    # Test 4b: _generate_company_name
    print("\n4b) Test _generate_company_name:")
    companies = [
        matching_service._generate_company_name("Python backend"),
        matching_service._generate_company_name("React frontend"),
        matching_service._generate_company_name("Data analysis machine learning"),
        matching_service._generate_company_name("Unknown technology"),
    ]
    print(f"   Companies: {companies}")
    assert "TechCorp" in companies[0], "❌ Python debe mapear a TechCorp"
    assert "Frontend" in companies[1], "❌ React debe mapear a Frontend"
    assert "AI" in companies[2], "❌ Machine learning debe mapear a AI"
    assert companies[3] == "TechCorp Global", "❌ Desconocido debe ser default"
    print("   ✓ PASS")


# ============================================================================
# MAIN
# ============================================================================
async def main():
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*20 + "TESTS - ENDPOINT RECOMMENDATIONS FIX" + " "*23 + "║")
    print("╚" + "═"*78 + "╝")
    
    try:
        # Tests síncronos
        test_query_building()
        test_helper_methods()
        
        # Tests asíncronos
        await test_mock_provider_enriched()
        await test_default_recommendations_generation()
        
        print("\n" + "="*80)
        print("✓ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("="*80 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLIDO: {e}\n")
        return False
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
