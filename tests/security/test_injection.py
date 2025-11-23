"""
Fase 3.2: Security Tests - Injection Prevention
Tests para prevenir SQL injection, NoSQL injection, y similares
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session


class TestSQLInjectionPrevention:
    """Test SQL injection prevention"""

    def test_email_field_sql_injection_attempt(self, client_with_admin: TestClient):
        """Email field should not allow SQL injection"""
        malicious_payloads = [
            "test@test.com'; DROP TABLE companies; --",
            "test@test.com' OR '1'='1",
            "test@test.com\" OR \"1\"=\"1",
            "test@test.com' UNION SELECT * FROM users --",
        ]

        for payload in malicious_payloads:
            # Attempt to create company with SQL injection in email
            company_data = {
                "email": payload,
                "name": "Injection Test",
                "description": "Test",
                "industry": "technology",
                "size": "pequena",
                "website": "https://injection.com"
            }
            response = client_with_admin.post("/api/v1/companies/", json=company_data)

            # Should either reject (400/422) or safely create with payload as literal string
            # Should NOT execute SQL
            assert response.status_code in [201, 400, 422], \
                f"Payload {payload} resulted in {response.status_code}"

            # If created, verify the email is stored as-is (literal string), not executed
            if response.status_code == 201:
                created_company = response.json()
                assert created_company["email"] == payload, \
                    f"Email should be stored as literal string, got {created_company['email']}"

    def test_name_field_sql_injection(self, client_with_admin: TestClient):
        """Name field should sanitize SQL injection attempts"""
        injections = [
            {"name": "'; DROP TABLE companies; --"},
            {"name": "\" OR 1=1 --"},
            {"name": "1'); DELETE FROM companies; --"},
        ]

        for injection in injections:
            company_data = {
                "email": "injection-name@test.com",
                "name": injection["name"],
                "description": "Test",
                "industry": "technology",
                "size": "pequena",
                "website": "https://test.com"
            }
            response = client_with_admin.post("/api/v1/companies/", json=company_data)

            # Should succeed with name stored as literal
            assert response.status_code in [201, 400, 422]  # May reject for other validation reasons
            if response.status_code == 201:
                # Name should be stored as-is, not executed
                assert response.json()["name"] == injection["name"]

    def test_description_field_sql_injection(self, client_with_admin: TestClient):
        """Large description field with injection attempts"""
        description = "Normal text ' OR '1'='1" * 100  # Repeated injection attempts

        company_data = {
            "email": "injection-desc@test.com",
            "name": "Test Company",
            "description": description,
            "industry": "technology",
            "size": "pequena",
            "website": "https://test.com"
        }
        response = client_with_admin.post("/api/v1/companies/", json=company_data)

        # Should handle large injection attempts
        assert response.status_code in [201, 400, 422]
        if response.status_code == 201:
            assert response.json()["description"] == description

    def test_query_parameter_injection(self, client_with_admin: TestClient):
        """Query parameters should be safely parameterized"""
        # Try SQL injection in query parameters
        injection_params = [
            "/api/v1/companies/?industry=technology' OR '1'='1",
            "/api/v1/companies/?skip=0; DELETE FROM companies; --",
            "/api/v1/companies/?limit=10 OR 1=1",
        ]

        for endpoint in injection_params:
            response = client_with_admin.get(endpoint)
            # Should not crash or return error 500
            assert response.status_code != 500, f"Query injection crashed: {endpoint}"

    def test_filter_injection_safety(self, client_with_admin: TestClient):
        """Complex filter queries should be safe"""
        filters = [
            "industry=tech' OR industry='",
            "size=pequena\"; DROP TABLE companies; --",
            "name=Test' UNION SELECT * FROM users --",
        ]

        for filter_str in filters:
            response = client_with_admin.get(f"/api/v1/companies/?{filter_str}")
            # Should handle gracefully
            assert response.status_code in [200, 400, 422]


class TestXSSPrevention:
    """Test XSS (Cross-Site Scripting) prevention"""

    def test_xss_in_company_name(self, client_with_admin: TestClient):
        """Company name should not execute JS"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "Test<img src=x onerror=alert('xss')>",
            "Test<svg onload=alert('xss')>",
            "Test<iframe src='javascript:alert(\"xss\")'></iframe>",
        ]

        for xss in xss_payloads:
            company_data = {
                "email": f"xss-{xss[:10]}@test.com",
                "name": xss,
                "description": "XSS test",
                "industry": "technology",
                "size": "pequena",
                "website": "https://xss.com"
            }
            response = client_with_admin.post("/api/v1/companies/", json=company_data)

            # Should accept or reject, but not execute
            assert response.status_code in [201, 400, 422]

            # If created, verify payload is in response as literal string, not executed
            if response.status_code == 201:
                data = response.json()
                # Should be stored/returned as literal string
                assert xss in data["name"]
                # Should NOT be in response as executable code
                # (The test client doesn't execute JS, but verify it's in raw response)

    def test_xss_in_description(self, client_with_admin: TestClient):
        """Description field with XSS attempts"""
        xss_payload = "<script>document.location='http://attacker.com'</script>"

        company_data = {
            "email": "xss-desc@test.com",
            "name": "Test",
            "description": xss_payload,
            "industry": "technology",
            "size": "pequena",
            "website": "https://test.com"
        }
        response = client_with_admin.post("/api/v1/companies/", json=company_data)

        # Should handle gracefully
        assert response.status_code in [201, 400, 422]
        if response.status_code == 201:
            # Payload should be stored as literal string
            data = response.json()
            assert xss_payload in data.get("description", "")

    def test_xss_in_website_url(self, client_with_admin: TestClient):
        """Website URL field with XSS attempts"""
        xss_urls = [
            "javascript:alert('xss')",
            "http://test.com<script>alert('xss')</script>",
            "data:text/html,<script>alert('xss')</script>",
        ]

        for url in xss_urls:
            company_data = {
                "email": f"xss-url-{url[:10]}@test.com",
                "name": "Test",
                "description": "Test",
                "industry": "technology",
                "size": "pequena",
                "website": url
            }
            response = client_with_admin.post("/api/v1/companies/", json=company_data)

            # May reject due to URL validation
            assert response.status_code in [201, 422, 400]


