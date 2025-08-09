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

The project includes a comprehensive test suite with 88%+ coverage across multiple categories.

#### Test Categories

1. **Unit Tests** (`test_crud.py`): Test CRUD operations in isolation
2. **Integration Tests** (`test_auth.py`, `test_tasks.py`): Test complete API workflows
3. **Security Tests** (`test_security.py`): Test authentication, authorization, and security
4. **Performance Tests** (`test_performance.py`): Test response times and scalability

#### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test categories
pytest tests/test_crud.py -v        # Unit tests
pytest tests/test_auth.py -v        # Authentication tests
pytest tests/test_tasks.py -v       # Task API tests
pytest tests/test_security.py -v    # Security tests
pytest tests/test_performance.py -v # Performance tests

# Run tests by markers
pytest -m unit                      # Only unit tests
pytest -m security                  # Only security tests
pytest -m performance               # Only performance tests
pytest -m "not slow"                # Skip slow tests

# Coverage reporting
pytest --cov=app --cov-report=html  # Generate HTML coverage report
pytest --cov=app --cov-report=term-missing  # Terminal coverage report

# Run specific test patterns
pytest -k "test_create"             # Tests containing "create"
pytest -k "auth and not security"   # Auth tests excluding security

# Parallel testing (install pytest-xdist first)
pytest -n auto                      # Run tests in parallel

# Test with different output formats
pytest --tb=short                   # Short traceback format
pytest --tb=no                      # No traceback
pytest -v                           # Verbose output
pytest -q                           # Quiet output
```

#### Test Database

Tests use isolated SQLite databases to prevent interference:

- Authentication tests: `test_auth.db`
- Task tests: `test_tasks.db`
- CRUD tests: `test_crud.db`
- Security tests: `test_security.db`
- Performance tests: `test_performance.db`

Each test file automatically creates and destroys its database for isolation.

#### Test Fixtures

The test suite includes reusable fixtures:

- `db_session`: Clean database session for each test
- `sample_user`: Pre-created user for testing
- `authenticated_user`: User with valid JWT token
- `auth_headers`: Authorization headers for API calls
- `test_user`: Complete user setup with token

#### Performance Benchmarks

Performance tests establish benchmarks for:

- **Login**: < 1.0 second
- **Registration**: < 2.0 seconds
- **Token verification**: < 0.5 seconds
- **Task creation**: < 0.5 seconds
- **Bulk operations**: < 50ms average per task
- **Search/filtering**: < 0.5 seconds
- **Pagination**: < 0.5 seconds regardless of position

#### Security Test Coverage

Security tests verify:

- Password hashing and complexity requirements
- JWT token creation, verification, and expiration
- Token tampering detection
- Authentication requirement enforcement
- User data isolation
- SQL injection prevention
- XSS handling
- Input length validation
- Brute force protection

#### Continuous Integration

For CI/CD pipelines, use:

```bash
# Fail if coverage drops below 85%
pytest --cov=app --cov-fail-under=85

# Generate JUnit XML for CI systems
pytest --junit-xml=test-results.xml

# Run with timeout to prevent hanging tests
pytest --timeout=300
```

#### Adding New Tests

When adding features, ensure you add tests to the appropriate category:

1. **Unit tests**: Test individual functions/methods in isolation
2. **Integration tests**: Test complete API workflows
3. **Security tests**: Test security implications of new features
4. **Performance tests**: Test performance impact

Follow the existing patterns and use provided fixtures for consistency.

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

## Google Apigee Integration

The API is fully integrated with Google Apigee for enterprise API management. See `APIGEE_INTEGRATION_GUIDE.md` for detailed setup instructions.

### Quick Apigee Deployment

1. **Configure Environment**

   ```bash
   cd apigee/
   cp .env.template .env
   # Edit .env with your Apigee credentials and backend URL
   ```

2. **Deploy to Apigee**

   ```bash
   ./deploy.sh test your-apigee-org
   ```

3. **Test Integration**
   ```bash
   export API_KEY=your-generated-api-key
   node test-proxy.js
   ```

### Apigee Features Included

- **JWT Authentication** - Seamless token verification
- **API Key Management** - Rate limiting and analytics per key
- **CORS Handling** - Browser-compatible cross-origin requests
- **Rate Limiting** - 100 requests/minute with spike arrest protection
- **Request/Response Transformation** - Header management and cleanup
- **Health Monitoring** - Backend health checks and failover
- **Analytics Integration** - Request tracking and performance monitoring

### Apigee Proxy Endpoints

- **Health**: `https://your-org-env.apigee.net/task-api/v1/health`
- **Authentication**: `https://your-org-env.apigee.net/task-api/v1/api/v1/auth/*`
- **Tasks**: `https://your-org-env.apigee.net/task-api/v1/api/v1/tasks/*`
- **Documentation**: `https://your-org-env.apigee.net/task-api/v1/docs`

## Phase Completion Checklist

When completing each development phase:

1. All code follows the established patterns
2. Tests are written and passing
3. Documentation is updated
4. Code is formatted and linted
5. Functionality is manually tested via Swagger UI
6. **Apigee integration tested** (if deploying to production)
