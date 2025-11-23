"""
Configuración global de fixtures para tests
Incluye mocks para autenticación, base de datos, y cliente HTTP
"""
import pytest
from typing import Generator
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_session
from app.schemas import UserContext
from app.middleware.auth import AuthService, Role


# ============================================================================
# BASE DE DATOS DE PRUEBA
# ============================================================================

@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    """
    Crea una sesión de base de datos en memoria para tests
    Aislado, rápido, sin efectos secundarios
    """
    engine = create_engine(
        "sqlite://",  # In-memory database
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Crear todas las tablas
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session


# ============================================================================
# MOCKS DE USUARIOS
# ============================================================================

@pytest.fixture(name="admin_user")
def admin_user_fixture() -> UserContext:
    """Mock de usuario admin autenticado"""
    return UserContext(
        role=Role.ADMIN,
        user_id=1,
        email="admin@moirai.com",
        permissions=["read:all", "write:all", "admin:all"]
    )


@pytest.fixture(name="company_user")
def company_user_fixture() -> UserContext:
    """Mock de usuario company autenticado"""
    return UserContext(
        role=Role.COMPANY,
        user_id=2,
        email="company@example.com",
        permissions=["read:students", "read:jobs", "write:jobs"]
    )


@pytest.fixture(name="student_user")
def student_user_fixture() -> UserContext:
    """Mock de usuario student autenticado"""
    return UserContext(
        role=Role.STUDENT,
        user_id=3,
        email="student@unrc.edu.mx",
        permissions=["read:own", "write:own", "read:jobs"]
    )


@pytest.fixture(name="anonymous_user")
def anonymous_user_fixture() -> UserContext:
    """Mock de usuario anónimo"""
    return UserContext(
        role=Role.ANONYMOUS,
        user_id=None,
        email=None,
        permissions=[]
    )


# ============================================================================
# MOCKS DE AUTENTICACIÓN
# ============================================================================

@pytest.fixture(name="mock_get_current_user_admin")
def mock_get_current_user_admin_fixture(admin_user: UserContext):
    """Mock de AuthService.get_current_user para admin"""
    async def _mock_get_current_user():
        return admin_user
    
    return _mock_get_current_user


@pytest.fixture(name="mock_get_current_user_company")
def mock_get_current_user_company_fixture(company_user: UserContext):
    """Mock de AuthService.get_current_user para company"""
    async def _mock_get_current_user():
        return company_user
    
    return _mock_get_current_user


@pytest.fixture(name="mock_get_current_user_student")
def mock_get_current_user_student_fixture(student_user: UserContext):
    """Mock de AuthService.get_current_user para student"""
    async def _mock_get_current_user():
        return student_user
    
    return _mock_get_current_user


@pytest.fixture(name="mock_get_current_user_anonymous")
def mock_get_current_user_anonymous_fixture(anonymous_user: UserContext):
    """Mock de AuthService.get_current_user para anonymous"""
    async def _mock_get_current_user():
        return anonymous_user
    
    return _mock_get_current_user


# ============================================================================
# CLIENTS CON AUTENTICACIÓN (RESET-SAFE VERSION)
# Cada cliente configura SUS propios overrides en el momento de uso
# ============================================================================

@pytest.fixture(name="client_with_admin")
def client_with_admin_fixture(session: Session, mock_get_current_user_admin, cleanup_overrides) -> TestClient:
    """Cliente con autenticación de admin
    
    IMPORTANTE: Cada llamada a este fixture asegura que los overrides
    sean correctos ANTES de usar el cliente
    """
    app.dependency_overrides.clear()  # Clean slate
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[AuthService.get_current_user] = mock_get_current_user_admin
    
    client = TestClient(app)
    yield client


@pytest.fixture(name="client_with_company")
def client_with_company_fixture(session: Session, mock_get_current_user_company, cleanup_overrides) -> TestClient:
    """Cliente con autenticación de company"""
    app.dependency_overrides.clear()  # Clean slate
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[AuthService.get_current_user] = mock_get_current_user_company
    
    client = TestClient(app)
    yield client


@pytest.fixture(name="client_with_student")
def client_with_student_fixture(session: Session, mock_get_current_user_student, cleanup_overrides) -> TestClient:
    """Cliente con autenticación de student"""
    app.dependency_overrides.clear()  # Clean slate
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[AuthService.get_current_user] = mock_get_current_user_student
    
    client = TestClient(app)
    yield client


@pytest.fixture(name="client_with_anonymous")
def client_with_anonymous_fixture(session: Session, mock_get_current_user_anonymous, cleanup_overrides) -> TestClient:
    """Cliente con autenticación de anonymous"""
    app.dependency_overrides.clear()  # Clean slate
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[AuthService.get_current_user] = mock_get_current_user_anonymous
    
    client = TestClient(app)
    yield client


# ============================================================================
# AUTOCLEANUP GLOBAL (Se ejecuta después de cada test)
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_overrides():
    """Limpia los dependency overrides después de cada test
    
    autouse=True: Se ejecuta automáticamente
    yield: Permite que el test corra entre setup y cleanup
    """
    yield
    # Cleanup después del test
    app.dependency_overrides.clear()
