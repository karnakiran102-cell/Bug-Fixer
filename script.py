"""
Platform Engineering Script Generator
=====================================
Role: Principal Platform Engineer

This script scaffolds a production-ready, strictly formatted `scripts/` 
directory containing essential automation utilities for DX, CI/CD, and cron.
"""

import os
import stat
from pathlib import Path

# ============================================================================
# BASH BOILERPLATE (Strict Mode & Colors)
# ============================================================================
BASH_BASE = """#!/usr/bin/env bash
# Strict mode: Fail on error, unassigned variables, and piped failures
set -euo pipefail

# Color formatting for terminal output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

"""

# ============================================================================
# 1. THE LOCAL SETUP SCRIPT (Bootstrapper)
# ============================================================================
SETUP_LOCAL_CONTENT = BASH_BASE + """\
log_info "Starting local environment bootstrap..."

# 1. Idempotent Environment Setup
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        log_info "Copied .env.example to .env. Please fill in any missing secrets!"
    else
        log_warn ".env.example missing. Skipping .env creation."
    fi
else
    log_info ".env file already exists. Skipping."
fi

# 2. Dependency Check (Docker)
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker Desktop and try again."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    log_error "Docker Compose is not installed."
    exit 1
fi

# 3. Spin up local containers
log_info "Starting Docker containers..."
# Use `docker compose` or `docker-compose` depending on the system
if command -v docker-compose &> /dev/null; then
    docker-compose up -d --build
else
    docker compose up -d --build
fi

# 4. Install local dependencies (Stub for Python/Node)
if [ -f "requirements.txt" ] && command -v pip &> /dev/null; then
    log_info "Installing Python dependencies locally for IDE support..."
    pip install -r requirements.txt > /dev/null
fi

log_info "Bootstrap complete! System is running in the background."
"""

# ============================================================================
# 2. THE DATABASE UTILITY SCRIPT (db-reset)
# ============================================================================
DB_RESET_CONTENT = BASH_BASE + """\
log_info "Initializing database reset utility..."

# ============================================================================
# 🚨 PRODUCTION SAFETY GUARD 🚨
# ============================================================================
if [[ "${NODE_ENV:-}" == "production" || "${APP_ENV:-}" == "prod" || "${ENVIRONMENT:-}" == "production" ]]; then
    log_error "CATASTROPHIC ABORT: You are attempting to reset the database in a PRODUCTION environment!"
    exit 1
fi

log_warn "This will DROP all tables, run migrations, and inject seed data."
read -p "Are you absolutely sure you want to destroy local data? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Aborted by user."
    exit 0
fi

log_info "Dropping schema and applying migrations..."
# Example for Alembic (Python). If using Prisma, replace with: npx prisma migrate reset --force
docker-compose exec -T api bash -c "alembic downgrade base || true"
docker-compose exec -T api bash -c "alembic upgrade head"

log_info "Executing seed scripts..."
# Example for Python seed script. If using Node: npm run seed
docker-compose exec -T api bash -c "python -m src.database.seed || echo 'No seed script found.'"

log_info "Database has been successfully reset and seeded."
"""

# ============================================================================
# 3. THE CI/CD HEALTH CHECK SCRIPT
# ============================================================================
HEALTH_CHECK_CONTENT = BASH_BASE + """\
TARGET_URL=${1:-"http://localhost:8000/health"}
MAX_RETRIES=${2:-30}
SLEEP_INTERVAL=${3:-2}

log_info "Pinging $TARGET_URL to check for readiness..."

count=0
while ! curl -s -f "$TARGET_URL" > /dev/null; do
    count=$((count+1))
    if [ $count -ge "$MAX_RETRIES" ]; then
        log_error "Timeout: Service at $TARGET_URL did not become healthy within $((MAX_RETRIES * SLEEP_INTERVAL)) seconds."
        # Print Docker logs for debugging in CI
        log_warn "Dumping recent API logs for debugging:"
        docker-compose logs --tail=50 api || true
        exit 1
    fi
    log_warn "Service unavailable. Retrying in $SLEEP_INTERVAL seconds... ($count/$MAX_RETRIES)"
    sleep "$SLEEP_INTERVAL"
done

log_info "Service is up and healthy! Proceeding with integration tests."
"""

# ============================================================================
# 4. THE MAINTENANCE SCRIPT (cron)
# ============================================================================
CLEANUP_LOGS_CONTENT = BASH_BASE + """\
LOG_DIR=${1:-"/var/log/app"}
DAYS_TO_KEEP=${2:-30}

log_info "Starting routine cleanup task..."

# 1. Prune old log files
if [ -d "$LOG_DIR" ]; then
    log_info "Removing logs older than $DAYS_TO_KEEP days in $LOG_DIR..."
    find "$LOG_DIR" -type f -name "*.log" -mtime +"$DAYS_TO_KEEP" -exec rm -f {} \\;
else
    log_warn "Log directory $LOG_DIR does not exist. Skipping."
fi

# 2. Clear Python __pycache__ / temp files safely
log_info "Clearing local cache directories..."
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# 3. Database Session Cleanup (Stub)
# Assuming an abstracted python script handles expiring sessions:
# docker-compose exec -T api python -m src.scripts.purge_expired_sessions || true

log_info "Maintenance cleanup completed successfully."
"""

# ============================================================================
# GENERATOR LOGIC
# ============================================================================

def create_script(filepath: str, content: str):
    """Writes the bash content and applies execution permissions."""
    path = Path(filepath)
    
    # Ensure parent directories exist
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write content
    with open(path, "w", newline='\n', encoding="utf-8") as f:
        f.write(content)
        
    # Apply `chmod +x` equivalent in Python
    if os.name == 'posix':
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IEXEC)
        
    print(f"  ✓ Created & made executable: {filepath}")

if __name__ == "__main__":
    print("Initializing Scripts Architecture...")
    
    # Define the routing mapping
    files_to_generate = {
        "scripts/dev/setup-local.sh": SETUP_LOCAL_CONTENT,
        "scripts/dev/db-reset.sh": DB_RESET_CONTENT,
        "scripts/ci/health-check.sh": HEALTH_CHECK_CONTENT,
        "scripts/cron/cleanup-logs.sh": CLEANUP_LOGS_CONTENT
    }
    
    for filepath, content in files_to_generate.items():
        create_script(filepath, content)
        
    print("\\n🚀 Scripts successfully generated!")
    print("Note: If you move these files to a Linux/Mac machine via a zip or Git without preserving modes,")
    print("you may need to run `chmod +x scripts/**/*.sh` manually.")