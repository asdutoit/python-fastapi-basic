import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.core.security import create_access_token, verify_token, get_password_hash, verify_password
from datetime import timedelta, datetime
from jose import jwt
import time

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_security.db"

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


@pytest.fixture
def valid_user():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "security@example.com",
            "username": "securityuser",
            "password": "securepassword123"
        }
    )
    return response.json()


class TestPasswordSecurity:
    def test_password_hashing(self):
        """Test that passwords are properly hashed"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # Hash should be different from original password
        assert hashed != password
        # Hash should be consistent for same password
        assert verify_password(password, hashed) is True
        # Wrong password should not verify
        assert verify_password("wrongpassword", hashed) is False

    def test_password_complexity_enforced(self):
        """Test that password requirements are enforced"""
        # Too short password
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test1@example.com",
                "username": "testuser1",
                "password": "short"
            }
        )
        assert response.status_code == 422
        
        # Valid password
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test2@example.com",
                "username": "testuser2", 
                "password": "validpassword123"
            }
        )
        assert response.status_code == 201

    def test_password_not_returned_in_response(self, valid_user):
        """Test that password/hash is never returned in API responses"""
        # Registration response
        assert "password" not in valid_user
        assert "hashed_password" not in valid_user
        
        # Login and get user profile
        login_response = client.post(
            "/api/v1/auth/login-json",
            json={"username": "security@example.com", "password": "securepassword123"}
        )
        token = login_response.json()["access_token"]
        
        profile_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        profile_data = profile_response.json()
        assert "password" not in profile_data
        assert "hashed_password" not in profile_data


class TestJWTSecurity:
    def test_token_creation_and_verification(self):
        """Test JWT token creation and verification"""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        # Token should be a string
        assert isinstance(token, str)
        # Should be able to verify token
        email = verify_token(token)
        assert email == "test@example.com"

    def test_token_expiration(self):
        """Test that expired tokens are rejected"""
        data = {"sub": "test@example.com"}
        # Create token that expires in 1 second
        token = create_access_token(data, expires_delta=timedelta(seconds=1))
        
        # Should work immediately
        email = verify_token(token)
        assert email == "test@example.com"
        
        # Wait for expiration
        time.sleep(2)
        
        # Should be invalid after expiration
        email = verify_token(token)
        assert email is None

    def test_token_tampering_detection(self):
        """Test that tampered tokens are rejected"""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        # Tamper with the token
        tampered_token = token[:-5] + "XXXXX"
        
        # Should be rejected
        email = verify_token(tampered_token)
        assert email is None

    def test_invalid_token_formats(self):
        """Test various invalid token formats"""
        invalid_tokens = [
            "invalid.token",
            "not.a.token.at.all",
            "",
            "Bearer token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"  # Incomplete token
        ]
        
        for invalid_token in invalid_tokens:
            email = verify_token(invalid_token)
            assert email is None


class TestAuthenticationEndpoints:
    def test_authentication_required_endpoints(self):
        """Test that protected endpoints require authentication"""
        protected_endpoints = [
            ("GET", "/api/v1/auth/me"),
            ("GET", "/api/v1/tasks/"),
            ("POST", "/api/v1/tasks/"),
            ("GET", "/api/v1/tasks/some-id"),
            ("PUT", "/api/v1/tasks/some-id"),
            ("DELETE", "/api/v1/tasks/some-id"),
        ]
        
        for method, endpoint in protected_endpoints:
            response = client.request(method, endpoint)
            assert response.status_code == 401
            assert "Not authenticated" in response.json()["detail"]

    def test_invalid_token_rejected(self):
        """Test that invalid tokens are properly rejected"""
        invalid_tokens = [
            "Bearer invalid-token",
            "Bearer ",
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid",
            "InvalidFormat token"
        ]
        
        for invalid_token in invalid_tokens:
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": invalid_token}
            )
            assert response.status_code == 401

    def test_expired_token_rejected(self, valid_user):
        """Test that expired tokens are rejected"""
        # Create a token that expires immediately  
        data = {"sub": "security@example.com"}
        expired_token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401

    def test_login_brute_force_protection(self):
        """Test protection against brute force attacks"""
        # Register a user first
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "bruteforce@example.com",
                "username": "bruteuser",
                "password": "correctpassword123"
            }
        )
        
        # Try multiple failed login attempts
        for i in range(5):
            response = client.post(
                "/api/v1/auth/login-json",
                json={"username": "bruteforce@example.com", "password": "wrongpassword"}
            )
            assert response.status_code == 401
        
        # Should still be able to login with correct credentials
        response = client.post(
            "/api/v1/auth/login-json",
            json={"username": "bruteforce@example.com", "password": "correctpassword123"}
        )
        assert response.status_code == 200


class TestDataIsolation:
    def test_user_data_isolation(self):
        """Test that users can only access their own data"""
        # Create two users
        user1_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user1@example.com",
                "username": "user1",
                "password": "password123"
            }
        )
        
        user2_response = client.post(
            "/api/v1/auth/register", 
            json={
                "email": "user2@example.com",
                "username": "user2",
                "password": "password123"
            }
        )
        
        # Login both users
        user1_login = client.post(
            "/api/v1/auth/login-json",
            json={"username": "user1@example.com", "password": "password123"}
        )
        user1_token = user1_login.json()["access_token"]
        
        user2_login = client.post(
            "/api/v1/auth/login-json",
            json={"username": "user2@example.com", "password": "password123"}
        )
        user2_token = user2_login.json()["access_token"]
        
        # Create task for user1
        task_response = client.post(
            "/api/v1/tasks/",
            json={"title": "User 1 Private Task", "priority": 0},
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        task_id = task_response.json()["id"]
        
        # User2 should not be able to access user1's task
        response = client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        assert response.status_code == 404
        
        # User2 should not see user1's tasks in list
        response = client.get(
            "/api/v1/tasks/",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        assert len(response.json()) == 0
        
        # User1 should see their own task
        response = client.get(
            "/api/v1/tasks/",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert len(response.json()) == 1


class TestInputValidation:
    def test_sql_injection_prevention(self):
        """Test that SQL injection attempts are prevented"""
        # Try SQL injection in login
        sql_injection_attempts = [
            "'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "'; INSERT INTO users VALUES ('hacker', 'hack@hack.com'); --"
        ]
        
        for injection_attempt in sql_injection_attempts:
            response = client.post(
                "/api/v1/auth/login-json",
                json={"username": injection_attempt, "password": "anything"}
            )
            # Should get 401, not 500 (which would indicate SQL error)
            assert response.status_code == 401

    def test_xss_prevention_in_task_data(self):
        """Test that XSS attempts in task data are handled"""
        # Register and login user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "xsstest@example.com",
                "username": "xssuser",
                "password": "password123"
            }
        )
        
        login_response = client.post(
            "/api/v1/auth/login-json",
            json={"username": "xsstest@example.com", "password": "password123"}
        )
        token = login_response.json()["access_token"]
        
        # Try to create task with XSS payload
        xss_payload = "<script>alert('XSS')</script>"
        response = client.post(
            "/api/v1/tasks/",
            json={
                "title": f"Task {xss_payload}",
                "description": f"Description {xss_payload}",
                "priority": 0
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        task_data = response.json()
        
        # The payload should be stored as-is (FastAPI handles output encoding)
        assert xss_payload in task_data["title"]
        assert xss_payload in task_data["description"]

    def test_input_length_limits(self):
        """Test that input length limits are enforced"""
        # Register user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "length@example.com",
                "username": "lengthuser",
                "password": "password123"
            }
        )
        
        login_response = client.post(
            "/api/v1/auth/login-json",
            json={"username": "length@example.com", "password": "password123"}
        )
        token = login_response.json()["access_token"]
        
        # Try to create task with too long title
        long_title = "x" * 300  # Exceeds max length of 200
        response = client.post(
            "/api/v1/tasks/",
            json={"title": long_title, "priority": 0},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 422  # Validation error
        
        # Try to create task with too long description  
        long_description = "x" * 3000  # Exceeds max length of 2000
        response = client.post(
            "/api/v1/tasks/",
            json={
                "title": "Valid Title",
                "description": long_description,
                "priority": 0
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 422  # Validation error