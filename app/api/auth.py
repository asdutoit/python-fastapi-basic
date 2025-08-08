from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import Token, LoginRequest
from app.schemas.errors import COMMON_RESPONSES
from app.crud import user as user_crud
from app.core.security import verify_password, create_access_token
from app.config import settings
from app.core.dependencies import get_current_active_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register", 
    response_model=UserResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
    Create a new user account.
    
    **Requirements:**
    - Email must be unique and valid
    - Username must be unique
    - Password must be provided (will be securely hashed)
    
    **Returns:**
    - User information (password is never returned)
    - User ID for reference
    - Account creation timestamp
    """,
    responses={
        201: {"description": "User successfully created"},
        400: {"description": "Email or username already exists"},
        **{k: v for k, v in COMMON_RESPONSES.items() if k in [422]}
    }
)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    db_user = user_crud.get_user_by_email(db, email=user_data.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    db_user = user_crud.get_user_by_username(db, username=user_data.username)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )
    
    return user_crud.create_user(db=db, user=user_data)


@router.post(
    "/login", 
    response_model=Token,
    summary="Login with form data (OAuth2 compatible)",
    description="""
    OAuth2 compatible login endpoint using form-encoded data.
    
    **Authentication:**
    - The 'username' field accepts either email or username
    - Password is verified against stored hash
    
    **Returns:**
    - JWT access token valid for 30 minutes
    - Token type (always 'bearer')
    
    **Usage:**
    Use form-encoded data with Content-Type: application/x-www-form-urlencoded
    """
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Try to find user by email first, then by username
    user = user_crud.get_user_by_email(db, email=form_data.username)
    if not user:
        user = user_crud.get_user_by_username(db, username=form_data.username)
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/login-json", 
    response_model=Token,
    summary="Login with JSON data (modern web apps)",
    description="""
    JSON-based login endpoint for modern web applications.
    
    **Authentication:**
    - The 'username' field accepts either email or username
    - Password is verified against stored hash
    
    **Returns:**
    - JWT access token valid for 30 minutes
    - Token type (always 'bearer')
    
    **Usage:**
    Use JSON data with Content-Type: application/json
    
    **Example Request:**
    ```json
    {
        "username": "user@example.com",
        "password": "mypassword"
    }
    ```
    """
)
async def login_json(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    # Try to find user by email first, then by username
    user = user_crud.get_user_by_email(db, email=login_data.username)
    if not user:
        user = user_crud.get_user_by_username(db, username=login_data.username)
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get(
    "/me", 
    response_model=UserResponse,
    summary="Get current user profile",
    description="""
    Retrieve the authenticated user's profile information.
    
    **Authentication Required:**
    - Must provide valid JWT token in Authorization header
    - Token format: `Bearer YOUR_TOKEN`
    
    **Returns:**
    - Complete user profile (excluding password)
    - Account status and creation date
    """
)
async def get_current_user(
    current_user: UserResponse = Depends(get_current_active_user)
):
    return current_user