# ===== Stage 1: Build dependencies =====
FROM python:3.13.6-alpine3.21 AS builder

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

# Install build dependencies
RUN apk add --no-cache --virtual .build-deps \
        gcc \
        musl-dev \
        libffi-dev \
        openssl-dev \
    && pip install --no-cache-dir --upgrade -r /code/requirements.txt \
    && apk del .build-deps

COPY ./app /code/app


# ===== Stage 2: Final lightweight runtime =====
FROM python:3.13.6-alpine3.21

WORKDIR /code

# Copy installed packages from builder stage
COPY --from=builder /usr/local /usr/local
COPY --from=builder /code/app /code/app

# If your app needs runtime libraries (e.g., libffi, openssl), install them here
RUN apk add --no-cache \
        libffi \
        openssl

EXPOSE 80

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]