from sqlalchemy import text
from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings
import os

# Detectar tipo de base de datos
DATABASE_URL = settings.DATABASE_URL
is_postgres = DATABASE_URL.startswith("postgresql")

if is_postgres:
    engine = create_engine(
        DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
else:
    # SQLite fallback para desarrollo local sin Docker
    _sqlite3_available = True
    try:
        import _sqlite3
    except ImportError:
        _sqlite3_available = False

    if _sqlite3_available:
        engine = create_engine(
            DATABASE_URL,
            echo=settings.DEBUG,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
    else:
        import aiosqlite
        from sqlalchemy.ext.asyncio import create_async_engine
        engine = create_async_engine(
            DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://"),
            echo=settings.DEBUG,
            pool_pre_ping=True,
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
    from app.models.user import User, UserTenant
    from app.models.tenant import Tenant
    from app.models.client import Client
    from app.models.obligation import Obligation
    from app.models.process import CobroProcess
    from app.models.document import DocumentTemplate, GeneratedDocument
    from app.models.user_audit import UserAuditLog
    from app.models.user_invitation import UserInvitation
    from app.models.process_config import TenantProcessConfig
    from app.models.process_note import ProcessNote
    from app.models.payment_agreement import PaymentAgreement, AgreementInstallment
    from app.models.notification import Notification

    # Crear todas las tablas
    SQLModel.metadata.create_all(engine)
