from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.schemas.user import UserResponse
from app.crud import task as task_crud
from app.core.dependencies import get_current_active_user
from app.models.task import Task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "/", 
    response_model=TaskResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    description="""
    Create a new task for the authenticated user.
    
    **Authentication Required:** Bearer token in Authorization header
    
    **Request Fields:**
    - **title** (required): Task title/name
    - **description** (optional): Detailed task description  
    - **completed** (default: false): Task completion status
    - **priority** (default: 0): Task priority (0=low, 1=medium, 2=high)
    
    **Returns:**
    - Complete task object with generated ID
    - User association and timestamps
    
    **Example Request:**
    ```json
    {
        "title": "Review project documentation",
        "description": "Review and update API documentation",
        "priority": 1,
        "completed": false
    }
    ```
    """
)
async def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    return task_crud.create_task(db=db, task=task, user_id=current_user.id)


@router.get(
    "/", 
    response_model=List[TaskResponse],
    summary="Get user tasks with filtering",
    description="""
    Retrieve all tasks for the authenticated user with advanced filtering options.
    
    **Authentication Required:** Bearer token in Authorization header
    
    **Query Parameters:**
    - **completed**: Filter by completion status (true/false)
    - **search**: Search text in title and description (case-insensitive)
    - **created_after**: ISO datetime string (e.g., 2024-01-01T00:00:00)
    - **created_before**: ISO datetime string (e.g., 2024-12-31T23:59:59)
    - **skip**: Number of tasks to skip for pagination (default: 0)
    - **limit**: Maximum tasks to return, max 100 (default: 100)
    
    **Features:**
    - Results ordered by creation date (newest first)
    - Supports pagination with skip/limit
    - Full-text search across title and description
    - Date range filtering
    
    **Example Usage:**
    - `/tasks/` - Get all tasks
    - `/tasks/?completed=false` - Get incomplete tasks only
    - `/tasks/?search=meeting&limit=10` - Search for "meeting" in first 10 tasks
    - `/tasks/?created_after=2024-01-01T00:00:00` - Tasks created this year
    """
)
async def get_tasks(
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of tasks to return"),
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    created_after: Optional[datetime] = Query(None, description="Filter tasks created after this date"),
    created_before: Optional[datetime] = Query(None, description="Filter tasks created before this date"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    return task_crud.get_user_tasks(
        db=db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit,
        completed=completed,
        search=search,
        created_after=created_after,
        created_before=created_before
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)  # 👈 Protected
):
    """
    Get a specific task by ID.
    Requires Bearer token in Authorization header.
    Only returns task if it belongs to the authenticated user.
    """
    task = task_crud.get_task(db=db, task_id=task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)  # 👈 Protected
):
    """
    Update a task.
    Requires Bearer token in Authorization header.
    Only updates task if it belongs to the authenticated user.
    """
    task = task_crud.update_task(db=db, task_id=task_id, user_id=current_user.id, task_update=task_update)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)  # 👈 Protected
):
    """
    Delete a task.
    Requires Bearer token in Authorization header.
    Only deletes task if it belongs to the authenticated user.
    """
    if not task_crud.delete_task(db=db, task_id=task_id, user_id=current_user.id):
        raise HTTPException(status_code=404, detail="Task not found")
    return None


# Example of a public route (no authentication required)
@router.get("/public/stats")
async def get_public_stats(db: Session = Depends(get_db)):
    """
    Public endpoint - no authentication required.
    Notice: No current_user dependency here!
    """
    task_count = db.query(Task).count()
    return {"total_tasks": task_count}