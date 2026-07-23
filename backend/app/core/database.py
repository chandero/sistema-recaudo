from sqlalchemy import text
from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings

# Detectar si _sqlite3 está disponible
_sqlite3_available = True
try:
    import _sqlite3
except ImportError:
    _sqlite3_available = False

if _sqlite3_available:
    # Usar sqlite3 estándar
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True
    )
else:
    # Usar aiosqlite para evitar dependencia de _sqlite3
    import aiosqlite
    from sqlalchemy.ext.asyncio import create_async_engine
    
    # Crear engine asíncrono con aiosqlite
    engine = create_async_engine(
        settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://"),
        echo=settings.DEBUG,
        pool_pre_ping=True
    )


def get_session() -> Session:
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


get_db = get_session


def init_db():
    # Importar todos los modelos para que SQLModel los registre
    from app.models.user import User
    from app.models.tenant import Tenant
    from app.models.client import Client
    from app.models.obligation import Obligation
    from app.models.process import CobroProcess
    from app.models.document import DocumentTemplate, GeneratedDocument
    from app.models.user_audit import UserAuditLog
    from app.models.user_invitation import UserInvitation
    
    # Crear todas las tablas
    SQLModel.metadata.create_all(engine)
