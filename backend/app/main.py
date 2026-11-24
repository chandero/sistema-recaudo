from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import init_db
from app.api.v1.api import api_router
from app.core.logging import logger
from app.models.workflow import WorkflowState
from app.core.security.http_security import HttpSecurityMiddleware

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema de Seguimiento y Control de Cobro de Cartera",
    # La documentación solo se expone cuando se pide explícitamente (EXPOSE_API_DOCS).
    # En producción evita que el contrato completo del API sea público.
    docs_url="/docs" if settings.EXPOSE_API_DOCS else None,
    redoc_url="/redoc" if settings.EXPOSE_API_DOCS else None,
    openapi_url="/openapi.json" if settings.EXPOSE_API_DOCS else None,
)

# Seguridad HTTP (cabeceras de seguridad en todas las respuestas)
app.add_middleware(HttpSecurityMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Total-Count",
        # Conteo de documentos y envíos de correspondencia (Auto de Archivo,
        # Constancia Secretarial e impresión por rango).
        "X-Document-Count",
        "X-File-Count",
        "X-Email-Sent",
        "X-Email-Failed",
    ],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Manejar excepciones de validación"""
    # Sanitize errors: convert bytes and other non-serializable objects to strings
    safe_errors = []
    for error in exc.errors():
        safe_error = {}
        for key, value in error.items():
            if isinstance(value, bytes):
                safe_error[key] = value.decode("utf-8", errors="replace")
            else:
                safe_error[key] = str(value) if not isinstance(value, (str, int, float, bool, list, dict, type(None))) else value
        safe_errors.append(safe_error)
    logger.warning(f"Validation error: {safe_errors}")
    return JSONResponse(
        status_code=422,
        content={"detail": safe_errors}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Manejar excepciones generales"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


@app.on_event("startup")
async def startup_event():
    # Initialize database tables
    init_db()
    logger.info("Database initialized")
    if not settings.EXPOSE_API_DOCS:
        logger.info("Documentación del API deshabilitada (EXPOSE_API_DOCS=false)")

    # Seed initial workflow states (solo para demo, en producción usar migraciones)
    if not settings.SEED_DEMO_DATA:
        logger.info("Semilla de datos de demostración deshabilitada (SEED_DEMO_DATA=false)")
        return

    try:
        from sqlmodel import Session, select
        from app.core.database import get_session
        from app.db.seed_workflow import seed_workflow, get_initial_workflow_states
        
        session = next(get_session())

        # Crear un tenant por defecto para demo
        from app.models.tenant import Tenant
        tenant = session.exec(
            select(Tenant).where(Tenant.code == "demo")
        ).first()
        
        if not tenant:
            tenant = Tenant(
                name="Demo Tenant",
                code="demo",
                is_active=True
            )
            session.add(tenant)
            session.commit()
            session.refresh(tenant)
            logger.info(f"Created default tenant: {tenant.id}")
        
        # Verificar si ya hay estados
        statement = select(WorkflowState)
        existing_states = session.exec(statement).all()
        
        if not existing_states:
            # Seed workflow states
            stats = seed_workflow(session, tenant.id)
            logger.info(f"Workflow seeded: {stats}")

        # Crear usuario admin por defecto
        from app.models.user import User, UserRole
        from app.core.security import get_password_hash
        
        admin_user = session.exec(
            select(User).where(User.username == "admin")
        ).first()
        
        if not admin_user:
            # Sin una contraseña explícita no se crea ninguna cuenta: una clave por
            # defecto conocida (admin123) en un PLATFORM_ADMIN es accesible desde internet.
            if not settings.BOOTSTRAP_ADMIN_PASSWORD:
                logger.warning(
                    "No existe usuario admin y BOOTSTRAP_ADMIN_PASSWORD no está definida: "
                    "se omite la creación de la cuenta inicial"
                )
                return

            admin_user = User(
                username="admin",
                email="admin@sistema-cobro.com",
                full_name="Administrador del Sistema",
                hashed_password=get_password_hash(settings.BOOTSTRAP_ADMIN_PASSWORD),
                role=UserRole.PLATFORM_ADMIN,
                is_active=True,
                is_platform_admin=True,
                tenant_id=tenant.id
            )
            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)
            logger.warning(
                f"Creado usuario admin inicial: {admin_user.id} "
                "(defina su contraseña definitiva y retire BOOTSTRAP_ADMIN_PASSWORD)"
            )
            
    except Exception as e:
        logger.warning(f"Could not seed workflow: {str(e)}")


@app.get("/")
async def root():
    return {
        "message": "Sistema de Cobro de Cartera API",
        "version": settings.APP_VERSION
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
