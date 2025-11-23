"""
🧪 TESTING DE ENDPOINTS CONSOLIDADOS

Tests para verificar que los endpoints consolidados funcionan correctamente:
- Jobs: autocomplete/skills y autocomplete/locations
- Students: search/skills

Ejecución:
  pytest test_consolidated_endpoints.py -v
  pytest test_consolidated_endpoints.py::test_autocomplete_skills -v
"""

import pytest
import json
from httpx import AsyncClient
from fastapi.testclient import TestClient
from datetime import datetime

# Asumiendo que la app está en app.main:app
from app.main import app


class TestAutocompleteSkills:
    """
    Tests para GET /jobs/autocomplete/skills
    """
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_autocomplete_skills_empty_query(self, client):
        """
        Prueba: Autocomplete sin query devuelve todas las habilidades ordenadas por frecuencia
        """
        response = client.get("/api/v1/jobs/autocomplete/skills")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificaciones
        assert "query" in data
        assert "suggestions" in data
        assert "count" in data
        assert data["query"] == ""
        assert len(data["suggestions"]) > 0
        print(f"✅ Autocomplete skills empty query: {len(data['suggestions'])} sugerencias")
    
    def test_autocomplete_skills_with_prefix(self, client):
        """
        Prueba: Autocomplete con prefijo filtra correctamente
        """
        response = client.get("/api/v1/jobs/autocomplete/skills?q=pyt")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["query"] == "pyt"
        assert len(data["suggestions"]) > 0
        
        # Verificar que todas las sugerencias comienzan con "pyt"
        for skill in data["suggestions"]:
            assert "text" in skill
            assert skill["text"].lower().startswith("pyt")
            assert "category" in skill
            assert "frequency" in skill
        
        print(f"✅ Autocomplete skills 'pyt': {len(data['suggestions'])} matches")
        print(f"   Resultados: {[s['text'] for s in data['suggestions']]}")
    
    def test_autocomplete_skills_limit(self, client):
        """
        Prueba: Límite de resultados funciona correctamente
        """
        response = client.get("/api/v1/jobs/autocomplete/skills?q=&limit=3")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["suggestions"]) <= 3
        print(f"✅ Autocomplete skills limit=3: {len(data['suggestions'])} resultados")
    
    def test_autocomplete_skills_case_insensitive(self, client):
        """
        Prueba: Búsqueda es case-insensitive
        """
        response_lower = client.get("/api/v1/jobs/autocomplete/skills?q=java")
        response_upper = client.get("/api/v1/jobs/autocomplete/skills?q=JAVA")
        response_mixed = client.get("/api/v1/jobs/autocomplete/skills?q=JaVa")
        
        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        assert response_mixed.status_code == 200
        
        # Todos deberían retornar el mismo número de resultados
        data_lower = response_lower.json()
        data_upper = response_upper.json()
        data_mixed = response_mixed.json()
        
        assert len(data_lower["suggestions"]) == len(data_upper["suggestions"])
        assert len(data_lower["suggestions"]) == len(data_mixed["suggestions"])
        
        print(f"✅ Autocomplete skills case-insensitive: Todos retornan {len(data_lower['suggestions'])} resultados")
    
    def test_autocomplete_skills_frequency_sorting(self, client):
        """
        Prueba: Los resultados están ordenados por frecuencia (desc)
        """
        response = client.get("/api/v1/jobs/autocomplete/skills")
        
        assert response.status_code == 200
        data = response.json()
        suggestions = data["suggestions"]
        
        # Verificar que están ordenados por frecuencia descendente
        for i in range(len(suggestions) - 1):
            assert suggestions[i]["frequency"] >= suggestions[i+1]["frequency"]
        
        print(f"✅ Autocomplete skills sorting: Ordenadas por frecuencia (desc)")
        for skill in suggestions[:5]:
            print(f"   • {skill['text']}: {skill['frequency']} jobs")


