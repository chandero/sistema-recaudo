from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging.logger import logger
from app.core.logging.config import setup_logging
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import engine
from app.core.database import init_db
from sqlmodel import Session, select
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.core.security import get_password_hash

def create_default_tenant_and_user():
    """Crear tenant y usuario por defecto si no existen"""
    with Session(engine) as session:
        # Verificar si existe el tenant demo
        demo_tenant = session.exec(select(Tenant).where(Tenant.code == "demo")).first()
        if not demo_tenant:
            demo_tenant = Tenant(
                name="Demo Tenant",
                code="demo",
                is_active=True
            )
            session.add(demo_tenant)
            session.commit()
            session.refresh(demo_tenant)
            logger.info(f"Created default demo tenant: {demo_tenant.id}")
        else:
            logger.info(f"Demo tenant already exists: {demo_tenant.id}")
        
        # Verificar si existe el usuario admin
        admin_user = session.exec(select(User).where(User.username == "admin")).first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@sistema-cobro.com",
                full_name="Administrador del Sistema",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.PLATFORM_ADMIN,
                is_active=True,
                is_platform_admin=True,
                tenant_id=demo_tenant.id
            )
            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)
            logger.info(f"Created default admin user: {admin_user.id}")
        else:
            logger.info(f"Admin user already exists: {admin_user.id}")
        
        # Inicializar estados de workflow para el tenant
        from app.db.seed_workflow import seed_workflow
        stats = seed_workflow(session, demo_tenant.id)
        logger.info(f"Workflow seed completed for tenant {demo_tenant.id}: {stats}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código de inicialización
    logger.info("Iniciando la aplicación...")
    setup_logging()
    init_db()  # Inicializar la base de datos
    
    # Crear tenant y usuario por defecto
    create_default_tenant_and_user()
    
    yield
    # Código de apagado
    logger.info("Apagando la aplicación...")

def create_app():
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        lifespan=lifespan
    )

    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        # expose_headers=["Access-Control-Allow-Origin"]
    )
    
    # Incluir rutas API
    app.include_router(api_router, prefix="/api/v1")
    
    return app

# Para ejecución directa
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:create_app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        factory=True
    )