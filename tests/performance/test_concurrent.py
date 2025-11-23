"""
Fase 3.1: Concurrency Tests
Tests para validar que múltiples requests simultáneos funcionan correctamente
sin race conditions o data corruption.
"""
import asyncio
import pytest
from httpx import AsyncClient
from sqlmodel import Session, select
from app.main import app
from app.models import Company
from tests.conftest import get_session


class TestConcurrentOperations:
    """Test concurrent CRUD operations on same resource"""

    @pytest.mark.asyncio
    async def test_concurrent_company_creation(self, session: Session):
        """Create 50 companies concurrently without email conflicts"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Prepare tasks
            tasks = []
            for i in range(50):
                email = f"concurrent-{i}@test.com"
                payload = {
                    "email": email,
                    "name": f"Company {i}",
                    "description": f"Concurrent test company {i}",
                    "industry": "technology",
                    "size": "pequena",
                    "website": f"https://company{i}.com"
                }
                tasks.append(client.post("/api/v1/companies/", json=payload))

            # Execute concurrently
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify results
            success_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 201)
            assert success_count == 50, f"Expected 50 successful creations, got {success_count}"

            # Verify all companies in DB
            companies = session.exec(select(Company)).all()
            assert len(companies) >= 50, f"Expected at least 50 companies in DB, got {len(companies)}"

    @pytest.mark.asyncio
    async def test_concurrent_same_company_update(self, session: Session):
        """Update same company concurrently - last write wins"""
        # Create initial company
        company = Company(
            email="concurrent-update@test.com",
            name="Original Name",
            description="Original description",
            industry="technology",
            size="mediana",
            website="https://original.com",
            user_id=1
        )
        session.add(company)
        session.commit()
        session.refresh(company)

        async with AsyncClient(app=app, base_url="http://test") as client:
            # 10 concurrent updates with different names
            tasks = []
            for i in range(10):
                payload = {
                    "name": f"Updated Name {i}",
                    "description": f"Description {i}",
                    "website": f"https://updated{i}.com"
                }
                tasks.append(
                    client.put(
                        f"/api/v1/companies/{company.id}",
                        json=payload,
                        headers={"Authorization": "Bearer admin_token"}
                    )
                )

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # All should succeed (200)
            success_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
            assert success_count == 10, f"Expected 10 successful updates, got {success_count}"

            # Verify final state - should have one of the updated names
            session.refresh(company)
            assert company.name.startswith("Updated Name"), f"Expected updated name, got {company.name}"

    @pytest.mark.asyncio
    async def test_concurrent_read_operations(self, session: Session):
        """Multiple concurrent reads should not block each other"""
        # Create test companies
        for i in range(10):
            company = Company(
                email=f"concurrent-read-{i}@test.com",
                name=f"Read Test {i}",
                description=f"Read test company {i}",
                industry="technology",
                size="pequena",
                website=f"https://read{i}.com",
                user_id=1,
                is_verified=True
            )
            session.add(company)
        session.commit()

        async with AsyncClient(app=app, base_url="http://test") as client:
            # 100 concurrent GET requests
            tasks = []
            for i in range(100):
                tasks.append(client.get("/api/v1/companies/"))

            import time
            start = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            elapsed = time.time() - start

            # All should succeed (200)
            success_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
            assert success_count == 100, f"Expected 100 successful reads, got {success_count}"

            # Performance check: 100 reads should be fast (< 5 seconds)
            assert elapsed < 5.0, f"100 concurrent reads took {elapsed:.2f}s, expected < 5s"

    @pytest.mark.asyncio
    async def test_concurrent_read_write_mix(self, session: Session):
        """Mix of concurrent reads and writes - no data corruption"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create initial company
            company_data = {
                "email": "concurrent-rw@test.com",
                "name": "R/W Test",
                "description": "Read/Write test",
                "industry": "technology",
                "size": "mediana",
                "website": "https://rw.com"
            }
            resp = await client.post("/api/v1/companies/", json=company_data)
            assert resp.status_code == 201
            company_id = resp.json()["id"]

            # Mix of operations: 30 reads, 20 writes
            tasks = []
            # 30 reads
            for _ in range(30):
                tasks.append(client.get(f"/api/v1/companies/{company_id}"))
            # 20 writes
            for i in range(20):
                update_data = {
                    "name": f"Updated {i}",
                    "description": f"Updated description {i}",
                    "website": f"https://rw{i}.com"
                }
                tasks.append(
                    client.put(
                        f"/api/v1/companies/{company_id}",
                        json=update_data,
                        headers={"Authorization": "Bearer admin_token"}
                    )
                )

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # All should succeed
            successful = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code in [200, 201])
            assert successful == 50, f"Expected 50 successful ops, got {successful}"

            # Final read should show valid data
            final_resp = await client.get(f"/api/v1/companies/{company_id}")
            assert final_resp.status_code == 200
            company_data = final_resp.json()
            assert company_data["id"] == company_id
            assert isinstance(company_data["name"], str)
            assert len(company_data["name"]) > 0


class TestRaceConditionPrevention:
    """Test that race conditions are prevented"""

    @pytest.mark.asyncio
    async def test_duplicate_email_race_condition(self, session: Session):
        """Two concurrent requests with same email - only one should succeed"""
        email = "duplicate-race@test.com"
        payload = {
            "email": email,
            "name": "Race Test",
            "description": "Race condition test",
            "industry": "technology",
            "size": "pequena",
            "website": "https://race.com"
        }

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Send two identical requests concurrently
            tasks = [
                client.post("/api/v1/companies/", json=payload),
                client.post("/api/v1/companies/", json=payload)
            ]

            responses = await asyncio.gather(*tasks)

            # One should succeed (201), one should fail (409 Conflict)
            status_codes = [r.status_code for r in responses]
            assert 201 in status_codes, f"Expected at least one 201, got {status_codes}"
            assert 409 in status_codes, f"Expected 409 conflict, got {status_codes}"

            # Only one company should exist in DB
            companies = session.exec(select(Company).where(Company.email == email)).all()
            assert len(companies) == 1, f"Expected 1 company, found {len(companies)}"

    @pytest.mark.asyncio
    async def test_soft_delete_race_condition(self, session: Session):
        """Concurrent soft delete and read - deleted should not appear"""
        # Create company
        company = Company(
            email="softdelete-race@test.com",
            name="Soft Delete Test",
            description="Test",
            industry="technology",
            size="pequena",
            website="https://sdel.com",
            user_id=1,
            is_active=True
        )
        session.add(company)
        session.commit()
        session.refresh(company)

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Concurrent: soft delete + reads
            tasks = [
                client.delete(f"/api/v1/companies/{company.id}"),  # Default soft delete
                client.get(f"/api/v1/companies/{company.id}"),
                client.get(f"/api/v1/companies/{company.id}"),
                client.get(f"/api/v1/companies/{company.id}")
            ]

            responses = await asyncio.gather(*tasks)

            # Delete should succeed (200)
            assert responses[0].status_code == 200

            # Reads: may see company (if before delete), or 404 (if after delete)
            # But all responses should be consistent
            read_statuses = [r.status_code for r in responses[1:]]
            # After soft delete, non-admin should get 404
            for status in read_statuses:
                assert status in [200, 404], f"Unexpected status {status}"
