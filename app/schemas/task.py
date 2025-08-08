from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import IntEnum


class TaskPriority(IntEnum):
    """Task priority levels"""
    LOW = 0
    MEDIUM = 1
    HIGH = 2


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Task title", example="Review project documentation")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed task description", example="Review and update the API documentation for accuracy")
    completed: bool = Field(False, description="Task completion status")
    priority: int = Field(default=0, ge=0, le=2, description="Task priority: 0=Low, 1=Medium, 2=High", example=1)


class TaskCreate(TaskBase):
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Review project documentation",
                "description": "Review and update the API documentation for accuracy",
                "completed": False,
                "priority": 1
            }
        }
    }


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="New task title")
    description: Optional[str] = Field(None, max_length=2000, description="New task description")
    completed: Optional[bool] = Field(None, description="New completion status")
    priority: Optional[int] = Field(None, ge=0, le=2, description="New priority level")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "completed": True,
                "priority": 2
            }
        }
    }


class TaskResponse(TaskBase):
    id: str = Field(..., description="Unique task identifier")
    user_id: str = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Task creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "456e7890-e89b-12d3-a456-426614174000",
                "title": "Review project documentation",
                "description": "Review and update the API documentation for accuracy",
                "completed": False,
                "priority": 1,
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2024-01-01T10:30:00",
                "updated_at": "2024-01-01T10:30:00"
            }
        }
    }