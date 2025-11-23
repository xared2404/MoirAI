"""
Unit tests for the Suggestions API endpoint.

Tests verify:
- Skill autocomplete functionality
- Location autocomplete functionality
- Combined suggestions
- Search recommendations
- Response schemas
- Latency requirements (< 50ms)
"""

import pytest
import time
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestSkillSuggestions:
    """Tests for /skills endpoint"""
    
    def test_skill_suggestions_empty_query(self):
        """Test getting top skills with empty query"""
        response = client.get("/api/v1/suggestions/skills?q=&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "suggestions" in data
        assert "query" in data
        assert "count" in data
        assert data["query"] == ""
        assert len(data["suggestions"]) <= 5
        
        print(f"✓ Empty query returned {len(data['suggestions'])} top skills")
    
    def test_skill_suggestions_prefix_python(self):
        """Test skill prefix matching for 'Py'"""
        response = client.get("/api/v1/suggestions/skills?q=Py&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["query"] == "Py"
        assert len(data["suggestions"]) > 0
        
        # Should contain Python
        skill_texts = [s["text"] for s in data["suggestions"]]
        assert "Python" in skill_texts
        
        print(f"✓ 'Py' prefix matched: {skill_texts}")
    
    def test_skill_suggestions_prefix_java(self):
        """Test skill prefix matching for 'Ja'"""
        response = client.get("/api/v1/suggestions/skills?q=Ja&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["suggestions"]) > 0
        skill_texts = [s["text"] for s in data["suggestions"]]
        
        # Should contain Java or JavaScript
        assert any("Java" in text for text in skill_texts)
        
        print(f"✓ 'Ja' prefix matched: {skill_texts}")
    
    def test_skill_suggestions_case_insensitive(self):
        """Test that prefix matching is case-insensitive"""
        response_lower = client.get("/api/v1/suggestions/skills?q=py&limit=5")
        response_upper = client.get("/api/v1/suggestions/skills?q=PY&limit=5")
        
        lower_skills = {s["text"] for s in response_lower.json()["suggestions"]}
        upper_skills = {s["text"] for s in response_upper.json()["suggestions"]}
        
        assert lower_skills == upper_skills
        print(f"✓ Case-insensitive matching working: {lower_skills}")
    
    def test_skill_suggestions_limit_parameter(self):
        """Test limit parameter respected"""
        for limit in [1, 5, 10, 20]:
            response = client.get(f"/api/v1/suggestions/skills?q=&limit={limit}")
            data = response.json()
            assert len(data["suggestions"]) <= limit
        
        print("✓ Limit parameter respected for all values")
    
    def test_skill_suggestions_response_structure(self):
        """Test response structure matches schema"""
        response = client.get("/api/v1/suggestions/skills?q=Py&limit=5")
        data = response.json()
        
        # Check structure
        assert "query" in data
        assert "suggestions" in data
        assert "count" in data
        
        # Check suggestions have required fields
        for suggestion in data["suggestions"]:
            assert "text" in suggestion
            assert "category" in suggestion
            assert "frequency" in suggestion
            assert isinstance(suggestion["frequency"], int)
            assert suggestion["frequency"] > 0
        
        print("✓ Response structure valid")
    
    def test_skill_suggestions_sorting(self):
        """Test suggestions sorted by frequency"""
        response = client.get("/api/v1/suggestions/skills?q=&limit=10")
        data = response.json()
        
        frequencies = [s["frequency"] for s in data["suggestions"]]
        
        # Should be sorted descending
        assert frequencies == sorted(frequencies, reverse=True)
        print(f"✓ Results sorted by frequency: {frequencies}")
    
    def test_skill_suggestions_latency(self):
        """Test endpoint response time < 50ms"""
        start = time.time()
        response = client.get("/api/v1/suggestions/skills?q=Py&limit=10")
        elapsed = (time.time() - start) * 1000
        
        assert response.status_code == 200
        assert elapsed < 50  # Must be < 50ms
        
        print(f"✓ Latency: {elapsed:.2f}ms (SLA: < 50ms)")


class TestLocationSuggestions:
    """Tests for /locations endpoint"""
    
    def test_location_suggestions_empty_query(self):
        """Test getting popular locations with empty query"""
        response = client.get("/api/v1/suggestions/locations?q=&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["suggestions"]) <= 5
        assert all("text" in loc for loc in data["suggestions"])
        assert all("normalized" in loc for loc in data["suggestions"])
        assert all("jobs" in loc for loc in data["suggestions"])
        
        print(f"✓ Popular locations: {[loc['text'] for loc in data['suggestions']]}")
    
    def test_location_suggestions_prefix_ciudad(self):
        """Test location prefix matching for 'Ciu'"""
        response = client.get("/api/v1/suggestions/locations?q=Ciu&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["suggestions"]) > 0
        assert any("Ciudad" in loc["text"] for loc in data["suggestions"])
        
        print(f"✓ 'Ciu' prefix matched: {[loc['text'] for loc in data['suggestions']]}")
    
    def test_location_suggestions_prefix_remote(self):
        """Test location prefix matching for 'Rem'"""
        response = client.get("/api/v1/suggestions/locations?q=Rem&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["suggestions"]) > 0
        location_texts = [loc["text"] for loc in data["suggestions"]]
        assert "Remoto" in location_texts
        
        print(f"✓ 'Rem' prefix matched: {location_texts}")
    
    def test_location_suggestions_english_names(self):
        """Test that normalized English names are searchable"""
        # Search by normalized English name
        response = client.get("/api/v1/suggestions/locations?q=Remote&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["suggestions"]) > 0
        assert any("Remoto" in loc["text"] for loc in data["suggestions"])
        
        print(f"✓ English names searchable: {[loc['normalized'] for loc in data['suggestions']]}")
    
    def test_location_suggestions_sorting_by_jobs(self):
        """Test locations sorted by job count"""
        response = client.get("/api/v1/suggestions/locations?q=&limit=10")
        data = response.json()
        
        job_counts = [loc["jobs"] for loc in data["suggestions"]]
        
        # Should be sorted descending by job count
        assert job_counts == sorted(job_counts, reverse=True)
        print(f"✓ Sorted by job count: {job_counts}")
    
    def test_location_suggestions_latency(self):
        """Test endpoint response time < 50ms"""
        start = time.time()
        response = client.get("/api/v1/suggestions/locations?q=Rem&limit=10")
        elapsed = (time.time() - start) * 1000
        
        assert response.status_code == 200
        assert elapsed < 50
        
        print(f"✓ Latency: {elapsed:.2f}ms (SLA: < 50ms)")


class TestCombinedSuggestions:
    """Tests for /combined endpoint"""
    
    def test_combined_suggestions(self):
        """Test combined endpoint returns both skills and locations"""
        response = client.get(
            "/api/v1/suggestions/combined?skill_q=Py&location_q=Rem&limit=5"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "skills" in data
        assert "locations" in data
        assert "timestamp" in data
        
        assert len(data["skills"]) > 0
        assert len(data["locations"]) > 0
        
        print(f"✓ Combined suggestions: {len(data['skills'])} skills + {len(data['locations'])} locations")
    
    def test_combined_suggestions_empty_queries(self):
        """Test combined endpoint with empty queries returns top results"""
        response = client.get("/api/v1/suggestions/combined?skill_q=&location_q=&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["skills"]) <= 5
        assert len(data["locations"]) <= 5
        
        print("✓ Combined with empty queries working")
    
    def test_combined_suggestions_latency(self):
        """Test combined endpoint response time < 50ms"""
        start = time.time()
        response = client.get("/api/v1/suggestions/combined?skill_q=Py&location_q=Rem")
        elapsed = (time.time() - start) * 1000
        
        assert response.status_code == 200
        assert elapsed < 50
        
        print(f"✓ Combined latency: {elapsed:.2f}ms (SLA: < 50ms)")


class TestSearchRecommendations:
    """Tests for /search-recommendations endpoint"""
    
    def test_search_recommendations_basic(self):
        """Test basic search recommendations"""
        response = client.post(
            "/api/v1/suggestions/search-recommendations",
            params={
                "skills": ["Python", "JavaScript"],
                "locations": ["Remote", "CDMX"],
                "limit": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "recommendations" in data
        assert len(data["recommendations"]) > 0
        
        # Check structure
        for rec in data["recommendations"]:
            assert "query" in rec
            assert "skill" in rec
            assert "location" in rec
            assert "score" in rec
            assert isinstance(rec["score"], float)
            assert 0 <= rec["score"] <= 1
        
        print(f"✓ {len(data['recommendations'])} recommendations generated")
    
    def test_search_recommendations_defaults(self):
        """Test that recommendations work with default parameters"""
        response = client.post(
            "/api/v1/suggestions/search-recommendations",
            params={"limit": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["recommendations"]) > 0
        print(f"✓ Default recommendations: {[r['query'] for r in data['recommendations'][:3]]}")
    
    def test_search_recommendations_limit(self):
        """Test limit parameter for recommendations"""
        for limit in [1, 3, 5, 10]:
            response = client.post(
                "/api/v1/suggestions/search-recommendations",
                params={
                    "skills": ["Python", "JavaScript"],
                    "locations": ["Remote", "CDMX"],
                    "limit": limit
                }
            )
            
            data = response.json()
            assert len(data["recommendations"]) <= limit
        
        print("✓ Limit parameter working correctly")
    
    def test_search_recommendations_latency(self):
        """Test latency < 40ms"""
        start = time.time()
        response = client.post(
            "/api/v1/suggestions/search-recommendations",
            params={
                "skills": ["Python"],
                "locations": ["Remote"],
                "limit": 5
            }
        )
        elapsed = (time.time() - start) * 1000
        
        assert response.status_code == 200
        assert elapsed < 40
        
        print(f"✓ Latency: {elapsed:.2f}ms (SLA: < 40ms)")


class TestHealthCheck:
    """Tests for /health endpoint"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/api/v1/suggestions/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == "ok"
        
        print("✓ Health check passing")


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_invalid_limit_too_high(self):
        """Test limit parameter validation (max 50)"""
        response = client.get("/api/v1/suggestions/skills?q=Py&limit=100")
        
        assert response.status_code == 422  # Validation error
        print("✓ Validation: limit > 50 rejected")
    
    def test_invalid_limit_zero(self):
        """Test limit parameter validation (min 1)"""
        response = client.get("/api/v1/suggestions/skills?q=Py&limit=0")
        
        assert response.status_code == 422  # Validation error
        print("✓ Validation: limit < 1 rejected")
    
    def test_query_too_long(self):
        """Test query parameter validation (max 50 chars)"""
        long_query = "a" * 100
        response = client.get(f"/api/v1/suggestions/skills?q={long_query}")
        
        assert response.status_code == 422
        print("✓ Validation: query > 50 chars rejected")


class TestIntegration:
    """Integration tests combining multiple features"""
    
    def test_full_search_flow(self):
        """Test realistic user search flow"""
        # 1. User types skill
        skills_response = client.get("/api/v1/suggestions/skills?q=Py&limit=5")
        assert skills_response.status_code == 200
        skills = skills_response.json()["suggestions"]
        
        # 2. User types location
        locations_response = client.get("/api/v1/suggestions/locations?q=Rem&limit=5")
        assert locations_response.status_code == 200
        locations = locations_response.json()["suggestions"]
        
        # 3. Get recommendations
        skill_list = [s["text"] for s in skills]
        location_list = [l["text"] for l in locations]
        
        recs_response = client.post(
            "/api/v1/suggestions/search-recommendations",
            params={
                "skills": skill_list[:2],
                "locations": location_list[:2],
                "limit": 5
            }
        )
        
        assert recs_response.status_code == 200
        recs = recs_response.json()["recommendations"]
        
        print(f"✓ Full flow: {len(skills)} skills + {len(locations)} locations → {len(recs)} recommendations")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
