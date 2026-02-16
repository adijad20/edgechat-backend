"""
Day 5 — Integration tests: Auth API (register, login, refresh, me).
"""
import uuid

import pytest
import httpx


@pytest.mark.asyncio
async def test_register_and_login(client: httpx.AsyncClient):
    # Use a unique email so the test passes even if DB already has data from a previous run
    email = f"newuser_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePass123!"
    # Register
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data

    # Login
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_login_invalid_password(client: httpx.AsyncClient, auth_headers):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@example.com", "password": "WrongPass"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client: httpx.AsyncClient):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401  # No Bearer token (FastAPI HTTPBearer returns 401)


@pytest.mark.asyncio
async def test_me_returns_user(client: httpx.AsyncClient, auth_headers):
    r = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "email" in data
    assert data["email"] == "testuser@example.com"


@pytest.mark.asyncio
async def test_refresh_token(client: httpx.AsyncClient, auth_headers):
    # Login to get refresh_token
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@example.com", "password": "SecurePass123!"},
    )
    assert r.status_code == 200
    refresh_token = r.json()["refresh_token"]

    r = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()
    assert "refresh_token" in r.json()


@pytest.mark.asyncio
async def test_usage_me(client: httpx.AsyncClient, auth_headers):
    r = await client.get("/api/v1/usage/me", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "total_requests" in data
    assert "requests_last_24h" in data
    assert "requests_last_7d" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: httpx.AsyncClient):
    email = "dup@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePass123!"},
    )
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "OtherPass456!"},
    )
    assert r.status_code == 400
    assert "already" in (r.json().get("detail") or "").lower()
