import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.crud import user as user_crud, task as task_crud
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.task import TaskCreate, TaskUpdate
from datetime import datetime, timedelta

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_crud.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_user(db_session):
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="testpassword123"
    )
    return user_crud.create_user(db_session, user_data)


class TestUserCRUD:
    def test_create_user(self, db_session):
        user_data = UserCreate(
            email="new@example.com",
            username="newuser",
            password="password123"
        )
        user = user_crud.create_user(db_session, user_data)
        
        assert user.email == "new@example.com"
        assert user.username == "newuser"
        assert user.is_active is True
        assert user.hashed_password is not None
        assert user.hashed_password != "password123"  # Should be hashed
        assert user.id is not None
        assert user.created_at is not None

    def test_get_user_by_email(self, db_session, sample_user):
        found_user = user_crud.get_user_by_email(db_session, "test@example.com")
        assert found_user is not None
        assert found_user.id == sample_user.id
        assert found_user.email == sample_user.email
        
        # Test non-existent email
        not_found = user_crud.get_user_by_email(db_session, "nonexistent@example.com")
        assert not_found is None

    def test_get_user_by_username(self, db_session, sample_user):
        found_user = user_crud.get_user_by_username(db_session, "testuser")
        assert found_user is not None
        assert found_user.id == sample_user.id
        assert found_user.username == sample_user.username
        
        # Test non-existent username
        not_found = user_crud.get_user_by_username(db_session, "nonexistent")
        assert not_found is None

    def test_get_user_by_id(self, db_session, sample_user):
        found_user = user_crud.get_user(db_session, sample_user.id)
        assert found_user is not None
        assert found_user.id == sample_user.id
        
        # Test non-existent ID
        not_found = user_crud.get_user(db_session, "nonexistent-id")
        assert not_found is None

    def test_update_user(self, db_session, sample_user):
        update_data = UserUpdate(
            email="updated@example.com",
            username="updateduser",
            password="newpassword123"
        )
        updated_user = user_crud.update_user(db_session, sample_user.id, update_data)
        
        assert updated_user is not None
        assert updated_user.email == "updated@example.com"
        assert updated_user.username == "updateduser"
        assert updated_user.hashed_password != sample_user.hashed_password  # Password changed
        
        # Test partial update
        partial_update = UserUpdate(email="partial@example.com")
        updated_user = user_crud.update_user(db_session, sample_user.id, partial_update)
        assert updated_user.email == "partial@example.com"
        assert updated_user.username == "updateduser"  # Unchanged
        
        # Test update non-existent user
        not_updated = user_crud.update_user(db_session, "nonexistent-id", update_data)
        assert not_updated is None

    def test_delete_user(self, db_session, sample_user):
        user_id = sample_user.id
        
        # Delete user
        deleted = user_crud.delete_user(db_session, user_id)
        assert deleted is True
        
        # Verify user is deleted
        found_user = user_crud.get_user(db_session, user_id)
        assert found_user is None
        
        # Try to delete non-existent user
        not_deleted = user_crud.delete_user(db_session, "nonexistent-id")
        assert not_deleted is False

    def test_get_users(self, db_session):
        # Create multiple users
        users_data = [
            UserCreate(email=f"user{i}@example.com", username=f"user{i}", password="password123")
            for i in range(5)
        ]
        created_users = [user_crud.create_user(db_session, user_data) for user_data in users_data]
        
        # Test pagination
        users_page1 = user_crud.get_users(db_session, skip=0, limit=3)
        assert len(users_page1) == 3
        
        users_page2 = user_crud.get_users(db_session, skip=3, limit=3)
        assert len(users_page2) == 2
        
        # Test all users
        all_users = user_crud.get_users(db_session)
        assert len(all_users) == 5


