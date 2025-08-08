import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tasks.db"

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
def test_user():
    """Create a test user and return the user data with token"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == 201
    
    # Login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "test@example.com",
            "password": "testpass123"
        }
    )
    assert login_response.status_code == 200
    
    return {
        "user": response.json(),
        "token": login_response.json()["access_token"]
    }


@pytest.fixture
def auth_headers(test_user):
    """Return authorization headers with token"""
    return {"Authorization": f"Bearer {test_user['token']}"}


def test_create_task(auth_headers):
    response = client.post(
        "/api/v1/tasks/",
        json={
            "title": "Test Task",
            "description": "This is a test task",
            "completed": False
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "This is a test task"
    assert data["completed"] is False
    assert "id" in data
    assert "user_id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_task_without_auth():
    response = client.post(
        "/api/v1/tasks/",
        json={
            "title": "Test Task",
            "description": "This is a test task"
        }
    )
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_get_tasks_empty(auth_headers):
    response = client.get("/api/v1/tasks/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_get_tasks_with_data(auth_headers):
    # Create multiple tasks
    tasks = [
        {"title": "Task 1", "description": "First task", "completed": False},
        {"title": "Task 2", "description": "Second task", "completed": True},
        {"title": "Task 3", "description": "Third task", "completed": False}
    ]
    
    created_tasks = []
    for task in tasks:
        response = client.post("/api/v1/tasks/", json=task, headers=auth_headers)
        assert response.status_code == 201
        created_tasks.append(response.json())
    
    # Get all tasks
    response = client.get("/api/v1/tasks/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_get_tasks_with_filters(auth_headers):
    # Create tasks with different statuses
    tasks = [
        {"title": "Completed Task", "description": "Done", "completed": True},
        {"title": "Pending Task", "description": "Not done", "completed": False},
        {"title": "Another Done", "description": "Finished", "completed": True}
    ]
    
    for task in tasks:
        client.post("/api/v1/tasks/", json=task, headers=auth_headers)
    
    # Test completed filter
    response = client.get("/api/v1/tasks/?completed=true", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(task["completed"] for task in data)
    
    # Test incomplete filter
    response = client.get("/api/v1/tasks/?completed=false", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert not data[0]["completed"]


def test_get_tasks_with_search(auth_headers):
    # Create tasks with different titles and descriptions
    tasks = [
        {"title": "Buy groceries", "description": "Milk, eggs, bread"},
        {"title": "Write report", "description": "Q4 financial report"},
        {"title": "Call mom", "description": "Birthday reminder"}
    ]
    
    for task in tasks:
        client.post("/api/v1/tasks/", json=task, headers=auth_headers)
    
    # Search for "report"
    response = client.get("/api/v1/tasks/?search=report", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "report" in data[0]["title"].lower()
    
    # Search for "birthday"
    response = client.get("/api/v1/tasks/?search=birthday", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "birthday" in data[0]["description"].lower()


def test_get_tasks_pagination(auth_headers):
    # Create 10 tasks
    for i in range(10):
        client.post(
            "/api/v1/tasks/",
            json={"title": f"Task {i}", "description": f"Description {i}"},
            headers=auth_headers
        )
    
    # Test limit
    response = client.get("/api/v1/tasks/?limit=5", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 5
    
    # Test skip
    response = client.get("/api/v1/tasks/?skip=5&limit=5", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 5
    
    # Test skip beyond available
    response = client.get("/api/v1/tasks/?skip=20", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_get_task_by_id(auth_headers):
    # Create a task
    create_response = client.post(
        "/api/v1/tasks/",
        json={"title": "Test Task", "description": "Test description"},
        headers=auth_headers
    )
    task_id = create_response.json()["id"]
    
    # Get the task by ID
    response = client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Test Task"


def test_get_task_not_found(auth_headers):
    response = client.get("/api/v1/tasks/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]


def test_update_task(auth_headers):
    # Create a task
    create_response = client.post(
        "/api/v1/tasks/",
        json={"title": "Original Task", "description": "Original description"},
        headers=auth_headers
    )
    task_id = create_response.json()["id"]
    
    # Update the task
    response = client.put(
        f"/api/v1/tasks/{task_id}",
        json={
            "title": "Updated Task",
            "description": "Updated description",
            "completed": True
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Task"
    assert data["description"] == "Updated description"
    assert data["completed"] is True


def test_partial_update_task(auth_headers):
    # Create a task
    create_response = client.post(
        "/api/v1/tasks/",
        json={"title": "Original Task", "description": "Original description"},
        headers=auth_headers
    )
    task_id = create_response.json()["id"]
    
    # Partial update - only completed status
    response = client.put(
        f"/api/v1/tasks/{task_id}",
        json={"completed": True},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Original Task"  # Unchanged
    assert data["description"] == "Original description"  # Unchanged
    assert data["completed"] is True  # Updated


def test_delete_task(auth_headers):
    # Create a task
    create_response = client.post(
        "/api/v1/tasks/",
        json={"title": "Task to Delete", "description": "Will be deleted"},
        headers=auth_headers
    )
    task_id = create_response.json()["id"]
    
    # Delete the task
    response = client.delete(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == 204
    
    # Verify it's deleted
    response = client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == 404


def test_delete_nonexistent_task(auth_headers):
    response = client.delete("/api/v1/tasks/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]


def test_user_isolation(test_user):
    """Test that users can only see their own tasks"""
    # Create task for first user
    headers1 = {"Authorization": f"Bearer {test_user['token']}"}
    response = client.post(
        "/api/v1/tasks/",
        json={"title": "User 1 Task", "description": "Private task"},
        headers=headers1
    )
    task_id = response.json()["id"]
    
    # Create second user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "user2@example.com",
            "username": "user2",
            "password": "pass123"
        }
    )
    
    # Login as second user
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "user2@example.com",
            "password": "pass123"
        }
    )
    token2 = login_response.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # Try to access first user's task
    response = client.get(f"/api/v1/tasks/{task_id}", headers=headers2)
    assert response.status_code == 404  # Should not find the task
    
    # Second user should see empty task list
    response = client.get("/api/v1/tasks/", headers=headers2)
    assert response.status_code == 200
    assert len(response.json()) == 0