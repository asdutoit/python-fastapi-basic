from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="Valid email address", example="user@example.com")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username", example="johndoe")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password (min 8 characters)", example="mypassword123")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "username": "johndoe", 
                "password": "securepassword123"
            }
        }
    }


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, description="New email address")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="New username")
    password: Optional[str] = Field(None, min_length=8, description="New password (min 8 characters)")


class UserResponse(UserBase):
    id: str = Field(..., description="Unique user identifier")
    is_active: bool = Field(..., description="Account status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "username": "johndoe",
                "is_active": True,
                "created_at": "2024-01-01T12:00:00"
            }
        }
    }


class UserInDB(UserResponse):
    hashed_password: str