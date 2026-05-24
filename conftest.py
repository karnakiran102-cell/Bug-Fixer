"""
Global Test Configuration & Lifecycle Hooks
===========================================
Handles the isolated database transaction lifecycle and Auth bypassing.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Assuming your main FastAPI app and dependencies are importable here:
from src.main import app 
from users import get_db_session, get_current_user, User
from config import settings

# ----------------------------------------------------------------------------
# 1. DATABASE ISOLATION LIFECYCLE (THE "PRISTINE STATE" HOOK)
# ----------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Spins up the DB Engine once per test session."""
    engine = create_async_engine(settings.db.uri, echo=False)
    # In a real environment, run alembic upgrade head here or rely on Testcontainers
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture()
async def db_session(db_engine):
    """
    Wraps EACH test in an isolated nested transaction (Savepoint).
    Guarantees no data leaks between tests, even when running concurrently.
    """
    async with db_engine.connect() as conn:
        await conn.begin()
        await conn.begin_nested() # Create Savepoint
        
        async_session = AsyncSession(conn, expire_on_commit=False)
        
        # Ensure nested transactions are recreated if the application code commits
        @event.listens_for(async_session.sync_session, "after_transaction_end")
        def end_savepoint(session, transaction):
            if transaction.nested and not transaction._parent.nested:
                conn.sync_connection.begin_nested()

        yield async_session
        
        await async_session.close()
        await conn.rollback() # Rollback EVERYTHING the test did


# ----------------------------------------------------------------------------
# 2. DEPENDENCY INJECTION OVERRIDES & AUTH BYPASSING
# ----------------------------------------------------------------------------

@pytest.fixture
def override_db(db_session):
    """Injects the isolated transaction session into FastAPI."""
    app.dependency_overrides[get_db_session] = lambda: db_session
    yield
    app.dependency_overrides.pop(get_db_session, None)


@pytest.fixture
def bypass_auth(override_db):
    """
    Bypasses the JWT login flow to test protected endpoints directly.
    Injects a mock active User ID into the FastAPI dependency graph.
    """
    mock_user_id = "mock-uuid-1234"
    app.dependency_overrides[get_current_user] = lambda: mock_user_id
    yield mock_user_id
    app.dependency_overrides.pop(get_current_user, None)


# ----------------------------------------------------------------------------
# 3. THE ASYNC TEST CLIENT
# ----------------------------------------------------------------------------

@pytest_asyncio.fixture
async def async_client(override_db):
    """
    Provides an asynchronous HTTP client to hit the FastAPI endpoints
    without actually binding to a port.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client