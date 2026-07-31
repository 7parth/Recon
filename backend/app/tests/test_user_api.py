"""app/tests/test_user_api.py — Async tests for user profile and settings endpoints."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.database import dispose_engine


@pytest_asyncio.fixture(scope="module")
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    await dispose_engine()


@pytest.mark.asyncio(loop_scope="module")
async def test_get_and_update_user_profile(async_client: AsyncClient):
    response = await async_client.get("/api/v1/user/profile")
    assert response.status_code == 200
    data = response.json()
    assert "first_name" in data

    update_payload = {
        "first_name": "Parth",
        "last_name": "Waradkar",
        "email": "parth@example.com",
    }
    update_res = await async_client.put("/api/v1/user/profile", json=update_payload)
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["first_name"] == "Parth"
    assert updated_data["last_name"] == "Waradkar"
    assert updated_data["email"] == "parth@example.com"


@pytest.mark.asyncio(loop_scope="module")
async def test_get_and_update_user_settings(async_client: AsyncClient):
    response = await async_client.get("/api/v1/user/settings")
    assert response.status_code == 200
    data = response.json()
    assert "match_threshold" in data

    update_payload = {
        "match_threshold": 75,
        "auto_apply": True,
    }
    update_res = await async_client.put("/api/v1/user/settings", json=update_payload)
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["match_threshold"] == 75
    assert updated_data["auto_apply"] is True
