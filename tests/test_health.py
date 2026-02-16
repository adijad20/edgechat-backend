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
