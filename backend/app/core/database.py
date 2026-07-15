from sqlalchemy import text
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


get_db = get_session


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

    # SQLite no aplica alteraciones de modelos sobre tablas existentes con create_all.
    # Mantener compatibilidad con bases creadas antes de agregar atributos adicionales.
    if engine.url.get_backend_name() == "sqlite":
        with engine.begin() as connection:
            client_columns = {
                row[1]
                for row in connection.execute(text("PRAGMA table_info(clients)"))
            }
            if "additional_attributes" not in client_columns:
                connection.execute(
                    text("ALTER TABLE clients ADD COLUMN additional_attributes JSON DEFAULT '{}'")
                )

            obligation_columns = {
                row[1]
                for row in connection.execute(text("PRAGMA table_info(obligations)"))
            }
            obligation_repairs = {
                "resolution_number": "ALTER TABLE obligations ADD COLUMN resolution_number VARCHAR(100)",
                "resolution_year": "ALTER TABLE obligations ADD COLUMN resolution_year INTEGER",
                "resolution_date": "ALTER TABLE obligations ADD COLUMN resolution_date DATE",
                "radicado_number": "ALTER TABLE obligations ADD COLUMN radicado_number VARCHAR(100)",
                "resolution_assigned_at": "ALTER TABLE obligations ADD COLUMN resolution_assigned_at DATETIME",
                "resolution_observations": "ALTER TABLE obligations ADD COLUMN resolution_observations VARCHAR(1000)",
            }
            for column_name, ddl in obligation_repairs.items():
                if column_name not in obligation_columns:
                    connection.execute(text(ddl))
