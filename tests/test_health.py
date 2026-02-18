"""
Day 5 — Integration tests: Root and health endpoints.
"""
import pytest
import httpx


@pytest.mark.asyncio
async def test_root(client: httpx.AsyncClient):
    r = await client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert "app" in data


@pytest.mark.asyncio
async def test_health_db(client: httpx.AsyncClient):
    r = await client.get("/api/v1/health/db")
    assert r.status_code == 200
    assert r.json().get("database") == "connected"


@pytest.mark.asyncio
async def test_health_mongo(client: httpx.AsyncClient):
    r = await client.get("/api/v1/health/mongo")
    assert r.status_code == 200
    assert r.json().get("mongo") == "connected"


@pytest.mark.asyncio
async def test_health_liveness(client: httpx.AsyncClient):
    """Liveness: process is up."""
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_ready(client: httpx.AsyncClient):
    """Readiness: all dependencies (DB, Mongo, Redis) are up."""
    r = await client.get("/api/v1/health/ready")
    data = r.json()
    checks = data.get("checks", {})
    assert r.status_code == 200, (
        f"health/ready returned {r.status_code}. checks={checks} "
        "— ensure Postgres, Mongo, Redis are running (e.g. docker-compose up -d). "
        "If Redis is on port 16379, set REDIS_URL=redis://localhost:16379/0 in .env.test"
    )
    assert data.get("status") == "ok"
    assert checks.get("database") == "connected"
    assert checks.get("mongo") == "connected"
    assert checks.get("redis") == "connected"
