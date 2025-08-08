# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Task Management API built with FastAPI as a learning project for modern Python API development. The project follows a phased development approach, building from basic setup to a production-ready API suitable for Google Apigee integration.

## Current Development Phase

Track progress through the 10 development phases outlined in the project plan. Each phase builds upon the previous one.

## Common Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

### Running the Application
```bash
# Development server with auto-reload
uvicorn app.main:app --reload --port 8000

# Access API documentation
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### Database Operations

#### Alembic Migrations
```bash
# Check current migration status
alembic current

# Create a new migration automatically from model changes
alembic revision --autogenerate -m "Description of changes"

# Apply all migrations to latest version
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>

# Downgrade one revision
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision_id>

# Show migration history
alembic history

# Show SQL that would be executed (without applying)
alembic upgrade head --sql
```

#### Manual Database Operations
```bash
# Initialize database (SQLite for development)
python -c "from app.database import init_db; init_db()"

# For PostgreSQL in production
# Set DATABASE_URL environment variable
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_tasks.py -v

# Run tests matching pattern
pytest -k "test_create"
```

### Code Quality
```bash
# Format code with black
black app/ tests/

# Lint with ruff
ruff check app/ tests/

# Type checking with mypy
mypy app/

# Run all quality checks
black . && ruff check . && mypy app/
```

### Docker Operations
```bash
# Build and run with docker-compose
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f
```

## Project Architecture

### Directory Structure
```
task-api/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Settings management (environment variables)
│   ├── database.py          # SQLAlchemy database setup
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── user.py          # User model with relationships
│   │   └── task.py          # Task model with user foreign key
│   ├── schemas/             # Pydantic models for validation
│   │   ├── user.py          # UserCreate, UserResponse, UserUpdate
│   │   └── task.py          # TaskCreate, TaskResponse, TaskUpdate
│   ├── crud/                # Database operations layer
│   │   ├── user.py          # User CRUD operations
│   │   └── task.py          # Task CRUD with user filtering
│   ├── api/                 # API route handlers
│   │   ├── auth.py          # Login, register, token refresh
│   │   ├── users.py         # User management endpoints
│   │   └── tasks.py         # Task CRUD endpoints
│   └── core/                # Core utilities
│       ├── security.py      # JWT, password hashing
│       └── dependencies.py  # Shared dependencies (get_current_user)
└── tests/                   # Test suite with fixtures
```

### Key Design Patterns

1. **Dependency Injection**: Use FastAPI's `Depends()` for database sessions and authentication
2. **Schema Separation**: Keep Pydantic schemas separate from SQLAlchemy models
3. **CRUD Pattern**: Isolate database operations in dedicated CRUD modules
4. **JWT Authentication**: Stateless authentication with access tokens
5. **Async Support**: Use async/await for database operations when appropriate

## Database Schema

### User Model
- id: UUID primary key
- email: Unique, indexed
- username: Unique
- hashed_password: Bcrypt hash
- is_active: Boolean
- created_at: Timestamp

### Task Model
- id: UUID primary key
- title: String, required
- description: Text, optional
- completed: Boolean, default False
- user_id: Foreign key to User
- created_at: Timestamp
- updated_at: Timestamp (auto-update)

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - Login with email/password
- `GET /auth/me` - Get current user (protected)

### Users
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update current user
- `GET /users/{user_id}` - Get user by ID (admin only)

### Tasks
- `GET /tasks` - List user's tasks (paginated)
- `POST /tasks` - Create new task
- `GET /tasks/{task_id}` - Get specific task
- `PUT /tasks/{task_id}` - Update task
- `DELETE /tasks/{task_id}` - Delete task

## Development Guidelines

### When Adding New Features
1. Create SQLAlchemy model in `app/models/`
2. Create Pydantic schemas in `app/schemas/`
3. Implement CRUD operations in `app/crud/`
4. Add API endpoints in `app/api/`
5. Write tests in `tests/`

### Testing Strategy
- Use pytest fixtures for database and client setup
- Test both success and error cases
- Mock external dependencies
- Use test database separate from development

### Security Considerations
- Never store plain text passwords
- Use environment variables for secrets
- Implement proper CORS for production
- Add rate limiting for public endpoints
- Validate all inputs with Pydantic

### Apigee Integration Preparation
- Ensure all endpoints return consistent JSON responses
- Implement proper HTTP status codes
- Add OpenAPI documentation tags
- Include health check endpoint at `/health`
- Design with API gateway policies in mind

## Environment Variables

Create `.env` file for local development:
```
DATABASE_URL=sqlite:///./task_api.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

For production, use PostgreSQL:
```
DATABASE_URL=postgresql://user:password@localhost/dbname
```

## Common Issues and Solutions

1. **Import Errors**: Ensure running from project root with `python -m` or proper PYTHONPATH
2. **Database Migrations**: For schema changes, drop and recreate tables in development
3. **Authentication Failures**: Check JWT secret key and token expiration settings
4. **CORS Issues**: Configure CORS middleware in main.py for frontend integration

## Phase Completion Checklist

When completing each development phase:
1. All code follows the established patterns
2. Tests are written and passing
3. Documentation is updated
4. Code is formatted and linted
5. Functionality is manually tested via Swagger UI