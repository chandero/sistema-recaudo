from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import init_db
from app.api.v1.api import api_router
from app.core.logging import logger
from app.models.workflow import WorkflowState

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema de Seguimiento y Control de Cobro de Cartera"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Manejar excepciones de validación"""
    logger.warning(f"Validation error: {exc.errors()}, body: {getattr(request, 'body', None)}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
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
    
    # Seed initial workflow states (solo para demo, en producción usar migraciones)
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
            admin_user = User(
                username="admin",
                email="admin@sistema-cobro.com",
                full_name="Administrador del Sistema",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.PLATFORM_ADMIN,
                is_active=True,
                is_platform_admin=True,
                tenant_id=tenant.id
            )
            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)
            logger.info(f"Created default admin user: {admin_user.id}")
            
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
