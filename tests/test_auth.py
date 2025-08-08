import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.config import settings

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def test_register_user():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicate_email():
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser2",
            "password": "testpass123"
        }
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_register_duplicate_username():
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test2@example.com",
            "username": "testuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == 400
    assert "Username already taken" in response.json()["detail"]


def test_login_success():
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123"
        }
    )
    
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "test@example.com",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123"
        }
    )
    
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "test@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "Incorrect username/email or password" in response.json()["detail"]


def test_login_nonexistent_user():
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "testpass123"
        }
    )
    assert response.status_code == 401
    assert "Incorrect username/email or password" in response.json()["detail"]


def test_get_current_user():
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123"
        }
    )
    
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "test@example.com",
            "password": "testpass123"
        }
    )
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "hashed_password" not in data


def test_get_current_user_invalid_token():
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]


def test_get_current_user_no_token():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]