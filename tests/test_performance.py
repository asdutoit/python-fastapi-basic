import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_performance.db"

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
def authenticated_user():
    # Register user
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "perf@example.com",
            "username": "perfuser",
            "password": "password123"
        }
    )
    user = response.json()
    
    # Login
    login_response = client.post(
        "/api/v1/auth/login-json",
        json={"username": "perf@example.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    return {
        "user": user,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }


class TestAuthenticationPerformance:
    def test_login_performance(self):
        """Test login endpoint performance"""
        # Register user first
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "username": "loginuser",
                "password": "password123"
            }
        )
        
        # Measure login performance
        start_time = time.time()
        response = client.post(
            "/api/v1/auth/login-json",
            json={"username": "login@example.com", "password": "password123"}
        )
        end_time = time.time()
        
        assert response.status_code == 200
        login_time = end_time - start_time
        
        # Login should complete within reasonable time (adjust threshold as needed)
        assert login_time < 1.0, f"Login took {login_time:.3f} seconds, which is too slow"

    def test_registration_performance(self):
        """Test registration endpoint performance"""
        start_time = time.time()
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "register@example.com",
                "username": "registeruser",
                "password": "password123"
            }
        )
        end_time = time.time()
        
        assert response.status_code == 201
        registration_time = end_time - start_time
        
        # Registration should complete within reasonable time
        assert registration_time < 2.0, f"Registration took {registration_time:.3f} seconds, which is too slow"

    def test_token_verification_performance(self, authenticated_user):
        """Test JWT token verification performance"""
        headers = authenticated_user["headers"]
        
        # Measure token verification performance
        start_time = time.time()
        response = client.get("/api/v1/auth/me", headers=headers)
        end_time = time.time()
        
        assert response.status_code == 200
        verification_time = end_time - start_time
        
        # Token verification should be very fast
        assert verification_time < 0.5, f"Token verification took {verification_time:.3f} seconds, which is too slow"


class TestTaskCRUDPerformance:
    def test_task_creation_performance(self, authenticated_user):
        """Test task creation performance"""
        headers = authenticated_user["headers"]
        
        start_time = time.time()
        response = client.post(
            "/api/v1/tasks/",
            json={
                "title": "Performance Test Task",
                "description": "Testing task creation performance",
                "priority": 1
            },
            headers=headers
        )
        end_time = time.time()
        
        assert response.status_code == 201
        creation_time = end_time - start_time
        
        # Task creation should be fast
        assert creation_time < 0.5, f"Task creation took {creation_time:.3f} seconds, which is too slow"

    def test_bulk_task_creation_performance(self, authenticated_user):
        """Test performance when creating many tasks"""
        headers = authenticated_user["headers"]
        
        # Create 100 tasks and measure total time
        start_time = time.time()
        
        for i in range(100):
            response = client.post(
                "/api/v1/tasks/",
                json={
                    "title": f"Task {i}",
                    "description": f"Description for task {i}",
                    "priority": i % 3
                },
                headers=headers
            )
            assert response.status_code == 201
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time_per_task = total_time / 100
        
        # Each task creation should average less than 50ms
        assert avg_time_per_task < 0.05, f"Average task creation time: {avg_time_per_task:.3f}s, which is too slow"
        
        # Total time should be reasonable
        assert total_time < 10.0, f"Creating 100 tasks took {total_time:.3f} seconds, which is too slow"

    def test_task_listing_performance_with_large_dataset(self, authenticated_user):
        """Test performance of listing tasks with large dataset"""
        headers = authenticated_user["headers"]
        
        # Create 1000 tasks
        for i in range(1000):
            client.post(
                "/api/v1/tasks/",
                json={
                    "title": f"Task {i}",
                    "description": f"Description {i}",
                    "completed": i % 2 == 0,
                    "priority": i % 3
                },
                headers=headers
            )
        
        # Test listing performance
        start_time = time.time()
        response = client.get("/api/v1/tasks/?limit=100", headers=headers)
        end_time = time.time()
        
        assert response.status_code == 200
        assert len(response.json()) == 100
        
        listing_time = end_time - start_time
        
        # Listing 100 tasks from 1000 should be fast
        assert listing_time < 1.0, f"Listing tasks took {listing_time:.3f} seconds, which is too slow"

    def test_task_search_performance(self, authenticated_user):
        """Test performance of task search functionality"""
        headers = authenticated_user["headers"]
        
        # Create diverse tasks
        search_terms = ["meeting", "report", "email", "development", "testing"]
        for i in range(500):
            term = search_terms[i % len(search_terms)]
            client.post(
                "/api/v1/tasks/",
                json={
                    "title": f"{term} task {i}",
                    "description": f"Description for {term} task {i}",
                    "priority": i % 3
                },
                headers=headers
            )
        
        # Test search performance
        start_time = time.time()
        response = client.get("/api/v1/tasks/?search=meeting", headers=headers)
        end_time = time.time()
        
        assert response.status_code == 200
        search_time = end_time - start_time
        
        # Search should be fast
        assert search_time < 0.5, f"Search took {search_time:.3f} seconds, which is too slow"

    def test_task_filtering_performance(self, authenticated_user):
        """Test performance of task filtering"""
        headers = authenticated_user["headers"]
        
        # Create tasks with different statuses
        for i in range(500):
            client.post(
                "/api/v1/tasks/",
                json={
                    "title": f"Task {i}",
                    "completed": i % 3 == 0,  # Every third task completed
                    "priority": i % 3
                },
                headers=headers
            )
        
        # Test filtering performance
        start_time = time.time()
        response = client.get("/api/v1/tasks/?completed=true&limit=50", headers=headers)
        end_time = time.time()
        
        assert response.status_code == 200
        filtering_time = end_time - start_time
        
        # Filtering should be fast
        assert filtering_time < 0.5, f"Filtering took {filtering_time:.3f} seconds, which is too slow"


