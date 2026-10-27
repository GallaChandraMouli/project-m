import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("worker"))

from app.core.config import settings
settings.DATABASE_URL = "sqlite:///./test_suite.db"

from app.core.database import Base, engine, SessionLocal, get_db
from app.main import app
from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.services.billing import get_or_create_wallet

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_suite.db"):
        try:
            os.remove("./test_suite.db")
        except Exception:
            pass

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db):
    def override_get_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def consumer_user(db):
    email = f"consumer_{os.urandom(4).hex()}@example.com"
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        role="consumer"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    get_or_create_wallet(db, user.id)
    return user

@pytest.fixture
def provider_user(db):
    email = f"provider_{os.urandom(4).hex()}@example.com"
    user = User(
        email=email,
        password_hash=hash_password("Password123!"),
        role="provider"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    get_or_create_wallet(db, user.id)
    return user

@pytest.fixture
def consumer_token(consumer_user):
    return create_access_token(data={"sub": consumer_user.id, "email": consumer_user.email, "role": consumer_user.role})

@pytest.fixture
def provider_token(provider_user):
    return create_access_token(data={"sub": provider_user.id, "email": provider_user.email, "role": provider_user.role})

@pytest.fixture
def consumer_headers(consumer_token):
    return {"Authorization": f"Bearer {consumer_token}"}

@pytest.fixture
def provider_headers(provider_token):
    return {"Authorization": f"Bearer {provider_token}"}