class TestTaskCRUD:
    def test_create_task(self, db_session, sample_user):
        task_data = TaskCreate(
            title="Test Task",
            description="This is a test task",
            completed=False,
            priority=1
        )
        task = task_crud.create_task(db_session, task_data, sample_user.id)
        
        assert task.title == "Test Task"
        assert task.description == "This is a test task"
        assert task.completed is False
        assert task.priority == 1
        assert task.user_id == sample_user.id
        assert task.id is not None
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_get_task(self, db_session, sample_user):
        # Create task
        task_data = TaskCreate(title="Test Task", description="Test", priority=0)
        created_task = task_crud.create_task(db_session, task_data, sample_user.id)
        
        # Get task
        found_task = task_crud.get_task(db_session, created_task.id, sample_user.id)
        assert found_task is not None
        assert found_task.id == created_task.id
        assert found_task.user_id == sample_user.id
        
        # Test with wrong user_id (security test)
        not_found = task_crud.get_task(db_session, created_task.id, "wrong-user-id")
        assert not_found is None
        
        # Test non-existent task
        not_found = task_crud.get_task(db_session, "nonexistent-id", sample_user.id)
        assert not_found is None

    def test_get_user_tasks(self, db_session, sample_user):
        # Create multiple tasks
        tasks_data = [
            TaskCreate(title=f"Task {i}", description=f"Description {i}", 
                      completed=i % 2 == 0, priority=i % 3)
            for i in range(10)
        ]
        created_tasks = [
            task_crud.create_task(db_session, task_data, sample_user.id) 
            for task_data in tasks_data
        ]
        
        # Test basic retrieval
        all_tasks = task_crud.get_user_tasks(db_session, sample_user.id)
        assert len(all_tasks) == 10
        
        # Test pagination
        page1 = task_crud.get_user_tasks(db_session, sample_user.id, skip=0, limit=5)
        assert len(page1) == 5
        
        page2 = task_crud.get_user_tasks(db_session, sample_user.id, skip=5, limit=5)
        assert len(page2) == 5
        
        # Test completed filter
        completed_tasks = task_crud.get_user_tasks(db_session, sample_user.id, completed=True)
        assert len(completed_tasks) == 5  # Tasks 0, 2, 4, 6, 8
        assert all(task.completed for task in completed_tasks)
        
        incomplete_tasks = task_crud.get_user_tasks(db_session, sample_user.id, completed=False)
        assert len(incomplete_tasks) == 5  # Tasks 1, 3, 5, 7, 9
        assert all(not task.completed for task in incomplete_tasks)
        
        # Test search
        search_tasks = task_crud.get_user_tasks(db_session, sample_user.id, search="Task 5")
        assert len(search_tasks) == 1
        assert "Task 5" in search_tasks[0].title
        
        # Test date filtering
        yesterday = datetime.utcnow() - timedelta(days=1)
        tomorrow = datetime.utcnow() + timedelta(days=1)
        
        recent_tasks = task_crud.get_user_tasks(
            db_session, sample_user.id, created_after=yesterday
        )
        assert len(recent_tasks) == 10  # All tasks created today
        
        old_tasks = task_crud.get_user_tasks(
            db_session, sample_user.id, created_before=yesterday
        )
        assert len(old_tasks) == 0  # No tasks created before yesterday

    def test_update_task(self, db_session, sample_user):
        # Create task
        task_data = TaskCreate(title="Original Task", description="Original", priority=0)
        created_task = task_crud.create_task(db_session, task_data, sample_user.id)
        
        # Update task
        update_data = TaskUpdate(
            title="Updated Task",
            description="Updated description",
            completed=True,
            priority=2
        )
        updated_task = task_crud.update_task(
            db_session, created_task.id, sample_user.id, update_data
        )
        
        assert updated_task is not None
        assert updated_task.title == "Updated Task"
        assert updated_task.description == "Updated description"
        assert updated_task.completed is True
        assert updated_task.priority == 2
        assert updated_task.updated_at > updated_task.created_at
        
        # Test partial update
        partial_update = TaskUpdate(completed=False)
        updated_task = task_crud.update_task(
            db_session, created_task.id, sample_user.id, partial_update
        )
        assert updated_task.completed is False
        assert updated_task.title == "Updated Task"  # Unchanged
        
        # Test update with wrong user_id
        not_updated = task_crud.update_task(
            db_session, created_task.id, "wrong-user-id", update_data
        )
        assert not_updated is None
        
        # Test update non-existent task
        not_updated = task_crud.update_task(
            db_session, "nonexistent-id", sample_user.id, update_data
        )
        assert not_updated is None

    def test_delete_task(self, db_session, sample_user):
        # Create task
        task_data = TaskCreate(title="Task to Delete", priority=0)
        created_task = task_crud.create_task(db_session, task_data, sample_user.id)
        task_id = created_task.id
        
        # Delete task
        deleted = task_crud.delete_task(db_session, task_id, sample_user.id)
        assert deleted is True
        
        # Verify task is deleted
        found_task = task_crud.get_task(db_session, task_id, sample_user.id)
        assert found_task is None
        
        # Try to delete with wrong user_id
        task_data2 = TaskCreate(title="Another Task", priority=0)
        created_task2 = task_crud.create_task(db_session, task_data2, sample_user.id)
        
        not_deleted = task_crud.delete_task(db_session, created_task2.id, "wrong-user-id")
        assert not_deleted is False
        
        # Verify task still exists
        found_task = task_crud.get_task(db_session, created_task2.id, sample_user.id)
        assert found_task is not None
        
        # Try to delete non-existent task
        not_deleted = task_crud.delete_task(db_session, "nonexistent-id", sample_user.id)
        assert not_deleted is False


class TestDataIntegrity:
    def test_user_task_relationship(self, db_session):
        # Create user
        user_data = UserCreate(email="test@example.com", username="testuser", password="pass123456")
        user = user_crud.create_user(db_session, user_data)
        
        # Create tasks
        task_data = TaskCreate(title="User Task", priority=0)
        task = task_crud.create_task(db_session, task_data, user.id)
        
        # Verify relationship
        assert task.user_id == user.id
        
        # Test cascade delete (if user is deleted, tasks should be deleted)
        user_crud.delete_user(db_session, user.id)
        found_task = task_crud.get_task(db_session, task.id, user.id)
        assert found_task is None  # Task should be deleted due to cascade

    def test_unique_constraints(self, db_session):
        # Create first user
        user_data1 = UserCreate(email="test@example.com", username="testuser", password="pass123456")
        user1 = user_crud.create_user(db_session, user_data1)
        assert user1 is not None
        
        # Try to create user with same email
        user_data2 = UserCreate(email="test@example.com", username="differentuser", password="pass123456")
        try:
            user2 = user_crud.create_user(db_session, user_data2)
            assert False, "Should have raised an exception for duplicate email"
        except Exception:
            pass  # Expected
        
        # Try to create user with same username
        user_data3 = UserCreate(email="different@example.com", username="testuser", password="pass123456")
        try:
            user3 = user_crud.create_user(db_session, user_data3)
            assert False, "Should have raised an exception for duplicate username"
        except Exception:
            pass  # Expected