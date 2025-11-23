#!/usr/bin/env python3
"""
Frontend Integration Testing Script
Tests all API endpoints used by the frontend
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configuration
API_BASE = "http://localhost:8000/api/v1"
VERBOSE = True

# Test data
TEST_USER_EMAIL = "frontend_test@example.com"
TEST_USER_PASSWORD = "TestPass123"
TEST_USER_ROLE = "student"


class FrontendIntegrationTester:
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.session = requests.Session()
        self.results: List[Dict] = []
        self.test_count = 0
        self.passed_count = 0
        self.failed_count = 0
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] [{level}]"
        print(f"{prefix} {message}")
        
    def test(self, name: str, method: str, endpoint: str, 
             expected_status: int = 200, 
             data: Optional[Dict] = None,
             headers: Optional[Dict] = None) -> Tuple[bool, Dict]:
        """Execute a single API test"""
        
        self.test_count += 1
        url = f"{self.base_url}{endpoint}"
        
        # Prepare headers
        test_headers = headers or {}
        if self.token and "Authorization" not in test_headers:
            test_headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            if VERBOSE:
                self.log(f"[TEST #{self.test_count}] {name}")
                self.log(f"  {method} {endpoint}")
                
            if method == "GET":
                response = self.session.get(url, headers=test_headers)
            elif method == "POST":
                response = self.session.post(url, json=data, headers=test_headers)
            elif method == "PUT":
                response = self.session.put(url, json=data, headers=test_headers)
            elif method == "DELETE":
                response = self.session.delete(url, headers=test_headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Check status
            success = response.status_code == expected_status
            
            if VERBOSE:
                self.log(f"  Status: {response.status_code} (expected {expected_status})", 
                        "✓" if success else "✗")
                
                # Show response body if error
                if not success and response.text:
                    try:
                        resp_json = response.json()
                        self.log(f"  Response: {json.dumps(resp_json, indent=2)}", "DEBUG")
                    except:
                        self.log(f"  Response: {response.text[:200]}", "DEBUG")
            
            if success:
                self.passed_count += 1
            else:
                self.failed_count += 1
                
            # Store result
            self.results.append({
                "test_num": self.test_count,
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "status": response.status_code,
                "expected": expected_status,
                "passed": success,
                "response": response.json() if response.text else None
            })
            
            return success, response.json() if response.text else {}
            
        except Exception as e:
            self.log(f"  ERROR: {str(e)}", "✗")
            self.failed_count += 1
            self.results.append({
                "test_num": self.test_count,
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "status": 0,
                "expected": expected_status,
                "passed": False,
                "error": str(e)
            })
            return False, {}
    
    # ============================================================================
    # Authentication Endpoints
    # ============================================================================
    
    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        self.log("=" * 70)
        self.log("TESTING AUTHENTICATION ENDPOINTS", "TEST")
        self.log("=" * 70)
        
        # 1. Register
        register_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "first_name": "Test",
            "last_name": "User",
            "role": TEST_USER_ROLE
        }
        success, response = self.test(
            "POST /auth/register - New user registration",
            "POST", "/auth/register", 201, register_data
        )
        
        # 2. Login
        login_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        success, response = self.test(
            "POST /auth/login - User login",
            "POST", "/auth/login", 200, login_data
        )
        
        if success and "access_token" in response:
            self.token = response.get("access_token")
            self.log(f"  Token obtained: {self.token[:20]}...", "DEBUG")
            
            # Extract user_id if available
            if "user" in response:
                self.user_id = response["user"].get("id")
        
        # 3. Get current user
        success, response = self.test(
            "GET /auth/me - Get current user",
            "GET", "/auth/me", 200
        )
        
        if success and "id" in response:
            self.user_id = response.get("id")
            self.log(f"  User ID: {self.user_id}", "DEBUG")
    
    # ============================================================================
    # Student Endpoints
    # ============================================================================
    
    def test_student_endpoints(self):
        """Test student profile endpoints"""
        self.log("=" * 70)
        self.log("TESTING STUDENT ENDPOINTS", "TEST")
        self.log("=" * 70)
        
        if not self.user_id:
            self.log("No user_id available, skipping student tests", "WARN")
            return
        
        # 1. Get student profile
        success, response = self.test(
            "GET /students/{id} - Get student profile",
            "GET", f"/students/{self.user_id}", 200
        )
        
        # 2. Update student profile
        update_data = {
            "first_name": "Test",
            "last_name": "User",
            "phone": "+56912345678",
            "bio": "This is a test bio",
            "career": "Computer Science",
            "current_year": 2
        }
        success, response = self.test(
            "PUT /students/{id} - Update student profile",
            "PUT", f"/students/{self.user_id}", 200, update_data
        )
        
        # 3. Get resume (if uploaded)
        success, response = self.test(
            "GET /students/{id}/resume - Get student resume",
            "GET", f"/students/{self.user_id}/resume", 404  # Expect 404 if not uploaded
        )
    
    # ============================================================================
    # Jobs & Opportunities Endpoints
    # ============================================================================
    
    def test_jobs_endpoints(self):
        """Test job/opportunity endpoints"""
        self.log("=" * 70)
        self.log("TESTING JOBS & OPPORTUNITIES ENDPOINTS", "TEST")
        self.log("=" * 70)
        
        # 1. Search jobs
        search_data = {
            "keywords": "python",
            "location": "Santiago",
            "limit": 10
        }
        success, response = self.test(
            "POST /jobs/search - Search jobs",
            "POST", "/jobs/search", 200, search_data
        )
        
        # 2. Get all jobs
        success, response = self.test(
            "GET /jobs - Get all jobs",
            "GET", "/jobs?limit=20", 200
        )
        
        # Get a job ID for detail test
        if success and "data" in response and len(response["data"]) > 0:
            job_id = response["data"][0].get("id")
            
            # 3. Get job details
            success, response = self.test(
                "GET /jobs/{id} - Get job details",
                "GET", f"/jobs/{job_id}", 200
            )
    
    # ============================================================================
    # Matching & Recommendations Endpoints
    # ============================================================================
    
    def test_matching_endpoints(self):
        """Test matching and recommendation endpoints"""
        self.log("=" * 70)
        self.log("TESTING MATCHING & RECOMMENDATIONS ENDPOINTS", "TEST")
        self.log("=" * 70)
        
        if not self.user_id:
            self.log("No user_id available, skipping matching tests", "WARN")
            return
        
        # 1. Get recommendations
        rec_data = {
            "limit": 10,
            "threshold": 0.5
        }
        success, response = self.test(
            "POST /matching/recommendations - Get recommendations",
            "POST", "/matching/recommendations", 200, rec_data
        )
        
        # 2. Get match score
        success, response = self.test(
            "GET /matching/student/{id}/matching-score - Get match score",
            "GET", f"/matching/student/{self.user_id}/matching-score", 200
        )
    
    # ============================================================================
    # Applications Endpoints
    # ============================================================================
    
    def test_applications_endpoints(self):
        """Test application management endpoints"""
        self.log("=" * 70)
        self.log("TESTING APPLICATIONS ENDPOINTS", "TEST")
        self.log("=" * 70)
        
        if not self.user_id:
            self.log("No user_id available, skipping applications tests", "WARN")
            return
        
        # 1. Get my applications
        success, response = self.test(
            "GET /applications/my-applications - Get my applications",
            "GET", "/applications/my-applications", 200
        )
        
        # 2. Get applications with filters
        success, response = self.test(
            "GET /applications/my-applications?status=pending - Filter applications",
            "GET", "/applications/my-applications?status=pending", 200
        )
        
        # 3. Create application (if job exists)
        # This would need a valid job_id
        apply_data = {
            "job_id": 1,  # Placeholder
            "motivation": "I'm interested in this position"
        }
        success, response = self.test(
            "POST /applications - Create application",
            "POST", "/applications", 201, apply_data
        )
    
    # ============================================================================
    # CV/Resume Upload Endpoints
    # ============================================================================
    
    def test_cv_endpoints(self):
        """Test CV/resume upload endpoints"""
        self.log("=" * 70)
        self.log("TESTING CV/RESUME UPLOAD ENDPOINTS", "TEST")
        self.log("=" * 70)
        
        if not self.user_id:
            self.log("No user_id available, skipping CV tests", "WARN")
            return
        
        self.log("Skipping file upload test (requires multipart form data)", "INFO")
        self.log("Manual test: Upload PDF/DOCX file via frontend", "INFO")
        
        # In browser testing:
        # 1. POST /students/{id}/upload-resume with file
        # 2. GET /students/{id}/resume to download
        # 3. DELETE /students/{id}/resume to delete
    
    # ============================================================================
    # Search & Filter Endpoints
    # ============================================================================
    
    def test_search_endpoints(self):
        """Test search endpoints"""
        self.log("=" * 70)
        self.log("TESTING SEARCH ENDPOINTS", "TEST")
        self.log("=" * 70)
        
        # 1. Search jobs by title
        search_data = {"q": "Python"}
        success, response = self.test(
            "GET /jobs/search?q=Python - Search by title",
            "GET", "/jobs/search?q=Python", 200
        )
        
        # 2. Advanced search with filters
        success, response = self.test(
            "GET /jobs/search?location=Santiago&modality=remote - Advanced search",
            "GET", "/jobs/search?location=Santiago&modality=remote", 200
        )
    
    # ============================================================================
    # Error Cases
    # ============================================================================
    
    def test_error_cases(self):
        """Test error handling"""
        self.log("=" * 70)
        self.log("TESTING ERROR CASES", "TEST")
        self.log("=" * 70)
        
        # 1. Invalid credentials
        invalid_login = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        success, response = self.test(
            "POST /auth/login - Invalid credentials",
            "POST", "/auth/login", 401, invalid_login
        )
        
        # 2. Missing required fields
        incomplete_register = {
            "email": "test@example.com"
            # Missing password, name, etc
        }
        success, response = self.test(
            "POST /auth/register - Missing fields",
            "POST", "/auth/register", 422, incomplete_register
        )
        
        # 3. Invalid email format
        invalid_email = {
            "email": "invalid-email",
            "password": "TestPass123",
            "first_name": "Test",
            "last_name": "User"
        }
        success, response = self.test(
            "POST /auth/register - Invalid email format",
            "POST", "/auth/register", 422, invalid_email
        )
        
        # 4. Unauthorized access
        self.log("Testing unauthorized access to protected endpoint...")
        original_token = self.token
        self.token = None
        success, response = self.test(
            "GET /auth/me - Unauthorized (no token)",
            "GET", "/auth/me", 401
        )
        self.token = original_token
        
        # 5. Not found
        success, response = self.test(
            "GET /students/99999 - Not found",
            "GET", "/students/99999", 404
        )
    
    # ============================================================================
    # Report Generation
    # ============================================================================
    
    def generate_report(self):
        """Generate and print test report"""
        self.log("=" * 70)
        self.log("TEST REPORT", "REPORT")
        self.log("=" * 70)
        
        print(f"\nTotal Tests: {self.test_count}")
        print(f"✓ Passed: {self.passed_count}")
        print(f"✗ Failed: {self.failed_count}")
        print(f"Success Rate: {(self.passed_count/self.test_count)*100:.1f}%")
        
        print("\n" + "=" * 70)
        print("DETAILED RESULTS")
        print("=" * 70)
        
        for result in self.results:
            status = "✓ PASS" if result["passed"] else "✗ FAIL"
            print(f"\n[{result['test_num']:3d}] {status} - {result['name']}")
            print(f"      {result['method']} {result['endpoint']}")
            print(f"      Status: {result['status']} (expected {result['expected']})")
            
            if result.get("error"):
                print(f"      Error: {result['error']}")
        
        print("\n" + "=" * 70)
        print("FAILED TESTS SUMMARY")
        print("=" * 70)
        
        failed_tests = [r for r in self.results if not r["passed"]]
        if failed_tests:
            for result in failed_tests:
                print(f"✗ {result['name']}")
                print(f"  {result['method']} {result['endpoint']}")
        else:
            print("✓ All tests passed!")
        
        # Save report to file
        report_file = "/Users/sparkmachine/MoirAI/test_results_frontend_integration.json"
        with open(report_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": self.test_count,
                    "passed": self.passed_count,
                    "failed": self.failed_count,
                    "success_rate": (self.passed_count/self.test_count)*100
                },
                "results": self.results
            }, f, indent=2)
        
        self.log(f"Report saved to: {report_file}", "INFO")


def main():
    """Main test runner"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  MOIRAI FRONTEND INTEGRATION TEST SUITE".center(68) + "║")
    print("║" + "  Testing API Endpoints Used by Frontend".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    tester = FrontendIntegrationTester()
    
    try:
        # Run all test suites
        tester.test_auth_endpoints()
        time.sleep(0.5)
        
        tester.test_student_endpoints()
        time.sleep(0.5)
        
        tester.test_jobs_endpoints()
        time.sleep(0.5)
        
        tester.test_matching_endpoints()
        time.sleep(0.5)
        
        tester.test_applications_endpoints()
        time.sleep(0.5)
        
        tester.test_cv_endpoints()
        time.sleep(0.5)
        
        tester.test_search_endpoints()
        time.sleep(0.5)
        
        tester.test_error_cases()
        
        # Generate report
        tester.generate_report()
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
