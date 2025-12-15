# ===========================================
# Vendly POS - Test Configuration
# ===========================================

import os

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment before importing app
os.environ["TESTING"] = "1"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["APP_ENV"] = "testing"
os.environ["DEBUG"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-12345678901234567890"
os.environ["JWT_SECRET"] = "test-jwt-secret-key-1234567890123456789"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core.deps import get_current_user, get_db, require_permission
from app.core.security import hash_password
from app.db.models import Base, User
from app.main import app

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


# Create a test user instance to use everywhere
test_user = None


def get_test_user():
    """Get or create test user from database"""
    global test_user
    if test_user:
        return test_user

    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "admin@vendly.com").first()
    if user:
        test_user = user
    db.close()
    return test_user


def override_get_current_user():
    """Get current user override for tests - bypass JWT validation"""
    user = get_test_user()
    if user:
        return user
    # Fallback - return a mock user
    return User(
        id=1,
        email="admin@vendly.com",
        password_hash="hashed",
        full_name="Admin",
        role="admin",
        is_active=True,
    )


def override_require_permission(permission):
    """Override permission requirement for tests - always passes"""

    def check_permission(user=Depends(override_get_current_user)):
        return user

    return check_permission


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
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[require_permission] = override_require_permission

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
    """Get authentication headers for test user"""
    # Simply return headers - auth is mocked via dependency overrides
    return {"Authorization": "Bearer test-token"}
