import os
import shutil

os.environ["ENV"] = "test"
os.environ["DEBUG"] = "false"
os.environ["SECRET_KEY"] = "test-secret-key-32-bytes-minimum-ok"
os.environ["CORS_ORIGINS"] = "*"
os.environ["DATABASE_URL"] = "sqlite:///./test_ecverifica.db"
os.environ["AI_PROVIDER"] = "mock"
os.environ["AI_ENABLED"] = "true"
os.environ["WORKER_BACKEND"] = "inline"
os.environ["UPLOAD_DIR"] = "test_uploads"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.core.security import create_access_token
from app.main import app
from app.models.base import Base
from app.models.user import User, UserRole
from app.services.user_service import create_user


@pytest.fixture(scope="session", autouse=True)
def _cleanup_dbs():
    if os.path.exists("test_ecverifica.db"):
        os.remove("test_ecverifica.db")
    yield
    engine.dispose()
    if os.path.exists("test_ecverifica.db"):
        os.remove("test_ecverifica.db")
    shutil.rmtree("test_uploads", ignore_errors=True)


@pytest.fixture(autouse=True)
def _clean_tables(db: Session):
    yield
    db.commit()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def regular_user(db: Session):
    return create_user(db, "user@test.com", "Usuario Normal", "password123")


@pytest.fixture()
def verifier_user(db: Session):
    return create_user(db, "verifier@test.com", "Verificador", "password123", role=UserRole.verifier)


@pytest.fixture()
def admin_user(db: Session):
    return create_user(db, "admin@test.com", "Administrador", "password123", role=UserRole.admin)


@pytest.fixture()
def auth_headers():
    def _make(user: User) -> dict[str, str]:
        token = create_access_token(subject=user.id, role=user.role.value)
        return {"Authorization": f"Bearer {token}"}

    return _make
