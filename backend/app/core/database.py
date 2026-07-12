from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True
)


def get_session() -> Session:
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def init_db():
    # Importar todos los modelos para que SQLModel los registre
    from app.models.user import User
    from app.models.tenant import Tenant
    from app.models.client import Client
    from app.models.obligation import Obligation
    from app.models.process import CobroProcess
    from app.models.document import DocumentTemplate, GeneratedDocument
    
    # Crear todas las tablas
    SQLModel.metadata.create_all(engine)
