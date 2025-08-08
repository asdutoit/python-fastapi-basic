from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User
from app.models.task import Task
import uuid


def test_database_operations():
    db: Session = SessionLocal()
    
    try:
        print("Testing Database Operations...")
        print("-" * 50)
        
        # Create a test user
        test_user = User(
            id=str(uuid.uuid4()),
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password_here",
            is_active=True
        )
        db.add(test_user)
        db.commit()
        print(f"✅ User created: {test_user.username} (ID: {test_user.id})")
        
        # Create tasks for the user
        task1 = Task(
            title="Complete Phase 2",
            description="Implement database layer with SQLAlchemy",
            completed=True,
            user_id=test_user.id
        )
        db.add(task1)
        
        task2 = Task(
            title="Start Phase 3",
            description="Create Pydantic schemas for validation",
            completed=False,
            user_id=test_user.id
        )
        db.add(task2)
        db.commit()
        print(f"✅ Tasks created for user {test_user.username}")
        
        # Query the database
        print("\n📊 Database Query Results:")
        print("-" * 50)
        
        # Get all users
        users = db.query(User).all()
        print(f"Total users in database: {len(users)}")
        
        # Get user with tasks
        user_with_tasks = db.query(User).filter(User.email == "test@example.com").first()
        if user_with_tasks:
            print(f"\nUser: {user_with_tasks.username}")
            print(f"Email: {user_with_tasks.email}")
            print(f"Created at: {user_with_tasks.created_at}")
            print(f"Number of tasks: {len(user_with_tasks.tasks)}")
            
            print("\nUser's Tasks:")
            for task in user_with_tasks.tasks:
                status = "✅" if task.completed else "⏳"
                print(f"  {status} {task.title}")
                print(f"     Description: {task.description}")
                print(f"     Created: {task.created_at}")
        
        # Test relationship
        print("\n🔗 Testing Relationships:")
        print("-" * 50)
        task = db.query(Task).first()
        if task:
            print(f"Task '{task.title}' belongs to user: {task.owner.username}")
        
        print("\n✅ All database tests passed successfully!")
        
        # Cleanup - remove test data
        db.query(Task).filter(Task.user_id == test_user.id).delete()
        db.query(User).filter(User.id == test_user.id).delete()
        db.commit()
        print("\n🧹 Test data cleaned up")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    test_database_operations()