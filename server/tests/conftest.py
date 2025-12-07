# ===========================================
# Vendly POS - Test Configuration
# ===========================================

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Set test environment before importing app
os.environ["TESTING"] = "1"
os.environ["RATE_LIMIT_ENABLED"] = "false"

from app.main import app
from app.db.models import Base, User
from app.core.deps import get_db
from app.core.security import hash_password


# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Database dependency override for tests"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Set up fresh database for each test"""
    Base.metadata.create_all(bind=engine)

    # Create admin user
    db = TestingSessionLocal()
    admin = db.query(User).filter(User.email == "admin@vendly.com").first()
    if not admin:
        admin = User(
            email="admin@vendly.com",
            password_hash=hash_password("admin123"),
            full_name="Admin User",
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
    db.close()

    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db

    yield

    # Cleanup
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db():
    """Get database session for tests"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    """Create a test client"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client):
    """Get authentication headers for admin user"""
    response = client.post(
        "/api/v1/auth/login", json={"email": "admin@vendly.com", "password": "admin123"}
    )

    if response.status_code != 200:
        pytest.fail(f"Failed to login admin user: {response.text}")

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
