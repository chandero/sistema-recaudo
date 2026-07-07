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
    SQLModel.metadata.create_all(engine)
