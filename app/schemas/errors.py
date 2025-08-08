from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ValidationError(BaseModel):
    """Validation error detail"""
    type: str
    loc: List[str]
    msg: str
    input: Optional[Any] = None
    ctx: Optional[Dict[str, Any]] = None


class HTTPErrorResponse(BaseModel):
    """Standard HTTP error response"""
    detail: str
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "Error message describing what went wrong"
            }
        }


class ValidationErrorResponse(BaseModel):
    """Validation error response with field details"""
    detail: List[ValidationError]
    
    class Config:
        schema_extra = {
            "example": {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "title"],
                        "msg": "Field required",
                        "input": None
                    }
                ]
            }
        }


class AuthErrorResponse(BaseModel):
    """Authentication error response"""
    detail: str = "Could not validate credentials"
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "Could not validate credentials"
            }
        }


# Common response examples for documentation
COMMON_RESPONSES = {
    400: {"model": HTTPErrorResponse, "description": "Bad Request"},
    401: {"model": AuthErrorResponse, "description": "Unauthorized"},
    403: {"model": HTTPErrorResponse, "description": "Forbidden"},
    404: {"model": HTTPErrorResponse, "description": "Not Found"},
    422: {"model": ValidationErrorResponse, "description": "Validation Error"},
    500: {"model": HTTPErrorResponse, "description": "Internal Server Error"},
}