class TestAutocompleteLocations:
    """
    Tests para GET /jobs/autocomplete/locations
    """
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_autocomplete_locations_empty_query(self, client):
        """
        Prueba: Autocomplete sin query devuelve todas las ubicaciones
        """
        response = client.get("/api/v1/jobs/autocomplete/locations")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "query" in data
        assert "suggestions" in data
        assert "count" in data
        assert data["query"] == ""
        assert len(data["suggestions"]) > 0
        print(f"✅ Autocomplete locations empty query: {len(data['suggestions'])} sugerencias")
    
    def test_autocomplete_locations_with_prefix(self, client):
        """
        Prueba: Autocomplete con prefijo filtra ubicaciones correctamente
        """
        response = client.get("/api/v1/jobs/autocomplete/locations?q=mex")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["query"] == "mex"
        assert len(data["suggestions"]) > 0
        
        # Verificar que todas comienzan con "mex"
        for location in data["suggestions"]:
            assert "text" in location
            assert "normalized" in location
            assert "jobs" in location
            # El prefijo puede estar en text o normalized
            assert (location["text"].lower().startswith("mex") or 
                   location["normalized"].lower().startswith("mex"))
        
        print(f"✅ Autocomplete locations 'mex': {len(data['suggestions'])} matches")
        print(f"   Resultados: {[s['text'] for s in data['suggestions']]}")
    
    def test_autocomplete_locations_limit(self, client):
        """
        Prueba: Límite de resultados funciona correctamente
        """
        response = client.get("/api/v1/jobs/autocomplete/locations?q=&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["suggestions"]) <= 2
        print(f"✅ Autocomplete locations limit=2: {len(data['suggestions'])} resultados")
    
    def test_autocomplete_locations_jobs_sorting(self, client):
        """
        Prueba: Las ubicaciones están ordenadas por cantidad de jobs (desc)
        """
        response = client.get("/api/v1/jobs/autocomplete/locations")
        
        assert response.status_code == 200
        data = response.json()
        suggestions = data["suggestions"]
        
        # Verificar que están ordenados por jobs descendente
        for i in range(len(suggestions) - 1):
            assert suggestions[i]["jobs"] >= suggestions[i+1]["jobs"]
        
        print(f"✅ Autocomplete locations sorting: Ordenadas por jobs (desc)")
        for location in suggestions:
            print(f"   • {location['text']}: {location['jobs']} jobs")


class TestStudentsSearchSkills:
    """
    Tests para GET /students/search/skills
    
    ⚠️ Nota: Este endpoint requiere autenticación y permisos especiales
    Solo empresas verificadas pueden acceder
    """
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_search_skills_without_auth_denied(self, client):
        """
        Prueba: Acceso sin autenticación es rechazado
        """
        response = client.get("/api/v1/students/search/skills?skills=Python")
        
        # Debería retornar 401 Unauthorized o 403 Forbidden
        assert response.status_code in [401, 403]
        print(f"✅ Search skills sin autenticación: Rechazado ({response.status_code})")
    
    def test_search_skills_invalid_params(self, client):
        """
        Prueba: Parámetros inválidos retornan error
        """
        # Sin parámetros requeridos
        response = client.get("/api/v1/students/search/skills")
        
        # Debería retornar 400 Bad Request o 422 Unprocessable Entity
        assert response.status_code in [400, 401, 403, 422]
        print(f"✅ Search skills sin parámetros: Error validación ({response.status_code})")


class TestHealthCheck:
    """
    Tests para verificar que los endpoints de health funcionan
    """
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_jobs_health(self, client):
        """
        Prueba: Health check del servicio de jobs
        """
        response = client.get("/api/v1/jobs/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data
        assert data["service"] == "jobs"
        
        print(f"✅ Jobs health check: {data['status']}")
    
    def test_main_health(self, client):
        """
        Prueba: Health check general de la aplicación
        """
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"
        
        print(f"✅ App health check: {data['status']}")


if __name__ == "__main__":
    """
    Ejecutar tests manualmente si no está instalado pytest
    """
    print("🧪 Testing Endpoints Consolidados")
    print("=" * 60)
    
    client = TestClient(app)
    
    # Test 1: Autocomplete Skills
    print("\n📝 Test 1: Autocomplete Skills")
    response = client.get("/api/v1/jobs/autocomplete/skills?q=pyt&limit=5")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 2: Autocomplete Locations  
    print("\n📝 Test 2: Autocomplete Locations")
    response = client.get("/api/v1/jobs/autocomplete/locations?q=mex&limit=5")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 3: Health Check
    print("\n📝 Test 3: Health Check")
    response = client.get("/jobs/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
