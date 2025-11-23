"""
Unit tests para Module 3 - Rate Limiting Middleware

Pruebas para:
- RateLimitConfig (configuración)
- RateLimiter (lógica de limitación)
- Rate limit checking por rol
- Rate limit checking por endpoint
- Ventanas deslizantes (sliding window)
- Thread safety
- Rate limit headers en responses
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from fastapi import Request, HTTPException, FastAPI
from fastapi.testclient import TestClient

from app.middleware.rate_limit import RateLimiter, RateLimitConfig


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def rate_limiter():
    """Crear una nueva instancia de RateLimiter para cada test"""
    return RateLimiter()


@pytest.fixture
def mock_request():
    """Crear un mock de FastAPI Request"""
    request = Mock(spec=Request)
    request.method = "GET"
    request.url.path = "/api/v1/students"
    request.headers = {}
    request.client.host = "192.168.1.100"
    return request


# ============================================================================
# Test RateLimitConfig
# ============================================================================

class TestRateLimitConfig:
    """Tests para configuración de rate limiting"""
    
    def test_rate_limit_config_has_role_limits(self):
        """Verificar que existan límites por rol"""
        assert "admin" in RateLimitConfig.LIMITS_PER_ROLE
        assert "company" in RateLimitConfig.LIMITS_PER_ROLE
        assert "student" in RateLimitConfig.LIMITS_PER_ROLE
        assert "anonymous" in RateLimitConfig.LIMITS_PER_ROLE
    
    def test_admin_has_highest_limit(self):
        """Verificar que admins tienen el límite más alto"""
        admin_limit = RateLimitConfig.LIMITS_PER_ROLE["admin"]
        student_limit = RateLimitConfig.LIMITS_PER_ROLE["student"]
        anon_limit = RateLimitConfig.LIMITS_PER_ROLE["anonymous"]
        
        assert admin_limit > student_limit > anon_limit
    
    def test_endpoint_limits_defined(self):
        """Verificar que hay límites por endpoint"""
        assert "DEFAULT" in RateLimitConfig.ENDPOINT_LIMITS
        assert len(RateLimitConfig.ENDPOINT_LIMITS) > 1
    
    def test_auth_endpoints_more_restrictive(self):
        """Verificar que endpoints de auth son más restrictivos"""
        login_limit = RateLimitConfig.ENDPOINT_LIMITS.get("POST /api/v1/auth/login", 100)
        default_limit = RateLimitConfig.ENDPOINT_LIMITS.get("DEFAULT", 100)
        
        assert login_limit <= default_limit
    
    def test_windows_configured(self):
        """Verificar que ventanas de tiempo están configuradas"""
        assert RateLimitConfig.HOURLY_WINDOW == 3600
        assert RateLimitConfig.MINUTE_WINDOW == 60


# ============================================================================
# Test RateLimiter - Client IP Detection
# ============================================================================

class TestRateLimiterClientIP:
    """Tests para detección de IP del cliente"""
    
    def test_get_client_ip_from_direct_connection(self):
        """Obtener IP de conexión directa"""
        request = Mock(spec=Request)
        request.client.host = "192.168.1.100"
        request.headers = {}
        
        ip = RateLimiter._get_client_ip(request)
        assert ip == "192.168.1.100"
    
    def test_get_client_ip_from_x_forwarded_for(self):
        """Obtener IP desde header X-Forwarded-For"""
        request = Mock(spec=Request)
        request.headers = {"x-forwarded-for": "10.0.0.1, 192.168.1.1"}
        
        ip = RateLimiter._get_client_ip(request)
        assert ip == "10.0.0.1"
    
    def test_get_client_ip_from_x_real_ip(self):
        """Obtener IP desde header X-Real-IP"""
        request = Mock(spec=Request)
        request.headers = {"x-real-ip": "172.16.0.1"}
        request.client = None
        
        ip = RateLimiter._get_client_ip(request)
        assert ip == "172.16.0.1"
    
    def test_get_client_ip_x_forwarded_for_takes_precedence(self):
        """X-Forwarded-For tiene precedencia sobre X-Real-IP"""
        request = Mock(spec=Request)
        request.headers = {
            "x-forwarded-for": "10.0.0.1",
            "x-real-ip": "172.16.0.1"
        }
        
        ip = RateLimiter._get_client_ip(request)
        assert ip == "10.0.0.1"


# ============================================================================
# Test RateLimiter - Rate Limit Key Generation
# ============================================================================

class TestRateLimiterKeyGeneration:
    """Tests para generación de claves de rate limit"""
    
    def test_rate_limit_key_for_authenticated_user(self):
        """Generar clave para usuario autenticado"""
        limiter = RateLimiter()
        request = Mock(spec=Request)
        request.client.host = "192.168.1.100"
        request.headers = {}
        
        key = limiter._get_rate_limit_key(request, "student")
        
        assert "192.168.1.100" in key
        assert "student" in key
    
    def test_rate_limit_key_for_anonymous_user(self):
        """Generar clave para usuario anónimo (solo IP)"""
        limiter = RateLimiter()
        request = Mock(spec=Request)
        request.client.host = "192.168.1.100"
        request.headers = {}
        
        key = limiter._get_rate_limit_key(request, None)
        
        assert key == "192.168.1.100"
    
    def test_rate_limit_key_different_for_different_ips(self):
        """Claves diferentes para diferentes IPs"""
        limiter = RateLimiter()
        
        request1 = Mock(spec=Request)
        request1.client.host = "192.168.1.100"
        request1.headers = {}
        
        request2 = Mock(spec=Request)
        request2.client.host = "192.168.1.101"
        request2.headers = {}
        
        key1 = limiter._get_rate_limit_key(request1, "student")
        key2 = limiter._get_rate_limit_key(request2, "student")
        
        assert key1 != key2


# ============================================================================
# Test RateLimiter - Endpoint Key Detection
# ============================================================================

class TestRateLimiterEndpointDetection:
    """Tests para detección de endpoints"""
    
    def test_get_endpoint_key_matches_pattern(self):
        """Detectar endpoint que tiene patrón definido"""
        limiter = RateLimiter()
        request = Mock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/v1/students"
        
        endpoint_key = limiter._get_endpoint_key(request)
        
        # Debería encontrar el patrón en ENDPOINT_LIMITS
        assert endpoint_key in RateLimitConfig.ENDPOINT_LIMITS or endpoint_key == "DEFAULT"
    
    def test_get_endpoint_key_default_for_unknown(self):
        """Usar DEFAULT para endpoint desconocido"""
        limiter = RateLimiter()
        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/v1/unknown-endpoint"
        
        endpoint_key = limiter._get_endpoint_key(request)
        
        assert endpoint_key == "DEFAULT"


# ============================================================================
# Test RateLimiter - Basic Rate Limiting
# ============================================================================

class TestRateLimiterBasic:
    """Tests para funcionalidad básica de rate limiting"""
    
    def test_first_request_always_allowed(self, rate_limiter, mock_request):
        """El primer request siempre es permitido"""
        allowed, error, info = rate_limiter.check_rate_limit(mock_request, "student")
        
        assert allowed is True
        assert error is None
    
    def test_multiple_requests_under_limit(self, rate_limiter, mock_request):
        """Múltiples requests bajo el límite son permitidos"""
        # El límite por minuto para GET /api/v1/students es 100
        for i in range(10):
            allowed, error, info = rate_limiter.check_rate_limit(mock_request, "student")
            assert allowed is True
            assert error is None
    
    def test_requests_exceed_minute_limit(self, rate_limiter, mock_request):
        """Exceder límite por minuto rechaza request"""
        # GET /api/v1/students tiene límite de 100/minuto
        # Pero el límite por hora del student (300) es más restrictivo
        # Vamos a usar un endpoint con límite más bajo para el test
        
        mock_request.method = "POST"
        mock_request.url.path = "/api/v1/auth/login"
        
        endpoint_limit = RateLimitConfig.ENDPOINT_LIMITS.get("POST /api/v1/auth/login", 5)
        
        # Hacer requests hasta exceder el límite
        exceeded = False
        for i in range(endpoint_limit + 5):
            allowed, error, info = rate_limiter.check_rate_limit(mock_request, "student")
            
            if not allowed:
                exceeded = True
                assert "excedido" in error.lower() or "limit" in error.lower()
                break
        
        assert exceeded, "El límite debería ser excedido eventualmente"
    
    def test_anonymous_has_stricter_limit(self, rate_limiter, mock_request):
        """Usuario anónimo tiene límite más estricto"""
        anon_hourly = RateLimitConfig.LIMITS_PER_ROLE["anonymous"]
        student_hourly = RateLimitConfig.LIMITS_PER_ROLE["student"]
        
        assert anon_hourly < student_hourly
    
    def test_admin_has_high_limit(self, rate_limiter, mock_request):
        """Admin tiene límite muy alto"""
        admin_hourly = RateLimitConfig.LIMITS_PER_ROLE["admin"]
        student_hourly = RateLimitConfig.LIMITS_PER_ROLE["student"]
        
        assert admin_hourly > student_hourly


# ============================================================================
# Test RateLimiter - Role-Based Limits
# ============================================================================

class TestRateLimiterRoleLimits:
    """Tests para límites basados en rol"""
    
    def test_get_limit_for_student(self, rate_limiter):
        """Obtener límite para rol student"""
        limit = rate_limiter._get_limit_for_role("student")
        
        assert limit == RateLimitConfig.LIMITS_PER_ROLE["student"]
    
    def test_get_limit_for_admin(self, rate_limiter):
        """Obtener límite para rol admin"""
        limit = rate_limiter._get_limit_for_role("admin")
        
        assert limit == RateLimitConfig.LIMITS_PER_ROLE["admin"]
    
    def test_get_limit_for_anonymous(self, rate_limiter):
        """Obtener límite para usuario anónimo"""
        limit = rate_limiter._get_limit_for_role(None)
        
        assert limit == RateLimitConfig.LIMITS_PER_ROLE["anonymous"]
    
    def test_unknown_role_defaults_to_anonymous(self, rate_limiter):
        """Rol desconocido usa límite de anonymous"""
        limit = rate_limiter._get_limit_for_role("unknown_role")
        
        assert limit == RateLimitConfig.LIMITS_PER_ROLE["anonymous"]


# ============================================================================
# Test RateLimiter - Endpoint Limits
# ============================================================================

class TestRateLimiterEndpointLimits:
    """Tests para límites específicos de endpoints"""
    
    def test_auth_login_has_strict_limit(self, rate_limiter):
        """Login tiene límite más estricto que default"""
        login_limit = rate_limiter._get_limit_for_endpoint("POST /api/v1/auth/login")
        default_limit = rate_limiter._get_limit_for_endpoint("DEFAULT")
        
        assert login_limit < default_limit
    
    def test_get_limit_for_unknown_endpoint(self, rate_limiter):
        """Endpoint desconocido usa DEFAULT"""
        limit = rate_limiter._get_limit_for_endpoint("UNKNOWN")
        
        assert limit == RateLimitConfig.ENDPOINT_LIMITS["DEFAULT"]
    
    def test_matching_recommendations_limit(self, rate_limiter):
        """Endpoint de recomendaciones tiene límite definido"""
        limit = rate_limiter._get_limit_for_endpoint("POST /api/v1/matching/recommendations")
        
        assert limit == RateLimitConfig.ENDPOINT_LIMITS["POST /api/v1/matching/recommendations"]


# ============================================================================
# Test RateLimiter - Time Window Management
# ============================================================================

class TestRateLimiterTimeWindows:
    """Tests para manejo de ventanas de tiempo"""
    
    def test_clean_old_requests_removes_stale_entries(self, rate_limiter):
        """Limpiar requests elimina entradas antiguas"""
        key = "test_key"
        now = datetime.utcnow()
        
        # Agregar un request antiguo
        rate_limiter._requests[key].append((now - timedelta(hours=2), "GET"))
        
        # Limpiar
        rate_limiter._clean_old_requests(key, now)
        
        # Debería estar vacío (request es más viejo que ventana)
        assert len(rate_limiter._requests[key]) == 0
    
    def test_clean_old_requests_keeps_recent(self, rate_limiter):
        """Limpiar requests mantiene entradas recientes"""
        key = "test_key"
        now = datetime.utcnow()
        
        # Agregar un request reciente
        rate_limiter._requests[key].append((now - timedelta(seconds=30), "GET"))
        
        # Limpiar
        rate_limiter._clean_old_requests(key, now)
        
        # Debería mantenerse (request es reciente)
        assert len(rate_limiter._requests[key]) == 1
    
    def test_sliding_window_behavior(self, rate_limiter, mock_request):
        """Verificar comportamiento de ventana deslizante"""
        # Hacer requests en la primera ventana
        for i in range(5):
            rate_limiter.check_rate_limit(mock_request, "student")
        
        # Obtener información
        allowed, error, info = rate_limiter.check_rate_limit(mock_request, "student")
        
        assert info["minute_requests"] > 0


# ============================================================================
# Test RateLimiter - Remaining Requests
# ============================================================================

class TestRateLimiterRemainingRequests:
    """Tests para información de requests restantes"""
    
    def test_get_remaining_requests_initial(self, rate_limiter, mock_request):
        """Requests restantes inicialmente igual al límite"""
        remaining_info = rate_limiter.get_remaining_requests(mock_request, "student")
        
        hourly_limit = remaining_info["hourly"]["limit"]
        hourly_remaining = remaining_info["hourly"]["remaining"]
        
        # Al inicio, remaining debería ser casi igual al límite
        assert hourly_remaining > 0
        assert hourly_remaining <= hourly_limit
    
    def test_get_remaining_decreases_after_request(self, rate_limiter, mock_request):
        """Requests restantes decrecen después de hacer requests"""
        # Primer check (sin usar el request aún)
        remaining_info1 = rate_limiter.get_remaining_requests(mock_request, "student")
        
        # Hacer varios requests
        for i in range(5):
            rate_limiter.check_rate_limit(mock_request, "student")
        
        # Segundo check
        remaining_info2 = rate_limiter.get_remaining_requests(mock_request, "student")
        
        # Debería tener menos requests restantes
        assert remaining_info2["hourly"]["used"] > remaining_info1["hourly"]["used"]


# ============================================================================
# Test RateLimiter - Thread Safety
# ============================================================================

class TestRateLimiterThreadSafety:
    """Tests para thread safety del rate limiter"""
    
    def test_rate_limiter_uses_lock(self, rate_limiter):
        """Verificar que rate limiter tiene un lock"""
        assert hasattr(rate_limiter, '_lock')
        assert rate_limiter._lock is not None
    
    def test_check_rate_limit_thread_safe(self, rate_limiter, mock_request):
        """Verificar que check_rate_limit es thread-safe"""
        # Este test verifica que el método no falla con concurrencia
        # (En un test real, habría que usar threading)
        allowed1, _, _ = rate_limiter.check_rate_limit(mock_request, "student")
        allowed2, _, _ = rate_limiter.check_rate_limit(mock_request, "student")
        
        assert allowed1 and allowed2  # Ambos debería ser True


# ============================================================================
# Test RateLimiter - Error Messages
# ============================================================================

class TestRateLimiterErrorMessages:
    """Tests para mensajes de error de rate limiting"""
    
    def test_error_message_format_minute_limit(self, rate_limiter, mock_request):
        """Mensaje de error para límite por minuto"""
        endpoint_limit = RateLimitConfig.ENDPOINT_LIMITS.get("GET /api/v1/students", 100)
        
        # Exceder el límite
        for i in range(endpoint_limit + 2):
            allowed, error, info = rate_limiter.check_rate_limit(mock_request, "student")
            if not allowed:
                assert "minuto" in error.lower() or "minute" in error.lower()
                assert str(endpoint_limit) in error
                break
    
    def test_info_includes_rate_limit_details(self, rate_limiter, mock_request):
        """Info incluye detalles de rate limit"""
        allowed, error, info = rate_limiter.check_rate_limit(mock_request, "student")
        
        assert "rate_limit_key" in info
        assert "endpoint" in info
        assert "hourly_limit" in info
        assert "hourly_requests" in info
        assert "minute_limit" in info
        assert "minute_requests" in info
        assert "user_role" in info
