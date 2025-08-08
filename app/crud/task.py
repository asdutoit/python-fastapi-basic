from sqlalchemy.orm import Session
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from typing import Optional, List
from datetime import datetime


def create_task(db: Session, task: TaskCreate, user_id: str) -> Task:
    db_task = Task(
        title=task.title,
        description=task.description,
        completed=task.completed,
        priority=task.priority,
        user_id=user_id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_task(db: Session, task_id: str, user_id: str) -> Optional[Task]:
    return db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()


def get_user_tasks(
    db: Session, 
    user_id: str, 
    skip: int = 0, 
    limit: int = 100,
    completed: Optional[bool] = None,
    search: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None
) -> List[Task]:
    query = db.query(Task).filter(Task.user_id == user_id)
    
    if completed is not None:
        query = query.filter(Task.completed == completed)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Task.title.ilike(search_pattern)) | 
            (Task.description.ilike(search_pattern))
        )
    
    if created_after:
        query = query.filter(Task.created_at >= created_after)
    
    if created_before:
        query = query.filter(Task.created_at <= created_before)
    
    query = query.order_by(Task.created_at.desc())
    
    return query.offset(skip).limit(limit).all()


def update_task(db: Session, task_id: str, user_id: str, task_update: TaskUpdate) -> Optional[Task]:
    db_task = get_task(db, task_id, user_id)
    if not db_task:
        return None
    
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: str, user_id: str) -> bool:
    db_task = get_task(db, task_id, user_id)
    if not db_task:
        return False
    
    db.delete(db_task)
    db.commit()
    return True