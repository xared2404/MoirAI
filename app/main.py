# Copyright 2025 HenrySpark369 y MoirAI Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Aplicación principal de MoirAI
FastAPI app con todos los endpoints y configuración
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.core.database import create_db_and_tables, get_session
from app.core.admin_init import init_default_admin, verify_admin_access_configured
from app.api.endpoints import students, auth
from app.schemas import ErrorResponse


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    **MoirAI - Plataforma de Matching Laboral UNRC**
    
    API RESTful para conectar estudiantes de la Universidad Nacional Rosario Castellanos 
    con oportunidades laborales mediante análisis inteligente de perfiles y matchmaking automatizado.
    
    ## Características principales:
    
    * **Análisis NLP de Currículums**: Extracción automática de habilidades técnicas, blandas y proyectos
    * **Matchmaking Inteligente**: Algoritmos de compatibilidad entre perfiles y vacantes
    * **Web Scraping OCC.com.mx**: Sistema completo de scraping y seguimiento de empleos ✅ IMPLEMENTADO
    * **Gestión de Aplicaciones**: Seguimiento de aplicaciones con estados y estadísticas
    * **Sistema de Alertas**: Notificaciones automáticas de nuevos empleos relevantes
    * **Gestión de Roles**: Acceso diferenciado para estudiantes, empresas y administradores
    * **Cumplimiento LFPDPPP**: Protección de datos y auditoría integrada
    * **Arquitectura Escalable**: FastAPI + PostgreSQL + modelos de ML

    ## Funcionalidades del Sistema de Scraping:
    
    * **Búsqueda Inteligente**: Filtros avanzados por ubicación, salario, modalidad de trabajo
    * **Aplicaciones Tracking**: Estados detallados (aplicado, entrevista, rechazado, aceptado)
    * **Alertas Personalizadas**: Notificaciones diarias/semanales por palabras clave
    * **Analytics**: Empleos trending, estadísticas personales, análisis de mercado
    * **Rate Limiting**: Respeta límites de OCC.com.mx con delays inteligentes

    ## Roles de Usuario:
    
    * **Estudiantes**: Gestión de perfil, búsqueda de empleos, seguimiento de aplicaciones
    * **Empresas**: Búsqueda y filtrado de candidatos, publicación de vacantes
    * **Administradores**: KPIs, gestión de usuarios, auditoría del sistema, procesamiento de alertas
    """,
    contact={
        "name": "UNRC - Ciencia de Datos para Negocios",
        "url": "https://www.ing.unrc.edu.mx/",
        "email": "contacto@ing.unrc.edu.mx"
    },
    license_info={
        "name": "Apache License, Version 2.0",
        "url": "https://opensource.org/license/apache-2-0"
    }
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Configurar archivos estáticos
static_path = Path(__file__).parent / "frontend" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# Event handlers
@app.on_event("startup")
async def startup_event():
    """Inicializar aplicación"""
    # Crear tablas de base de datos (ASYNC)
    await create_db_and_tables()
    
    # Inicializar admin por defecto desde .env (si está habilitado) - ASYNC
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.core.database import async_engine
        
        async with AsyncSession(async_engine) as session:
            admin_id = await init_default_admin(session)
            if admin_id:
                print(f"✅ Admin inicializado: ID {admin_id}")
    except Exception as e:
        print(f"⚠️  No se pudo inicializar admin: {e}")
    
    # Verificar que hay acceso admin disponible
    verify_admin_access_configured()
    
    print(f"🚀 {settings.PROJECT_NAME} iniciado correctamente")
    print(f"📊 Base de datos: {settings.DATABASE_URL}")
    print(f"🔐 Audit logging: {'✅' if settings.ENABLE_AUDIT_LOGGING else '❌'}")
    print(f"🌐 Landing page disponible en: http://localhost:8000/")

# Configurar archivos estáticos
static_path = Path(__file__).parent / "frontend" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.on_event("shutdown")
async def shutdown_event():
    """Limpiar recursos al cerrar"""
    print(f"🛑 {settings.PROJECT_NAME} detenido")


# Manejadores de errores globales
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Manejar errores de validación de Pydantic"""
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Error de validación en los datos enviados",
            details={
                "errors": exc.errors(),
                "body": exc.body if hasattr(exc, 'body') else None
            }
        ).dict()
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Manejar errores HTTP generales"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code="HTTP_ERROR",
            message=str(exc.detail),
            details={
                "status_code": exc.status_code,
                "path": str(request.url.path)
            }
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Manejar errores generales no capturados"""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_code="INTERNAL_ERROR",
            message="Error interno del servidor",
            details={
                "type": type(exc).__name__,
                "path": str(request.url.path)
            }
        ).dict()
    )


# Endpoints principales
@app.get("/", tags=["frontend"], include_in_schema=False)
@app.get("/landing", tags=["frontend"])
async def landing_page():
    """Servir la página de inicio (landing page)"""
    template_path = Path(__file__).parent / "frontend" / "templates" / "index.html"
    if template_path.exists():
        return FileResponse(str(template_path), media_type="text/html")
    # Si no existe el archivo, mostrar mensaje JSON
    return {
        "message": f"Bienvenido a {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "docs_url": "/docs",
        "openapi_url": "/openapi.json"
    }


@app.get("/admin/dashboard", tags=["admin"], include_in_schema=False)
@app.get("/admin", tags=["admin"], include_in_schema=False)
async def admin_dashboard():
    """Servir el dashboard administrativo"""
    template_path = Path(__file__).parent / "frontend" / "templates" / "admin" / "dashboard.html"
    if template_path.exists():
        return FileResponse(str(template_path), media_type="text/html")
    return {
        "message": "Admin dashboard not found",
        "status": "error"
    }


# Dashboard routes para roles autenticados
@app.get("/dashboard", tags=["frontend"], include_in_schema=False)
async def dashboard_page():
    """Servir el dashboard del usuario (estudiante/empresa)"""
    template_path = Path(__file__).parent / "frontend" / "templates" / "dashboard.html"
    if template_path.exists():
        return FileResponse(str(template_path), media_type="text/html")
    return {"message": "Dashboard no encontrado", "status": "error"}


@app.get("/profile", tags=["frontend"], include_in_schema=False)
async def profile_page():
    """Servir la página de perfil del usuario"""
    template_path = Path(__file__).parent / "frontend" / "templates" / "profile.html"
    if template_path.exists():
        return FileResponse(str(template_path), media_type="text/html")
    return {"message": "Página de perfil no encontrada", "status": "error"}


@app.get("/buscar-candidatos", tags=["frontend"], include_in_schema=False)
async def buscar_candidatos_page():
    """Servir la página de búsqueda de candidatos (para empresas)"""
    template_path = Path(__file__).parent / "frontend" / "templates" / "buscar-candidatos.html"
    if template_path.exists():
        return FileResponse(str(template_path), media_type="text/html")
    return {"message": "Página de búsqueda de candidatos no encontrada", "status": "error"}


@app.get("/mis-vacantes", tags=["frontend"], include_in_schema=False)
@app.get("/company/mis-vacantes", tags=["frontend"], include_in_schema=False)
async def mis_vacantes_page():
    """Servir la página de mis vacantes (para empresas)"""
    template_path = Path(__file__).parent / "frontend" / "templates" / "company" / "mis-vacantes.html"
    if template_path.exists():
        return FileResponse(str(template_path), media_type="text/html")
    return {"message": "Página de mis vacantes no encontrada", "status": "error"}


@app.get("/admin/users", tags=["frontend"], include_in_schema=False)
async def admin_users_page():
    """Servir la página de gestión de usuarios (para administradores)"""
    template_path = Path(__file__).parent / "frontend" / "templates" / "admin" / "users.html"
    if template_path.exists():
        return FileResponse(str(template_path), media_type="text/html")
    return {"message": "Página de gestión de usuarios no encontrada", "status": "error"}


@app.get("/admin/analytics", tags=["frontend"], include_in_schema=False)
async def admin_analytics_page():
    """Servir la página de analítica (para administradores)"""
    template_path = Path(__file__).parent / "frontend" / "templates" / "admin" / "analytics.html"
    if template_path.exists():
        return FileResponse(str(template_path), media_type="text/html")
    return {"message": "Página de analítica no encontrada", "status": "error"}



@app.get("/applications", tags=["frontend"], include_in_schema=False)
async def applications_page():
    """Servir la página de aplicaciones (para estudiantes)"""
    template_path = Path(__file__).parent / "frontend" / "templates" / "applications.html"
    if template_path.exists():
        return FileResponse(str(template_path), media_type="text/html")
    return {"message": "Página de aplicaciones no encontrada", "status": "error"}


@app.get("/login", tags=["frontend"], include_in_schema=False)
async def login_page():
    """Servir la página de login"""
    template_path = Path(__file__).parent / "frontend" / "templates" / "login.html"
    if template_path.exists():
        return FileResponse(str(template_path), media_type="text/html")
    return {"message": "Página de login no encontrada", "status": "error"}


@app.get("/logout-test", tags=["testing"], include_in_schema=False)
async def logout_test_page():
    """Servir la página de testing de logout (E2E Testing)"""
    template_path = Path(__file__).parent / "frontend" / "templates" / "logout-test.html"
    if template_path.exists():
        return FileResponse(str(template_path), media_type="text/html")
    return {"message": "Página de logout test no encontrada", "status": "error"}


# Sub-sites Pages
@app.get("/oportunidades", tags=["listings"], include_in_schema=False)
async def oportunidades_page():
    """Servir la página de oportunidades (empleos)"""
    template_path = Path(__file__).parent / "frontend" / "templates" / "oportunidades.html"
    if template_path.exists():
        return FileResponse(str(template_path), media_type="text/html")
    return {"message": "Página de oportunidades no encontrada", "status": "error"}


@app.get("/empresas", tags=["listings"], include_in_schema=False)
async def empresas_page():
    """Servir la página de empresas"""
    template_path = Path(__file__).parent / "frontend" / "templates" / "empresas.html"
    if template_path.exists():
        return FileResponse(str(template_path), media_type="text/html")
    return {"message": "Página de empresas no encontrada", "status": "error"}


@app.get("/estudiantes", tags=["listings"], include_in_schema=False)
async def estudiantes_page():
    """Servir la página de estudiantes"""
    template_path = Path(__file__).parent / "frontend" / "templates" / "student" / "estudiantes.html"
    if template_path.exists():
        return FileResponse(str(template_path), media_type="text/html")
    return {"message": "Página de estudiantes no encontrada", "status": "error"}


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint para monitoreo"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION,
        "environment": "development" if settings.DATABASE_URL.startswith("sqlite") else "production"
    }


@app.get("/info", tags=["info"])
async def api_info():
    """Información detallada de la API"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": "Plataforma de matching laboral para estudiantes UNRC",
        "features": [
            "Análisis NLP de currículums",
            "Matchmaking inteligente",
            "Búsqueda multi-proveedor de trabajos",
            "Gestión de roles y permisos",
            "Auditoría y compliance LFPDPPP",
            "API RESTful escalable"
        ],
        "endpoints": {
            "students": "/api/v1/students - Gestión de estudiantes",
            "jobs": "/api/v1/jobs - Búsqueda de trabajos",
            "companies": "/api/v1/companies - Gestión de empresas", 
            "matching": "/api/v1/matching - Algoritmos de matchmaking",
            "admin": "/api/v1/admin - Panel administrativo"
        },
        "documentation": "/docs",
        "contact": "contacto@ing.unrc.edu.mx"
    }