class TestPathTraversalPrevention:
    """Test path traversal prevention"""

    def test_path_traversal_in_company_id(self, client_with_admin: TestClient):
        """Company ID should not allow path traversal"""
        traversal_ids = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "test/../../admin",
        ]

        for traversal_id in traversal_ids:
            response = client_with_admin.get(f"/api/v1/companies/{traversal_id}")
            # Should return 404 or 400, not expose file system
            assert response.status_code in [400, 404, 422]


class TestDataValidation:
    """Test input validation"""

    def test_invalid_email_format(self, client_with_admin: TestClient):
        """Invalid emails should be rejected"""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user name@example.com",
            "",
        ]

        for invalid_email in invalid_emails:
            company_data = {
                "email": invalid_email,
                "name": "Test",
                "description": "Test",
                "industry": "technology",
                "size": "pequena",
                "website": "https://test.com"
            }
            response = client_with_admin.post("/api/v1/companies/", json=company_data)

            # Should reject invalid emails
            assert response.status_code in [400, 422], f"Invalid email {invalid_email} was accepted"

    def test_invalid_url_format(self, client_with_admin: TestClient):
        """Invalid URLs should be rejected or handled safely"""
        invalid_urls = [
            "not a url",
            "ht!tp://invalid",
            "ftp://unsupported",
        ]

        for invalid_url in invalid_urls:
            company_data = {
                "email": f"invalid-url-{invalid_url[:10]}@test.com",
                "name": "Test",
                "description": "Test",
                "industry": "technology",
                "size": "pequena",
                "website": invalid_url
            }
            response = client_with_admin.post("/api/v1/companies/", json=company_data)

            # Should reject or accept gracefully (depends on validation logic)
            assert response.status_code != 500

    def test_oversized_payload(self, client_with_admin: TestClient):
        """Very large payloads should be rejected"""
        huge_description = "X" * (1024 * 1024)  # 1MB of text

        company_data = {
            "email": "huge@test.com",
            "name": "Test",
            "description": huge_description,
            "industry": "technology",
            "size": "pequena",
            "website": "https://test.com"
        }

        response = client_with_admin.post("/api/v1/companies/", json=company_data)

        # Should reject oversized payload
        assert response.status_code in [400, 413, 422], f"Oversized payload was accepted"

    def test_special_characters_handled_safely(self, client_with_admin: TestClient):
        """Special characters should be handled safely"""
        special_chars = "!@#$%^&*()_+-=[]{}|;:'\",.<>?/~`"

        company_data = {
            "email": "special@test.com",
            "name": f"Company with {special_chars}",
            "description": f"Description {special_chars}",
            "industry": "technology",
            "size": "pequena",
            "website": "https://test.com"
        }

        response = client_with_admin.post("/api/v1/companies/", json=company_data)

        # Should handle gracefully
        assert response.status_code in [201, 400, 422]
