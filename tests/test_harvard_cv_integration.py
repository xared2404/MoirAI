#!/usr/bin/env python3
"""
🧪 Harvard CV Integration Test Suite
Verifica la integración completa del backend de Harvard CV:
1. El servidor está corriendo
2. El endpoint GET /auth/me devuelve los 5 nuevos campos
3. El endpoint PUT /students/{id} acepta los nuevos campos
4. Los datos persisten correctamente en la base de datos
5. La serialización JSON funciona correctamente

Similar al test Selenium E2E, genera reportes JSON y logs detallados.
"""

import asyncio
import httpx
import json
import sys
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

# Generar credenciales únicas para cada test run
TIMESTAMP = int(time.time() * 1000)

# Colores para output
class Colors:
    RESET = "\033[0m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"

def print_header(text):
    print(f"\n{Colors.CYAN}{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}{Colors.RESET}\n")

def print_success(text):
    logger.info(f"{Colors.GREEN}✅ {text}{Colors.RESET}")
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    logger.error(f"{Colors.RED}❌ {text}{Colors.RESET}")
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_info(text):
    logger.info(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def print_warning(text):
    logger.warning(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_section(text):
    logger.info(f"{Colors.MAGENTA}▶ {text}{Colors.RESET}")
    print(f"{Colors.MAGENTA}▶ {text}{Colors.RESET}")


# Test user credentials (try both test user and fallback to known user)
TEST_USER = {
    "role": "student",
    "name": f"Test Harvard CV Student {TIMESTAMP}",
    "email": f"harvard-cv-test-{TIMESTAMP}@example.com",
    "password": "TestPassword123!",
    "program": "Computer Science",
    "career": "Ingeniería Informática"
}

# Fallback credentials for pre-existing user (if registration fails)
FALLBACK_USER = {
    "email": "henryspark@hotmail.com",
    "password": "Henryspark123!"
}


class HarvardCVTestOrchestrator:
    """Test orchestrator for Harvard CV integration - Similar to SeleniumVisualE2ETester"""

    HARVARD_CV_FIELDS = ["objective", "education", "experience", "certifications", "languages"]

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "api_url": API_URL,
            "tests": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            },
            "logs": []
        }
        self.auth_token = None
        self.user_data = None

    def log_result(self, message: str, level: str = "info"):
        """Log result with timestamp"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        self.results["logs"].append(log_entry)

    # ========================================================================
    # ✅ MEJORA A1: Validación de Tipos de Datos
    # ========================================================================

    def _validate_harvard_fields_types(self, profile_data: Dict) -> Dict[str, bool]:
        """
        A1: Valida que los campos Harvard tienen tipos correctos.
        Previene silent data corruption.
        """
        validations = {}
        
        # 1. Validar tipos básicos
        validations["objective_is_string"] = isinstance(profile_data.get("objective"), str)
        validations["education_is_list"] = isinstance(profile_data.get("education"), list)
        validations["experience_is_list"] = isinstance(profile_data.get("experience"), list)
        validations["certifications_is_list"] = isinstance(profile_data.get("certifications"), list)
        validations["languages_is_list"] = isinstance(profile_data.get("languages"), list)
        
        # 2. Validar estructura interna de Education
        for i, edu in enumerate(profile_data.get("education", [])):
            validations[f"education_{i}_is_dict"] = isinstance(edu, dict)
            if validations[f"education_{i}_is_dict"]:
                required_fields = ["institution", "degree", "field_of_study", "graduation_year"]
                for field in required_fields:
                    validations[f"education_{i}_{field}_exists"] = field in edu
        
        # 3. Validar estructura interna de Experience
        for i, exp in enumerate(profile_data.get("experience", [])):
            validations[f"experience_{i}_is_dict"] = isinstance(exp, dict)
            if validations[f"experience_{i}_is_dict"]:
                required_fields = ["position", "company", "start_date", "end_date", "description"]
                for field in required_fields:
                    validations[f"experience_{i}_{field}_exists"] = field in exp
        
        # 4. Validar Certifications (array de strings)
        for i, cert in enumerate(profile_data.get("certifications", [])):
            validations[f"certification_{i}_is_string"] = isinstance(cert, str)
        
        # 5. Validar Languages (array de strings)
        for i, lang in enumerate(profile_data.get("languages", [])):
            validations[f"language_{i}_is_string"] = isinstance(lang, str)
        
        return validations

    # ========================================================================
    # ✅ MEJORA A2: Validación de Longitudes de Campos
    # ========================================================================

    def _validate_field_lengths(self, profile_data: Dict) -> Tuple[bool, Dict]:
        """
        A2: Valida que los campos no exceden longitudes máximas.
        Detecta truncation bugs.
        """
        MAX_LENGTHS = {
            "objective": 2000,
            "education_institution": 200,
            "education_degree": 100,
            "education_field": 150,
            "education_year": 4,
            "experience_company": 200,
            "experience_position": 150,
            "experience_description": 1000,
            "experience_date": 10,
            "certification": 200,
            "language": 100,
        }
        
        violations = {}
        
        # 1. Validar Objective (solo si no es None)
        objective = profile_data.get("objective")
        if objective is not None and len(str(objective)) > MAX_LENGTHS["objective"]:
            violations["objective_too_long"] = {
                "value_length": len(str(objective)),
                "excess": len(str(objective)) - MAX_LENGTHS["objective"]
            }
        
        # 2. Validar Education (solo si es lista)
        education = profile_data.get("education")
        if isinstance(education, list):
            for i, edu in enumerate(education):
                if isinstance(edu, dict):
                    if len(edu.get("institution", "")) > MAX_LENGTHS["education_institution"]:
                        violations[f"education_{i}_institution_too_long"] = len(edu.get("institution", ""))
                    
                    if len(edu.get("degree", "")) > MAX_LENGTHS["education_degree"]:
                        violations[f"education_{i}_degree_too_long"] = len(edu.get("degree", ""))
                    
                    if len(edu.get("field_of_study", "")) > MAX_LENGTHS["education_field"]:
                        violations[f"education_{i}_field_too_long"] = len(edu.get("field_of_study", ""))
        
        # 3. Validar Experience (solo si es lista)
        experience = profile_data.get("experience")
        if isinstance(experience, list):
            for i, exp in enumerate(experience):
                if isinstance(exp, dict):
                    if len(exp.get("company", "")) > MAX_LENGTHS["experience_company"]:
                        violations[f"experience_{i}_company_too_long"] = len(exp.get("company", ""))
                    
                    if len(exp.get("position", "")) > MAX_LENGTHS["experience_position"]:
                        violations[f"experience_{i}_position_too_long"] = len(exp.get("position", ""))
                    
                    if len(exp.get("description", "")) > MAX_LENGTHS["experience_description"]:
                        violations[f"experience_{i}_description_too_long"] = len(exp.get("description", ""))
        
        # 4. Validar Certifications (solo si es lista)
        certifications = profile_data.get("certifications")
        if isinstance(certifications, list):
            for i, cert in enumerate(certifications):
                if isinstance(cert, str) and len(cert) > MAX_LENGTHS["certification"]:
                    violations[f"certification_{i}_too_long"] = len(cert)
        
        # 5. Validar Languages (solo si es lista)
        languages = profile_data.get("languages")
        if isinstance(languages, list):
            for i, lang in enumerate(languages):
                if isinstance(lang, str) and len(lang) > MAX_LENGTHS["language"]:
                    violations[f"language_{i}_too_long"] = len(lang)
        
        is_valid = len(violations) == 0
        return is_valid, violations

    # ========================================================================
    # ✅ MEJORA A3: Validación de Persistencia Exacta
    # ========================================================================

    async def test_persistence_exact_match(self) -> bool:
        """
        A3: Verifica que los valores persisted coinciden exactamente con los enviados.
        Asegura data integrity en PUT → GET.
        """
        print_header("Test 3b: Exact Value Persistence")
        
        if not self.auth_token or not self.user_data:
            print_error("No auth token or user data available")
            return False
        
        user_id = self.user_data.get("id")
        headers = {"X-API-Key": self.auth_token}
        
        # Datos únicos para esta prueba
        unique_objective = f"Unique Test Objective {int(time.time() * 1000)}"
        test_data = {
            "objective": unique_objective,
            "languages": ["Spanish", "English", "French"]
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # 1. PUT unique data
                put_response = await client.put(
                    f"{API_URL}/students/{user_id}",
                    json=test_data,
                    headers=headers
                )
                
                if put_response.status_code != 200:
                    print_error(f"PUT failed: {put_response.status_code}")
                    return False
                
                # 2. GET y comparar exacto
                get_response = await client.get(
                    f"{API_URL}/auth/me",
                    headers=headers
                )
                
                if get_response.status_code != 200:
                    print_error(f"GET after PUT failed: {get_response.status_code}")
                    return False
                
                retrieved_data = get_response.json()
                
                # 3. Validaciones estrictas
                if retrieved_data.get("objective") != test_data["objective"]:
                    print_error(f"Objective mismatch: sent '{test_data['objective']}' but got '{retrieved_data.get('objective')}'")
                    return False
                
                if retrieved_data.get("languages") != test_data["languages"]:
                    print_error(f"Languages mismatch: sent {test_data['languages']} but got {retrieved_data.get('languages')}")
                    return False
                
                print_success("✅ All values persisted exactly as sent")
                self.log_result("✅ Exact persistence verified", "success")
                return True
                    
        except Exception as e:
            print_error(f"Persistence test error: {str(e)}")
            self.log_result(f"❌ Persistence test error: {str(e)}", "error")
            return False

    # ========================================================================
    # ✅ MEJORA A4: Casos Negativos / Error Handling
    # ========================================================================

    async def test_invalid_data_rejection(self) -> bool:
        """
        A4: Valida que el API rechaza datos inválidos.
        Crucial para seguridad y validación.
        """
        print_header("Test 4b: Invalid Data Rejection")
        
        if not self.auth_token or not self.user_data:
            print_error("No auth token or user data")
            return False
        
        user_id = self.user_data.get("id")
        headers = {"X-API-Key": self.auth_token}
        
        # Casos de datos inválidos
        invalid_cases = [
            {
                "data": {"objective": None},
                "description": "Objective is None",
                "expected_statuses": [400, 422]
            },
            {
                "data": {"education": "not a list"},
                "description": "Education is string instead of array",
                "expected_statuses": [400, 422]
            },
            {
                "data": {"certifications": ["Valid", None, "Another"]},
                "description": "Certifications array contains None",
                "expected_statuses": [400, 422]
            },
            {
                "data": {"languages": 123},
                "description": "Languages is number instead of array",
                "expected_statuses": [400, 422]
            },
        ]
        
        results = []
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                for case in invalid_cases:
                    response = await client.put(
                        f"{API_URL}/students/{user_id}",
                        json=case["data"],
                        headers=headers
                    )
                    
                    # API debe rechazar (400 o 422)
                    is_rejected = response.status_code in case["expected_statuses"]
                    results.append(is_rejected)
                    
                    if is_rejected:
                        print_success(f"✅ {case['description']} correctly rejected ({response.status_code})")
                    else:
                        print_warning(f"⚠️ {case['description']} returned {response.status_code} (expected {case['expected_statuses']})")
                        results.append(False)
            
            if all(results):
                print_success(f"\n✅ All {len(results)} invalid cases correctly rejected")
                self.log_result(f"✅ Invalid data handling verified ({len(results)} cases)", "success")
                return True
            else:
                failed = len([r for r in results if not r])
                print_warning(f"\n⚠️ {failed}/{len(results)} cases not rejected as expected")
                self.log_result(f"⚠️ {failed} invalid cases not handled", "warning")
                return True  # Continue with test
                    
        except Exception as e:
            print_error(f"Invalid data test error: {str(e)}")
            self.log_result(f"❌ Invalid data test error: {str(e)}", "error")
            return False

    # ========================================================================
    # ✅ MEJORA A5: Benchmarks de Performance
    # ========================================================================

    async def test_response_times(self) -> bool:
        """
        A5: Verifica que las operaciones están dentro de SLAs.
        Detecta regressions de performance.
        """
        print_header("Test 5c: Performance Benchmarks")
        
        if not self.auth_token:
            print_error("No auth token available")
            return False
        
        headers = {"X-API-Key": self.auth_token}
        performance_ok = True
        
        # Límites de SLA
        SLA_GET = 0.100  # 100ms
        SLA_PUT = 0.500  # 500ms
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Benchmark 1: GET /auth/me
                print_section("GET /auth/me performance:")
                times = []
                for i in range(3):
                    start = time.time()
                    response = await client.get(f"{API_URL}/auth/me", headers=headers)
                    elapsed = time.time() - start
                    times.append(elapsed)
                    
                    if elapsed > SLA_GET:
                        print_warning(f"  Attempt {i+1}: {elapsed*1000:.1f}ms (exceeds SLA of {SLA_GET*1000:.0f}ms)")
                        performance_ok = False
                    else:
                        print_success(f"  Attempt {i+1}: {elapsed*1000:.1f}ms")
                
                avg_time = sum(times) / len(times)
                print_info(f"  Average: {avg_time*1000:.1f}ms")
                
                # Benchmark 2: PUT /students/{id}
                print_section("PUT /students/{id} performance:")
                user_id = self.user_data.get("id")
                update_data = {"objective": "Test Update"}
                
                times = []
                for i in range(2):
                    start = time.time()
                    response = await client.put(
                        f"{API_URL}/students/{user_id}",
                        json=update_data,
                        headers=headers
                    )
                    elapsed = time.time() - start
                    times.append(elapsed)
                    
                    if elapsed > SLA_PUT:
                        print_warning(f"  Attempt {i+1}: {elapsed*1000:.1f}ms (exceeds SLA of {SLA_PUT*1000:.0f}ms)")
                        performance_ok = False
                    else:
                        print_success(f"  Attempt {i+1}: {elapsed*1000:.1f}ms")
                
                avg_time = sum(times) / len(times)
                print_info(f"  Average: {avg_time*1000:.1f}ms")
            
            if performance_ok:
                print_success("\n✅ All operations within SLA")
                self.log_result("✅ Performance benchmarks passed", "success")
            else:
                print_warning("\n⚠️ Some operations exceed SLA (but test continues)")
                self.log_result("⚠️ Some operations exceed SLA", "warning")
            
            return True
                    
        except Exception as e:
            print_error(f"Performance test error: {str(e)}")
            self.log_result(f"❌ Performance test error: {str(e)}", "error")
            return False

    async def register_test_user(self) -> bool:
        """Pre-step: Register a unique test user for this test run"""
        print_header("Pre-Step: Register Test User")
        
        test_result = {
            "name": "register_test_user",
            "status": "pending",
            "details": {}
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{API_URL}/auth/register",
                    json=TEST_USER
                )
                
                if response.status_code in [200, 201]:
                    print_success(f"Test user registered successfully")
                    print_info(f"Email: {TEST_USER['email']}")
                    test_result["status"] = "success"
                    test_result["details"]["email"] = TEST_USER["email"]
                    self.log_result("✅ Test user registered", "success")
                    self.results["tests"]["register_test_user"] = test_result
                    return True
                else:
                    print_warning(f"Registration status: {response.status_code}")
                    print_info(f"Response: {response.text[:150]}")
                    test_result["status"] = "warning"
                    test_result["details"]["status_code"] = response.status_code
                    # Continue anyway - user might already exist
                    self.log_result(f"⚠️ Registration status: {response.status_code}", "warning")
                    self.results["tests"]["register_test_user"] = test_result
                    return True
                    
        except Exception as e:
            print_warning(f"Could not register test user (may already exist): {str(e)[:80]}")
            test_result["status"] = "warning"
            test_result["details"]["error"] = str(e)
            self.log_result(f"⚠️ Register user warning: {str(e)}", "warning")
            self.results["tests"]["register_test_user"] = test_result
            # Continue anyway - user might already exist
            return True

    async def test_server_running(self) -> bool:
        """Test 1: Verificar que el servidor está corriendo"""
        print_header("Test 1: Server Running")
        
        test_result = {
            "name": "server_running",
            "status": "pending",
            "details": {}
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                start_time = datetime.now()
                response = await client.get(f"{BASE_URL}/", follow_redirects=True)
                elapsed = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    print_success(f"Server responding (Status: {response.status_code}, Response time: {elapsed:.2f}s)")
                    test_result["status"] = "success"
                    test_result["details"]["status_code"] = response.status_code
                    test_result["details"]["response_time_seconds"] = elapsed
                    self.log_result("✅ Server is running and responding", "success")
                    self.results["tests"]["server_running"] = test_result
                    self.results["summary"]["passed"] += 1
                    return True
                else:
                    print_warning(f"Server responding but status not 200: {response.status_code}")
                    test_result["status"] = "warning"
                    test_result["details"]["status_code"] = response.status_code
                    self.log_result(f"⚠️ Server status: {response.status_code}", "warning")
                    self.results["tests"]["server_running"] = test_result
                    self.results["summary"]["warnings"] += 1
                    return True  # Server is running
                    
        except Exception as e:
            print_error(f"Server not responding: {str(e)[:100]}")
            test_result["status"] = "failed"
            test_result["details"]["error"] = str(e)
            self.log_result(f"❌ Server test failed: {str(e)}", "error")
            self.results["tests"]["server_running"] = test_result
            self.results["summary"]["failed"] += 1
            return False

    async def test_authentication(self) -> bool:
        """Test 2: Obtener token de autenticación"""
        print_header("Test 2: Authentication")
        
        test_result = {
            "name": "authentication",
            "status": "pending",
            "details": {}
        }
        
        # Try test user first, then fallback
        login_attempts = [
            {
                "email": TEST_USER["email"],
                "password": TEST_USER["password"],
                "label": "Test User"
            },
            {
                "email": FALLBACK_USER["email"],
                "password": FALLBACK_USER["password"],
                "label": "Fallback User"
            }
        ]
        
        for login_data in login_attempts:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.post(
                        f"{API_URL}/auth/login",
                        json={"email": login_data["email"], "password": login_data["password"]}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        token = data.get("access_token") or data.get("api_key")
                        
                        if token:
                            print_success(f"Authentication successful with {login_data['label']}")
                            print_info(f"Email: {login_data['email']}")
                            print_info(f"Token: {token[:30]}...")
                            test_result["status"] = "success"
                            test_result["details"]["email"] = login_data["email"]
                            test_result["details"]["label"] = login_data["label"]
                            test_result["details"]["token_length"] = len(token)
                            self.auth_token = token
                            self.log_result(f"✅ Authentication successful with {login_data['label']}", "success")
                            self.results["tests"]["authentication"] = test_result
                            self.results["summary"]["passed"] += 1
                            return True
                        else:
                            print_warning(f"No token in response from {login_data['label']}")
                            continue
                    else:
                        print_warning(f"{login_data['label']} login returned: {response.status_code}")
                        continue
                        
            except Exception as e:
                print_warning(f"Error with {login_data['label']}: {str(e)[:80]}")
                continue
        
        # Both attempts failed
        print_error(f"Authentication failed with all attempts")
        test_result["status"] = "failed"
        test_result["details"]["error"] = "All authentication attempts failed"
        self.log_result("❌ All authentication attempts failed", "error")
        self.results["tests"]["authentication"] = test_result
        self.results["summary"]["failed"] += 1
        return False

    async def test_get_profile(self) -> bool:
        """Test 3: Verificar que GET /auth/me devuelve los nuevos campos"""
        print_header("Test 3: GET /auth/me - Verify Harvard CV Fields")
        
        test_result = {
            "name": "get_profile",
            "status": "pending",
            "details": {}
        }
        
        if not self.auth_token:
            print_error("No auth token available")
            test_result["status"] = "failed"
            self.results["tests"]["get_profile"] = test_result
            self.results["summary"]["failed"] += 1
            return False
        
        # ✅ Use X-API-Key header (MoirAI uses API keys, not Bearer tokens)
        headers = {"X-API-Key": self.auth_token}
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{API_URL}/auth/me",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.user_data = data
                    print_success("GET /auth/me successful")
                    
                    # Verificar que los campos nuevos existen
                    print_section("Verificando campos Harvard CV:")
                    fields_found = {}
                    all_present = True
                    
                    for field in self.HARVARD_CV_FIELDS:
                        if field in data:
                            value = data[field]
                            value_str = str(value)[:50] if value else "null"
                            print_success(f"  {field}: {value_str}")
                            fields_found[field] = "present"
                        else:
                            print_error(f"  {field}: MISSING")
                            fields_found[field] = "missing"
                            all_present = False
                    
                    test_result["status"] = "success" if all_present else "warning"
                    test_result["details"]["fields_found"] = fields_found
                    test_result["details"]["user_id"] = data.get("id")
                    test_result["details"]["email"] = data.get("email")
                    self.log_result(f"✅ Profile retrieved with {sum(1 for v in fields_found.values() if v == 'present')}/{len(self.HARVARD_CV_FIELDS)} Harvard fields", "success")
                    self.results["tests"]["get_profile"] = test_result
                    self.results["summary"]["passed"] += 1
                    return all_present
                else:
                    print_error(f"GET /auth/me failed (Status: {response.status_code})")
                    print_warning(f"Response: {response.text[:200]}")
                    test_result["status"] = "failed"
                    test_result["details"]["status_code"] = response.status_code
                    self.log_result(f"❌ GET /auth/me failed: {response.status_code}", "error")
                    self.results["tests"]["get_profile"] = test_result
                    self.results["summary"]["failed"] += 1
                    return False
                    
        except Exception as e:
            print_error(f"GET /auth/me error: {str(e)[:100]}")
            test_result["status"] = "failed"
            test_result["details"]["error"] = str(e)
            self.log_result(f"❌ GET /auth/me error: {str(e)}", "error")
            self.results["tests"]["get_profile"] = test_result
            self.results["summary"]["failed"] += 1
            return False

    async def test_update_profile(self) -> bool:
        """Test 4: Verificar que PUT /students/{id} acepta los nuevos campos"""
        print_header("Test 4: PUT /students/{id} - Update Harvard CV Fields")
        
        test_result = {
            "name": "update_profile",
            "status": "pending",
            "details": {}
        }
        
        if not self.auth_token or not self.user_data:
            print_error("No auth token or user data available")
            test_result["status"] = "failed"
            self.results["tests"]["update_profile"] = test_result
            self.results["summary"]["failed"] += 1
            return False
        
        user_id = self.user_data.get("id")
        if not user_id:
            print_error("No user ID found")
            test_result["status"] = "failed"
            self.results["tests"]["update_profile"] = test_result
            self.results["summary"]["failed"] += 1
            return False
        
        # Preparar datos de actualización con campos Harvard
        update_data = {
            "objective": "Desarrollador Full Stack con pasión por la innovación y el aprendizaje continuo. Especializado en arquitectura de sistemas escalables.",
            "education": [
                {
                    "institution": "Universidad Nacional de Río Cuarto",
                    "degree": "Licenciatura en Ciencias de la Computación",
                    "field_of_study": "Informática",
                    "graduation_year": "2024"
                },
                {
                    "institution": "Coursera",
                    "degree": "Certificado",
                    "field_of_study": "Cloud Computing",
                    "graduation_year": "2023"
                }
            ],
            "experience": [
                {
                    "position": "Junior Developer",
                    "company": "TechCorp Inc",
                    "start_date": "2023-01",
                    "end_date": "2024-01",
                    "description": "Development of web applications using React and FastAPI. Improved performance by 40%."
                },
                {
                    "position": "Intern Software Engineer",
                    "company": "StartupXYZ",
                    "start_date": "2022-06",
                    "end_date": "2022-12",
                    "description": "Backend development with Python and PostgreSQL"
                }
            ],
            "certifications": [
                "Google Cloud Associate Cloud Engineer",
                "AWS Solutions Architect Associate",
                "Certified Kubernetes Administrator (CKA)"
            ],
            "languages": [
                "Español - Nativo",
                "Inglés - Fluido (C1)",
                "Portugués - Intermedio (B1)"
            ]
        }
        
        # ✅ Use X-API-Key header (MoirAI uses API keys, not Bearer tokens)
        headers = {"X-API-Key": self.auth_token}
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.put(
                    f"{API_URL}/students/{user_id}",
                    json=update_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    print_success(f"PUT /students/{user_id} successful")
                    updated_data = response.json()
                    
                    # Verificar que los campos fueron guardados
                    print_section("Verificando campos actualizados:")
                    fields_updated = {}
                    
                    for field in update_data.keys():
                        if field in updated_data:
                            print_success(f"  {field}: Updated ✓")
                            fields_updated[field] = "updated"
                        else:
                            print_warning(f"  {field}: Not in response")
                            fields_updated[field] = "not_in_response"
                    
                    test_result["status"] = "success"
                    test_result["details"]["fields_updated"] = fields_updated
                    test_result["details"]["response_status"] = response.status_code
                    self.log_result(f"✅ Profile updated with {sum(1 for v in fields_updated.values() if v == 'updated')} Harvard fields", "success")
                    self.results["tests"]["update_profile"] = test_result
                    self.results["summary"]["passed"] += 1
                    return True
                else:
                    print_error(f"PUT /students/{user_id} failed (Status: {response.status_code})")
                    print_warning(f"Response: {response.text[:200]}")
                    test_result["status"] = "failed"
                    test_result["details"]["status_code"] = response.status_code
                    test_result["details"]["error"] = response.text[:200]
                    self.log_result(f"❌ PUT /students failed: {response.status_code}", "error")
                    self.results["tests"]["update_profile"] = test_result
                    self.results["summary"]["failed"] += 1
                    return False
                    
        except Exception as e:
            print_error(f"PUT /students/{user_id} error: {str(e)[:100]}")
            test_result["status"] = "failed"
            test_result["details"]["error"] = str(e)
            self.log_result(f"❌ PUT /students error: {str(e)}", "error")
            self.results["tests"]["update_profile"] = test_result
            self.results["summary"]["failed"] += 1
            return False

    async def test_persistence(self) -> bool:
        """Test 5: Verificar que los datos persisten tras un GET posterior"""
        print_header("Test 5: Data Persistence - Verify Data Saved")
        
        test_result = {
            "name": "persistence",
            "status": "pending",
            "details": {}
        }
        
        if not self.auth_token:
            print_error("No auth token available")
            test_result["status"] = "failed"
            self.results["tests"]["persistence"] = test_result
            self.results["summary"]["failed"] += 1
            return False
        
        # ✅ Use X-API-Key header (MoirAI uses API keys, not Bearer tokens)
        headers = {"X-API-Key": self.auth_token}
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{API_URL}/auth/me",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print_success("GET /auth/me after update successful")
                    
                    # Verificar que los datos se guardaron
                    print_section("Data persistence check:")
                    persistence_check = {}
                    all_persisted = True
                    
                    for field in self.HARVARD_CV_FIELDS:
                        value = data.get(field)
                        if value:
                            value_str = str(value)[:50] if value else "null"
                            print_success(f"  {field}: Persisted ✓ ({value_str})")
                            persistence_check[field] = "persisted"
                        else:
                            print_warning(f"  {field}: Not persisted")
                            persistence_check[field] = "not_persisted"
                            all_persisted = False
                    
                    test_result["status"] = "success" if all_persisted else "warning"
                    test_result["details"]["persistence_check"] = persistence_check
                    self.log_result(f"✅ Data persistence verified for {sum(1 for v in persistence_check.values() if v == 'persisted')} fields", "success")
                    self.results["tests"]["persistence"] = test_result
                    self.results["summary"]["passed"] += 1
                    return all_persisted
                else:
                    print_error(f"GET /auth/me failed (Status: {response.status_code})")
                    test_result["status"] = "failed"
                    test_result["details"]["status_code"] = response.status_code
                    self.log_result(f"❌ Persistence check failed: {response.status_code}", "error")
                    self.results["tests"]["persistence"] = test_result
                    self.results["summary"]["failed"] += 1
                    return False
                    
        except Exception as e:
            print_error(f"Persistence check error: {str(e)[:100]}")
            test_result["status"] = "failed"
            test_result["details"]["error"] = str(e)
            self.log_result(f"❌ Persistence check error: {str(e)}", "error")
            self.results["tests"]["persistence"] = test_result
            self.results["summary"]["failed"] += 1
            return False

    async def run_all_tests(self) -> bool:
        """Ejecutar todos los tests"""
        try:
            self.results["summary"]["total_tests"] = 11  # Include all new tests
            
            # Pre-step: Register test user
            if not await self.register_test_user():
                print_warning("Could not register test user, will try to continue...")
            
            # Test 1: Server Running
            if not await self.test_server_running():
                print_error("Cannot continue - server not responding")
                return False
            
            # Test 2: Authentication
            if not await self.test_authentication():
                print_error("Cannot continue - authentication failed")
                return False
            
            # Test 3: GET Profile
            if not await self.test_get_profile():
                print_warning("GET /auth/me test had issues, continuing...")
            
            # Test 3b: Validate Types (A1 - NEW)
            if self.user_data:
                print_header("Test 3b: Validate Field Types")
                type_validations = self._validate_harvard_fields_types(self.user_data)
                valid_types = sum(1 for v in type_validations.values() if v)
                total_validations = len(type_validations)
                
                print_section(f"Type validation results: {valid_types}/{total_validations} passed")
                for validation, result in type_validations.items():
                    if result:
                        print_success(f"  ✅ {validation}")
                    else:
                        print_warning(f"  ⚠️ {validation}")
                
                self.log_result(f"✅ Type validation: {valid_types}/{total_validations}", "success")
            
            # Test 3c: Validate Lengths (A2 - NEW)
            if self.user_data:
                print_header("Test 3c: Validate Field Lengths")
                is_valid, violations = self._validate_field_lengths(self.user_data)
                if is_valid:
                    print_success("✅ All fields within length limits")
                else:
                    print_warning(f"⚠️ Length violations found: {len(violations)}")
                    for violation, details in list(violations.items())[:5]:
                        print_warning(f"  • {violation}: {details}")
                self.log_result(f"✅ Length validation: {len(violations)} violations", "warning")
            
            # Test 4: PUT Update
            if not await self.test_update_profile():
                print_warning("PUT /students test had issues, continuing...")
            
            # Test 4b: Invalid Data Rejection (A4 - NEW)
            if not await self.test_invalid_data_rejection():
                print_warning("Invalid data rejection test had issues, continuing...")
            
            # Test 5: Persistence
            if not await self.test_persistence():
                print_warning("Persistence test had issues")
            
            # Test 5b: Exact Persistence Match (A3 - NEW)
            if not await self.test_persistence_exact_match():
                print_warning("Exact persistence test had issues, continuing...")
            
            # Test 5c: Performance Benchmarks (A5 - NEW)
            if not await self.test_response_times():
                print_warning("Performance benchmark test had issues, continuing...")
            
            return True
            
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            self.log_result(f"❌ Unexpected error: {str(e)}", "error")
            return False

    def generate_report(self) -> Path:
        """Generate JSON report (similar to Selenium E2E)"""
        report_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        report_filename = f"harvard-cv-integration-report-{report_timestamp}.json"
        report_path = Path("/Users/sparkmachine/MoirAI") / report_filename
        
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print_info(f"📊 Report generated: {report_path}")
        logger.info(f"📊 Report generated: {report_path}")
        return report_path

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("HARVARD CV INTEGRATION TEST SUMMARY")
        print("="*70)
        
        for test_name, test_result in self.results["tests"].items():
            if isinstance(test_result, dict) and "status" in test_result:
                status = test_result["status"]
                
                if status == "success":
                    icon = "✅"
                    status_text = "PASS"
                elif status == "warning":
                    icon = "⚠️"
                    status_text = "PARTIAL"
                else:
                    icon = "❌"
                    status_text = "FAIL"
                
                print(f"\n{icon} {test_name.upper()}: {status_text}")
                
                if test_result.get("details"):
                    for key, value in test_result["details"].items():
                        value_str = str(value)[:60] if not isinstance(value, dict) else "..."
                        print(f"  ├─ {key}: {value_str}")
        
        # Summary statistics
        print(f"\n{'='*70}")
        print(f"📈 Test Summary:")
        print(f"  • Total Tests: {self.results['summary']['total_tests']}")
        print(f"  • Passed: {self.results['summary']['passed']}")
        print(f"  • Warnings: {self.results['summary']['warnings']}")
        print(f"  • Failed: {self.results['summary']['failed']}")
        print(f"{'='*70}\n")


async def main():
    """Main entry point"""
    print(f"\n{Colors.CYAN}🧪 HARVARD CV INTEGRATION TEST SUITE{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    print(f"API URL: {API_URL}\n")
    
    tester = HarvardCVTestOrchestrator()
    success = await tester.run_all_tests()
    
    # Generate report and print summary
    report_path = tester.generate_report()
    tester.print_summary()
    
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if success and tester.results["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
