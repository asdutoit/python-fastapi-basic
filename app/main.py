from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from app.config import settings
from app.database import engine, Base
from app.api import auth, tasks
from app.middleware.rate_limit import InMemoryRateLimiter
from app.core.logging import setup_logging, get_logger
from app.core.tracing import setup_tracing, instrument_app, instrument_sqlalchemy

# Set up logging
setup_logging()
logger = get_logger(__name__)

# Set up tracing
if not settings.debug:  # Only enable tracing in production
    setup_tracing()

Base.metadata.create_all(bind=engine)

# Instrument SQLAlchemy for tracing
if not settings.debug:
    instrument_sqlalchemy(engine)

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

# Add rate limiting middleware (before CORS)
if not settings.debug:  # Only enable in production
    app.add_middleware(
        InMemoryRateLimiter,
        requests_per_minute=settings.rate_limit_requests
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Add tracing instrumentation
if not settings.debug:
    instrument_app(app)


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
    """
    Comprehensive health check endpoint for monitoring systems.
    
    Returns:
    - Service status and basic information
    - Database connectivity status
    - API version information
    """
    from app.database import engine
    
    # Check database connectivity
    db_status = "healthy"
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Overall health status
    overall_status = "healthy" if db_status == "healthy" else "unhealthy"
    
    return {
        "status": overall_status,
        "service": settings.app_name,
        "version": settings.app_version,
        "api_version": "v1",
        "database": db_status,
        "debug": settings.debug,
        "features": {
            "registration": settings.enable_registration,
            "password_reset": settings.enable_password_reset
        }
    }


@app.get("/health/live", tags=["health"])
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    Simple check to verify the application is running.
    """
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"])
async def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    Checks if the application is ready to serve traffic.
    """
    from app.database import engine
    
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not ready", "reason": str(e)}

