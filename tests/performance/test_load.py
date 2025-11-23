"""
Fase 3.1: Load/Performance Tests
Tests para validar rendimiento con múltiples requests y medir métricas
"""
import time
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from app.models import Company


class TestLoadPerformance:
    """Test API performance under load"""

    def test_bulk_company_creation_performance(self, client_with_admin: TestClient, session: Session):
        """Create 100 companies sequentially - measure total time"""
        start_time = time.time()
        created_ids = []

        for i in range(100):
            payload = {
                "email": f"load-create-{i}@test.com",
                "name": f"Load Test Company {i}",
                "description": f"Load test company {i}",
                "industry": "technology",
                "size": "pequena",
                "website": f"https://loadtest{i}.com"
            }
            response = client_with_admin.post("/api/v1/companies/", json=payload)
            assert response.status_code == 201
            created_ids.append(response.json()["id"])

        elapsed = time.time() - start_time

        # Performance: 100 creates should take < 5 seconds
        assert elapsed < 5.0, f"100 company creations took {elapsed:.2f}s, expected < 5s"

        # Verify all created
        assert len(created_ids) == 100
        assert len(set(created_ids)) == 100  # All unique

    def test_bulk_list_with_pagination_performance(self, client_with_admin: TestClient, session: Session):
        """List with pagination - 1000 items should be retrieved in chunks efficiently"""
        # Create 1000 companies in DB (directly for speed)
        companies = [
            Company(
                email=f"pagination-{i}@test.com",
                name=f"Pagination Test {i}",
                description="Test",
                industry="technology",
                size="pequena",
                website=f"https://pag{i}.com",
                user_id=1,
                is_verified=True
            )
            for i in range(1000)
        ]
        session.add_all(companies)
        session.commit()

        # Fetch in pages of 100
        start_time = time.time()
        total_retrieved = 0

        for page in range(10):
            skip = page * 100
            response = client_with_admin.get(f"/api/v1/companies/?skip={skip}&limit=100")
            assert response.status_code == 200
            data = response.json()
            total_retrieved += len(data.get("items", []))

        elapsed = time.time() - start_time

        # Performance: 10 paginated requests should be fast (< 2 seconds)
        assert elapsed < 2.0, f"Pagination of 1000 items took {elapsed:.2f}s, expected < 2s"
        assert total_retrieved >= 100, f"Retrieved {total_retrieved} items, expected >= 100"

    def test_get_nonexistent_company_performance(self, client_with_admin: TestClient):
        """Repeated 404 responses should be fast"""
        start_time = time.time()

        for i in range(100):
            response = client_with_admin.get(f"/api/v1/companies/{99999 + i}")
            assert response.status_code == 404

        elapsed = time.time() - start_time

        # Performance: 100 404s should be fast (< 1 second)
        assert elapsed < 1.0, f"100 404 responses took {elapsed:.2f}s, expected < 1s"

    def test_filter_performance_large_dataset(self, client_with_admin: TestClient, session: Session):
        """Filtering on 500 companies should be fast"""
        # Create mixed companies
        industries = ["technology", "finance", "healthcare", "retail", "manufacturing"]
        for i in range(500):
            company = Company(
                email=f"filter-perf-{i}@test.com",
                name=f"Filter Test {i}",
                description=f"Company in {industries[i % 5]}",
                industry=industries[i % 5],
                size="mediana",
                website=f"https://filtperf{i}.com",
                user_id=1,
                is_verified=True
            )
            session.add(company)
        session.commit()

        # Query by specific industry
        start_time = time.time()
        response = client_with_admin.get("/api/v1/companies/?industry=technology")
        elapsed = time.time() - start_time

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 100, f"Expected 100+ tech companies, got {data['total']}"

        # Performance: filtering should be fast (< 0.5 seconds)
        assert elapsed < 0.5, f"Filtering 500 companies took {elapsed:.2f}s, expected < 0.5s"

    def test_update_performance_batch(self, client_with_admin: TestClient, session: Session):
        """Update 50 different companies - measure time"""
        # Create 50 companies
        company_ids = []
        for i in range(50):
            company = Company(
                email=f"update-perf-{i}@test.com",
                name=f"Update Test {i}",
                description="Test",
                industry="technology",
                size="pequena",
                website=f"https://upd{i}.com",
                user_id=1
            )
            session.add(company)
        session.commit()
        for company in session.query(Company).filter(
            Company.email.like("update-perf-%")
        ).all():
            company_ids.append(company.id)

        # Update all 50
        start_time = time.time()
        for i, company_id in enumerate(company_ids):
            payload = {
                "name": f"Updated {i}",
                "description": f"Updated at {time.time()}",
                "website": f"https://updated{i}.com"
            }
            response = client_with_admin.put(f"/api/v1/companies/{company_id}", json=payload)
            assert response.status_code == 200

        elapsed = time.time() - start_time

        # Performance: 50 updates should be fast (< 2 seconds)
        assert elapsed < 2.0, f"50 updates took {elapsed:.2f}s, expected < 2s"

    def test_soft_delete_performance_batch(self, client_with_admin: TestClient, session: Session):
        """Soft delete 100 companies - should be very fast (just flag updates)"""
        # Create 100 companies
        companies = [
            Company(
                email=f"softdel-perf-{i}@test.com",
                name=f"Soft Delete Test {i}",
                description="Test",
                industry="technology",
                size="pequena",
                website=f"https://sdel{i}.com",
                user_id=1,
                is_active=True
            )
            for i in range(100)
        ]
        session.add_all(companies)
        session.commit()

        # Get IDs
        company_ids = [c.id for c in session.query(Company).filter(
            Company.email.like("softdel-perf-%")
        ).all()]

        # Soft delete all 100
        start_time = time.time()
        for company_id in company_ids:
            response = client_with_admin.delete(f"/api/v1/companies/{company_id}")
            assert response.status_code == 200

        elapsed = time.time() - start_time

        # Performance: 100 soft deletes should be very fast (< 1 second, just updates)
        assert elapsed < 1.0, f"100 soft deletes took {elapsed:.2f}s, expected < 1s"


class TestMemoryUsage:
    """Test memory efficiency"""

    def test_large_response_handling(self, client_with_admin: TestClient, session: Session):
        """Large response (many items) should be handled efficiently"""
        # Create companies with large descriptions
        for i in range(200):
            company = Company(
                email=f"memory-test-{i}@test.com",
                name=f"Memory Test {i}",
                description="X" * 1000,  # 1KB description
                industry="technology",
                size="pequena",
                website=f"https://mem{i}.com",
                user_id=1,
                is_verified=True
            )
            session.add(company)
        session.commit()

        # Request all - should not crash
        response = client_with_admin.get("/api/v1/companies/?limit=1000")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 200

        # Response should be parseable
        items = data.get("items", [])
        assert len(items) > 0
        assert all("description" in item for item in items)