@app.get("/compliance", tags=["compliance"])
async def compliance_info():
    """
    Información de cumplimiento y privacidad
    Transparencia según LFPDPPP y estándares ISO/IEC 27001
    """
    return {
        "privacy_by_design": True,
        "data_minimization": True,
        "pseudonymization": False,  # TODO: Implementar en producción
        "consent_required": settings.REQUIRE_CONSENT,
        "data_subject_rights": [
            "Acceso a datos personales",
            "Rectificación de datos incorrectos", 
            "Cancelación/eliminación de datos",
            "Oposición al tratamiento de datos"
        ],
        "retention_policy": f"Datos de estudiantes inactivos por {settings.DATA_RETENTION_DAYS} días son anonimizados",
        "audit_logging": settings.ENABLE_AUDIT_LOGGING,
        "encryption_at_rest": "Configurar cifrado a nivel de base de datos en producción",
        "encryption_in_transit": "TLS 1.3 requerido en producción",
        "data_protection_standards": [
            "Ley Federal de Protección de Datos Personales en Posesión de Particulares (LFPDPPP)",
            "ISO/IEC 27001 - Gestión de Seguridad de la Información"
        ],
        "contact_dpo": "dpo@unrc.edu.mx",
        "last_updated": "2025-01-15",
        "notice": "Esta información es de referencia. Consulte documentos legales oficiales para términos vinculantes."
    }


# Incluir routers de endpoints
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(students.router, prefix=settings.API_V1_STR)

# Sistema de scraping de empleos OCC.com.mx - ✅ IMPLEMENTADO
from app.api.endpoints import job_scraping
app.include_router(job_scraping.router, prefix=settings.API_V1_STR)

# Gestión de empresas - ✅ IMPLEMENTADO
from app.api.endpoints import companies
app.include_router(companies.router, prefix=settings.API_V1_STR)

# Module 2: Encryption Integration - Job Postings con Encriptación - ✅ IMPLEMENTADO
# Include jobs router (con autocomplete consolidado de suggestions)
from app.api.endpoints import jobs
app.include_router(jobs.router, prefix=settings.API_V1_STR)

# NOTE: suggestions.py ha sido consolidado en jobs.py (autocomplete endpoints)
# NOTE: matching.py ha sido consolidado en students.py (búsqueda por skills)

# ✅ HABILITADOS: Routers de matching y admin para acceso a todos los endpoints
from app.api.endpoints import matching
app.include_router(matching.router, prefix=settings.API_V1_STR)

from app.api.endpoints import admin
app.include_router(admin.router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    # Ejecutar aplicación directamente
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