class TestConcurrencyPerformance:
    def test_concurrent_user_registrations(self):
        """Test performance under concurrent user registrations"""
        def register_user(user_id):
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"concurrent{user_id}@example.com",
                    "username": f"concurrent{user_id}",
                    "password": "password123"
                }
            )
            return response.status_code == 201
        
        # Test with 10 concurrent registrations
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(register_user, i) for i in range(10)]
            results = [future.result() for future in futures]
        end_time = time.time()
        
        # All registrations should succeed
        assert all(results), "Some concurrent registrations failed"
        
        concurrent_time = end_time - start_time
        # Should complete within reasonable time
        assert concurrent_time < 3.0, f"Concurrent registrations took {concurrent_time:.3f} seconds, which is too slow"

    def test_concurrent_task_operations(self, authenticated_user):
        """Test performance under concurrent task operations"""
        headers = authenticated_user["headers"]
        
        def create_and_update_task(task_id):
            # Create task
            create_response = client.post(
                "/api/v1/tasks/",
                json={
                    "title": f"Concurrent Task {task_id}",
                    "priority": task_id % 3
                },
                headers=headers
            )
            
            if create_response.status_code != 201:
                return False
            
            task_data = create_response.json()
            
            # Update task
            update_response = client.put(
                f"/api/v1/tasks/{task_data['id']}",
                json={
                    "title": f"Updated Concurrent Task {task_id}",
                    "completed": True
                },
                headers=headers
            )
            
            return update_response.status_code == 200
        
        # Test with 20 concurrent operations
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_and_update_task, i) for i in range(20)]
            results = [future.result() for future in futures]
        end_time = time.time()
        
        # All operations should succeed
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.9, f"Success rate was {success_rate:.2%}, which is too low"
        
        concurrent_time = end_time - start_time
        # Should complete within reasonable time
        assert concurrent_time < 5.0, f"Concurrent operations took {concurrent_time:.3f} seconds, which is too slow"


class TestMemoryUsage:
    def test_memory_usage_with_large_responses(self, authenticated_user):
        """Test that large responses don't cause memory issues"""
        headers = authenticated_user["headers"]
        
        # Create tasks with large descriptions
        large_description = "x" * 1000  # 1KB description
        
        for i in range(100):
            response = client.post(
                "/api/v1/tasks/",
                json={
                    "title": f"Large Task {i}",
                    "description": large_description,
                    "priority": i % 3
                },
                headers=headers
            )
            assert response.status_code == 201
        
        # Retrieve all tasks (should handle large response efficiently)
        start_time = time.time()
        response = client.get("/api/v1/tasks/", headers=headers)
        end_time = time.time()
        
        assert response.status_code == 200
        assert len(response.json()) == 100
        
        retrieval_time = end_time - start_time
        # Should handle large responses efficiently
        assert retrieval_time < 2.0, f"Large response retrieval took {retrieval_time:.3f} seconds, which is too slow"


class TestDatabasePerformance:
    def test_pagination_performance(self, authenticated_user):
        """Test that pagination is efficient even with large datasets"""
        headers = authenticated_user["headers"]
        
        # Create 1000 tasks
        for i in range(1000):
            client.post(
                "/api/v1/tasks/",
                json={
                    "title": f"Pagination Task {i}",
                    "priority": i % 3
                },
                headers=headers
            )
        
        # Test different pagination positions
        page_positions = [0, 100, 500, 900]
        
        for skip in page_positions:
            start_time = time.time()
            response = client.get(
                f"/api/v1/tasks/?skip={skip}&limit=50",
                headers=headers
            )
            end_time = time.time()
            
            assert response.status_code == 200
            assert len(response.json()) == 50
            
            page_time = end_time - start_time
            # Pagination should be efficient regardless of position
            assert page_time < 0.5, f"Pagination at position {skip} took {page_time:.3f} seconds, which is too slow"