"""
Integration Tests: User Directory and Registration
==================================================
Hits the API endpoints and verifies Database state.
"""

import pytest
from sqlalchemy import select
from users import User, AccountStatus

pytestmark = pytest.mark.asyncio

@pytest.mark.integration
async def test_create_user_registration(async_client, db_session):
    """
    Tests that a POST to /users successfully creates a DB record.
    """
    # 1. Arrange: Define the payload
    payload = {
        "email": "integration@test.com",
        "password": "secure_password_123"
    }

    # 2. Act: Hit the FastAPI endpoint
    response = await async_client.post("/api/v1/users", json=payload)

    # 3. Assert HTTP Layer
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert "password_hash" not in data # Ensure DTO strips secrets

    # 4. Assert Database Layer: Verify record was actually created
    stmt = select(User).where(User.email == payload["email"])
    result = await db_session.execute(stmt)
    user_record = result.scalar_one_or_none()
    
    assert user_record is not None
    assert user_record.status == AccountStatus.PENDING

    # Note: Because of `conftest.py`, this DB record will instantly vanish after this test finishes!