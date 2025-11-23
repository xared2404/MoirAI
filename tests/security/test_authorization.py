"""
Fase 3.2: Security Tests - Authorization/RBAC
Tests para prevenir escalation of privileges y RBAC violations
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.models import Company


class TestRBACEnforcement:
    """Test RBAC (Role-Based Access Control) enforcement"""

    def test_student_cannot_create_company(self, client_with_student: TestClient):
        """Student role should not be able to create companies"""
        company_data = {
            "email": "student-create@test.com",
            "name": "Student Created",
            "description": "Test",
            "industry": "technology",
            "size": "pequena",
            "website": "https://test.com"
        }
        response = client_with_student.post("/api/v1/companies/", json=company_data)

        # Should be denied
        assert response.status_code == 403, f"Student should not create, got {response.status_code}"

    def test_student_cannot_list_companies(self, client_with_student: TestClient):
        """Student role should not list companies"""
        response = client_with_student.get("/api/v1/companies/")

        # Should be denied (403) or require auth (401)
        assert response.status_code in [401, 403]

    def test_student_cannot_update_company(self, client_with_student: TestClient):
        """Student role should not update companies"""
        company_data = {
            "name": "Updated by Student",
            "description": "Test",
            "website": "https://updated.com"
        }
        response = client_with_student.put("/api/v1/companies/999", json=company_data)

        # Should be denied
        assert response.status_code in [401, 403]

    def test_student_cannot_delete_company(self, client_with_student: TestClient):
        """Student role should not delete companies"""
        response = client_with_student.delete("/api/v1/companies/999")

        # Should be denied
        assert response.status_code in [401, 403]

    def test_student_cannot_verify_company(self, client_with_student: TestClient):
        """Student role should not verify companies"""
        response = client_with_student.patch("/api/v1/companies/999/verify")

        # Should be denied
        assert response.status_code in [401, 403]

    def test_company_cannot_verify_other_company(self, client_with_company: TestClient, session: Session):
        """Company role should not verify other companies"""
        # Create a company (as admin would)
        other_company = Company(
            email="other-company@test.com",
            name="Other Company",
            description="Test",
            industry="technology",
            size="pequena",
            website="https://other.com",
            user_id=999,  # Different user_id
            is_verified=False
        )
        session.add(other_company)
        session.commit()
        session.refresh(other_company)

        # Try to verify as different company
        response = client_with_company.patch(f"/api/v1/companies/{other_company.id}/verify")

        # Should be denied (only admin can verify)
        assert response.status_code == 403, f"Company should not verify, got {response.status_code}"

    def test_company_cannot_hard_delete(self, client_with_company: TestClient, session: Session):
        """Company role should not be able to hard delete"""
        company = Company(
            email="hard-del@test.com",
            name="Hard Delete Test",
            description="Test",
            industry="technology",
            size="pequena",
            website="https://test.com",
            user_id=2  # company user_id
        )
        session.add(company)
        session.commit()
        session.refresh(company)

        # Try hard delete
        response = client_with_company.delete(f"/api/v1/companies/{company.id}?permanently=true&reason=Test")

        # Should be denied
        assert response.status_code == 403, f"Company should not hard delete, got {response.status_code}"

    def test_company_can_soft_delete_own(self, client_with_company: TestClient, session: Session):
        """Company CAN soft delete their own company"""
        company = Company(
            email="soft-del-own@test.com",
            name="Soft Delete Own",
            description="Test",
            industry="technology",
            size="pequena",
            website="https://test.com",
            user_id=2  # company user_id matches client_with_company
        )
        session.add(company)
        session.commit()
        session.refresh(company)

        # Soft delete own company
        response = client_with_company.delete(f"/api/v1/companies/{company.id}")

        # Should succeed (default is soft delete)
        assert response.status_code == 200

    def test_anonymous_cannot_access_any_endpoint(self, client_with_anonymous: TestClient):
        """Anonymous user should get 401 on all endpoints"""
        endpoints = [
            ("POST", "/api/v1/companies/", {"email": "test@test.com", "name": "Test", "description": "Test", "industry": "technology", "size": "pequena", "website": "https://test.com"}),
            ("GET", "/api/v1/companies/", None),
            ("GET", "/api/v1/companies/1", None),
            ("PUT", "/api/v1/companies/1", {"name": "Updated"}),
            ("PATCH", "/api/v1/companies/1/verify", None),
            ("PATCH", "/api/v1/companies/1/activate", None),
            ("DELETE", "/api/v1/companies/1", None),
            ("GET", "/api/v1/companies/1/search-students", None),
        ]

        for method, endpoint, payload in endpoints:
            if method == "GET":
                response = client_with_anonymous.get(endpoint)
            elif method == "POST":
                response = client_with_anonymous.post(endpoint, json=payload)
            elif method == "PUT":
                response = client_with_anonymous.put(endpoint, json=payload)
            elif method == "PATCH":
                response = client_with_anonymous.patch(endpoint, json=payload)
            elif method == "DELETE":
                response = client_with_anonymous.delete(endpoint)

            # All should return 401 for anonymous
            assert response.status_code == 401, \
                f"{method} {endpoint} should return 401 for anonymous, got {response.status_code}"


class TestPrivilegeEscalation:
    """Test privilege escalation prevention"""

    def test_company_cannot_modify_admin_field(self, client_with_company: TestClient, session: Session):
        """Company should not be able to set admin-only fields"""
        company = Company(
            email="admin-field@test.com",
            name="Admin Field Test",
            description="Test",
            industry="technology",
            size="pequena",
            website="https://test.com",
            user_id=2,
            is_verified=False
        )
        session.add(company)
        session.commit()
        session.refresh(company)

        # Try to set is_verified (admin-only)
        update_data = {
            "name": "Updated",
            "is_verified": True  # Try to escalate to verified
        }

        # Note: API might ignore unknown fields or reject
        response = client_with_company.put(f"/api/v1/companies/{company.id}", json=update_data)

        # Should succeed (update name) but ignore is_verified
        if response.status_code == 200:
            updated = response.json()
            # Should still be unverified
            assert updated["is_verified"] == False, "Company should not be able to self-verify"

    def test_company_cannot_access_other_company_data(self, client_with_company: TestClient, session: Session):
        """Company should not access/modify other company data"""
        other_company = Company(
            email="other@test.com",
            name="Other Company",
            description="Test",
            industry="technology",
            size="mediana",
            website="https://other.com",
            user_id=999,  # Different company
            is_verified=True
        )
        session.add(other_company)
        session.commit()
        session.refresh(other_company)

        own_company = Company(
            email="own@test.com",
            name="Own Company",
            description="Test",
            industry="technology",
            size="pequena",
            website="https://own.com",
            user_id=2  # client_with_company user
        )
        session.add(own_company)
        session.commit()
        session.refresh(own_company)

        # Can read own company
        response = client_with_company.get(f"/api/v1/companies/{own_company.id}")
        assert response.status_code == 200

        # Can update own company
        response = client_with_company.put(
            f"/api/v1/companies/{own_company.id}",
            json={"name": "Updated Own"}
        )
        assert response.status_code == 200

        # Cannot modify other company
        response = client_with_company.put(
            f"/api/v1/companies/{other_company.id}",
            json={"name": "Updated Other"}
        )
        assert response.status_code in [403, 404], f"Should deny access to other company, got {response.status_code}"


class TestDataIsolation:
    """Test data isolation between users"""

    def test_list_only_shows_verified_for_company(self, client_with_company: TestClient, session: Session):
        """Company should only see verified companies in list"""
        # Create verified company
        verified = Company(
            email="verified@test.com",
            name="Verified",
            description="Test",
            industry="technology",
            size="pequena",
            website="https://verified.com",
            user_id=1,
            is_verified=True
        )
        session.add(verified)

        # Create unverified company
        unverified = Company(
            email="unverified@test.com",
            name="Unverified",
            description="Test",
            industry="technology",
            size="pequena",
            website="https://unverified.com",
            user_id=1,
            is_verified=False
        )
        session.add(unverified)
        session.commit()

        # List as company
        response = client_with_company.get("/api/v1/companies/")
        assert response.status_code == 200

        companies = response.json().get("items", [])

        # Should see verified
        verified_emails = [c["email"] for c in companies]
        assert "verified@test.com" in verified_emails, "Should see verified companies"

        # Should NOT see unverified (unless is admin)
        assert "unverified@test.com" not in verified_emails, "Company should not see unverified"

    def test_soft_deleted_hidden_from_company(self, client_with_company: TestClient, session: Session):
        """Soft-deleted companies should be hidden from non-admin"""
        # Create and soft delete
        company = Company(
            email="softdel-hide@test.com",
            name="Soft Deleted",
            description="Test",
            industry="technology",
            size="pequena",
            website="https://test.com",
            user_id=1,
            is_active=False  # Soft deleted
        )
        session.add(company)
        session.commit()
        session.refresh(company)

        # Try to get as company
        response = client_with_company.get(f"/api/v1/companies/{company.id}")

        # Should get 404 (not visible)
        assert response.status_code == 404, f"Soft deleted should be hidden, got {response.status_code}"
