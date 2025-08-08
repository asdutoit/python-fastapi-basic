from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.api import auth, tasks

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="""
A **modern**, **secure**, and **scalable** Task Management API built with FastAPI.

## Features

* 🔐 **JWT Authentication** - Secure user authentication with JWT tokens
* 👤 **User Management** - User registration, login, and profile management
* ✅ **Task CRUD** - Create, read, update, and delete tasks
* 🔍 **Advanced Filtering** - Filter tasks by status, priority, date, and search
* 📄 **Pagination** - Efficient pagination for large datasets
* 🗄️ **Database Migrations** - Version-controlled database schema with Alembic
* 📚 **Auto Documentation** - Interactive API documentation with Swagger UI
* 🔒 **Security** - Password hashing, CORS support, and request validation

## Getting Started

1. **Register** a new account at `/auth/register`
2. **Login** to get your JWT token at `/auth/login`
3. **Use the token** in the Authorization header: `Bearer YOUR_TOKEN`
4. **Create and manage** your tasks!

## API Sections

- **Authentication** - User registration and login
- **Tasks** - Task management endpoints
- **Health** - Service health checks
    """,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.debug,
    contact={
        "name": "API Support",
        "email": "support@taskapi.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "authentication",
            "description": "User authentication and authorization operations",
        },
        {
            "name": "tasks",
            "description": "Task management operations. All endpoints require authentication.",
        },
        {
            "name": "health",
            "description": "Health check endpoints for monitoring",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")


@app.get("/", tags=["health"])
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "api_version": "v1",
        "docs": "/docs",
        "redoc": "/redoc",
        "api_base_url": "/api/v1"
    }


@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "api_version": "v1"
    }

