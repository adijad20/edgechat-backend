"""
Day 5 — Test fixtures. Set test env before app is imported.
Tests always use fixed DB/Redis URLs (same as docker-compose and CI) so they
pass regardless of what's in .env. Start Postgres/Mongo/Redis with:
  docker-compose up -d postgres mongodb redis
"""
import os
from pathlib import Path

# MUST run before any app import so Settings() reads these values
_project_root = Path(__file__).resolve().parent.parent
_env = _project_root / ".env"
if _env.exists():
    from dotenv import load_dotenv
    load_dotenv(_env)
_env_test = _project_root / ".env.test"
if _env_test.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_test)

# Force test DB URLs (overwrite .env) so tests use docker-compose/CI credentials
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-prod")
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ["RATE_LIMIT_REQUESTS"] = "10000"

import asyncio
import pytest
import httpx
from httpx import ASGITransport

from app.main import app




@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped event loop so the same loop runs all tests; avoids asyncpg 'another operation is in progress'."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Async HTTP client against the FastAPI app. We run the app lifespan so init_mongo/init_redis/create_all run (httpx doesn't send ASGI lifespan by default)."""
    transport = ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.fixture
async def auth_headers(client: httpx.AsyncClient):
    """Register a user, login, return headers with Bearer token for use in authenticated requests."""
    email = "testuser@example.com"
    password = "SecurePass123!"
    # Register
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    if r.status_code == 201:
        pass
    elif r.status_code == 400 and "already registered" in (r.json().get("detail") or "").lower():
        # Already exists from previous test run
        pass
    else:
        r.raise_for_status()
    # Login
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_gemini_text(monkeypatch):
    """Replace generate_text where the router uses it so /ai/complete gets the mock."""
    async def _fake(*args, **kwargs):
        return "Mocked AI response"
    monkeypatch.setattr("app.api.v1.ai.generate_text", _fake)


@pytest.fixture
def mock_gemini_chat(monkeypatch):
    """Replace generate_chat where the chat router uses it so send_message gets the mock."""
    async def _fake(*args, **kwargs):
        return "Mocked chat reply"
    monkeypatch.setattr("app.api.v1.chat.generate_chat", _fake)
