# ===== Stage 1: Build dependencies =====
# Use python:3.12-slim-bullseye for better ARM64 compatibility
FROM python:3.12-slim-bullseye AS builder

WORKDIR /code

# Install system dependencies for building Python packages
# Use alternative approach for hash sum mismatches on ARM64
RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* \
    && apt-get update --fix-missing \
    && for i in 1 2 3; do apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl && break || sleep 5; done \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Copy and install Python dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --user -r /code/requirements.txt

# Copy application code
COPY ./app /code/app
COPY ./alembic /code/alembic
COPY ./alembic.ini /code/alembic.ini


# ===== Stage 2: Production runtime =====
FROM python:3.12-slim-bullseye AS production

WORKDIR /code

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies
RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* \
    && apt-get update --fix-missing \
    && for i in 1 2 3; do apt-get install -y --no-install-recommends \
        libpq5 \
        curl && break || sleep 5; done \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Copy Python packages and application from builder
COPY --from=builder /root/.local /home/appuser/.local
COPY --from=builder /code/app /code/app
COPY --from=builder /code/alembic /code/alembic
COPY --from=builder /code/alembic.ini /code/alembic.ini

# Make sure scripts in .local are usable
ENV PATH="/home/appuser/.local/bin:$PATH"

# Create directories and set permissions
RUN mkdir -p /code/logs \
    && chown -R appuser:appuser /code

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Production command with proper configuration
# Note: Using single worker for Prometheus metrics compatibility
# For multi-worker setup, use gunicorn with uvicorn workers or implement shared metrics
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--access-log"]