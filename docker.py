"""
Production-Ready Docker Infrastructure Generator
================================================
Role: Principal DevOps Engineer & Containerization Expert

This script scaffolds a highly secure, multi-stage, non-root Docker 
environment optimized for Python/FastAPI applications.

Directory Blueprint Generated:
------------------------------
/backend
 ├── Dockerfile                 # Production multi-stage Dockerfile
 ├── docker-compose.yml         # Local development orchestration
 ├── .dockerignore              # Build context exclusions
 ├── docker-entrypoint.sh       # Pre-flight checks and migrations
 └── /src                       # Application source code
"""

import os
import stat

# ============================================================================
# 1. MULTI-STAGE DOCKERFILE (Production & Security Optimized)
# ============================================================================
DOCKERFILE_CONTENT = """\
# ==========================================
# STAGE 1: Builder (Dependencies & Compilation)
# ==========================================
FROM python:3.11-slim AS builder

# Prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install system build dependencies (e.g., for psycopg2, cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc \\
    libpq-dev \\
    python3-dev \\
    && rm -rf /var/lib/apt/lists/*

# LAYER CACHING: Copy only requirements first to cache dependency installation
COPY requirements.txt .

# Build wheels instead of installing to easily copy them to the runner stage
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt


# ==========================================
# STAGE 2: Runner (Minimal & Secure Runtime)
# ==========================================
FROM python:3.11-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install ONLY required runtime dependencies (e.g., netcat for entrypoint, libpq for postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \\
    libpq5 \\
    curl \\
    netcat-traditional \\
    && rm -rf /var/lib/apt/lists/*

# SECURITY: Create a dedicated non-root user and group
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Install python dependencies from the builder's wheels
COPY --from=builder /build/wheels /wheels
COPY --from=builder /build/requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy the pre-flight entrypoint script
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Copy the actual application source code
COPY src/ ./src/

# SECURITY: Transfer ownership to the non-root user
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# HEALTHCHECK: Verify the FastAPI app is actively responding
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \\
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Use entrypoint script to run migrations/wait for DB before starting app
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

# ============================================================================
# 2. DOCKER COMPOSE (Local Orchestration & Live-Reloading)
# ============================================================================
DOCKER_COMPOSE_CONTENT = """\
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: dev_backend_api
    ports:
      - "8000:8000"
    volumes:
      # LIVE RELOAD: Mount the local src directory into the container
      - ./src:/app/src
    environment:
      - ENVIRONMENT=development
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_USER=${DB_USER:-postgres}
      - DB_PASSWORD=${DB_PASSWORD:-postgres}
      - DB_NAME=${DB_NAME:-app_db}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    # Override CMD for local dev to enable Uvicorn's hot-reloading
    command: ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    networks:
      - backend-network

  postgres:
    image: postgres:15-alpine
    container_name: dev_postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
      POSTGRES_DB: ${DB_NAME:-app_db}
    volumes:
      # PERSISTENCE: Retain database data across container restarts
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres} -d ${DB_NAME:-app_db}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend-network

  redis:
    image: redis:7-alpine
    container_name: dev_redis
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend-network

volumes:
  pgdata:
  redisdata:

networks:
  backend-network:
    driver: bridge
"""

# ============================================================================
# 3. DOCKER IGNORE (Context Optimization & Secret Protection)
# ============================================================================
DOCKER_IGNORE_CONTENT = """\
# Git
.git
.gitignore

# Secrets & Local Envs
.env
.env.*
*.pem
*.key

# Python & Virtual Environments
venv/
env/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
dist/
wheels/
*.egg-info/
*.egg

# Tests & Coverage
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/
.mypy_cache/

# Docker & Docs
docker-compose.yml
README.md
docker.py
"""

# ============================================================================
# 4. ENTRYPOINT SCRIPT (Pre-flight checks)
# ============================================================================
ENTRYPOINT_CONTENT = """\
#!/bin/bash
set -e

# 1. Wait for the database to be actively accepting connections
if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
    echo "⏳ Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.5
    done
    echo "✅ PostgreSQL is up and running!"
fi

# 2. Run Database Migrations securely before boot
# Uncomment below when Alembic is configured:
# echo "🚀 Running database migrations..."
# alembic upgrade head

# 3. Execute the CMD instruction passed by the Dockerfile
echo "🔥 Starting application..."
exec "$@"
"""

if __name__ == "__main__":
    print("Initializing Docker Infrastructure...")
    
    files = {
        "Dockerfile": DOCKERFILE_CONTENT,
        "docker-compose.yml": DOCKER_COMPOSE_CONTENT,
        ".dockerignore": DOCKER_IGNORE_CONTENT,
        "docker-entrypoint.sh": ENTRYPOINT_CONTENT
    }
    
    for filename, content in files.items():
        with open(filename, "w", newline='\n', encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ Generated {filename}")
        
        # Make the bash script executable locally if on Unix
        if filename == "docker-entrypoint.sh" and os.name == 'posix':
            st = os.stat(filename)
            os.chmod(filename, st.st_mode | stat.S_IEXEC)
            
    print("\nInfrastructure successfully generated. Run `docker-compose up --build` to start.")