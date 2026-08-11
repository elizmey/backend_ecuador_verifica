from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Crea las tablas si no existen (solo en desarrollo/CI).

    En producción usa migraciones Alembic (ver README).
    """
    from app.core.config import get_settings
    from app.models import analysis, news, request, source, user  # noqa: F401
    from app.models.base import Base

    if get_settings().ENV == "production":
        return

    Base.metadata.create_all(bind=engine)
