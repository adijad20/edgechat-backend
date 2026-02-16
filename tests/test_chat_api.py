"""
Day 5 — Integration tests: Chat API (conversations, messages). Gemini mocked for send_message.
"""
import pytest
import httpx


@pytest.mark.asyncio
async def test_create_and_list_conversations(client: httpx.AsyncClient, auth_headers):
    r = await client.post("/api/v1/chat/conversations", headers=auth_headers)
    assert r.status_code == 201
    conv_id = r.json()["id"]
    assert len(conv_id) > 0

    r = await client.get("/api/v1/chat/conversations", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "conversations" in data
    assert "has_more" in data
    assert any(c["id"] == conv_id for c in data["conversations"])


@pytest.mark.asyncio
async def test_send_message_and_get_messages(client: httpx.AsyncClient, auth_headers, mock_gemini_chat):
    r = await client.post("/api/v1/chat/conversations", headers=auth_headers)
    assert r.status_code == 201
    conv_id = r.json()["id"]

    r = await client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        headers=auth_headers,
        json={"content": "Hello AI"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["user_message"]["content"] == "Hello AI"
    assert data["model_message"]["content"] == "Mocked chat reply"

    r = await client.get(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "messages" in data
    assert "has_more" in data
    assert len(data["messages"]) >= 2


@pytest.mark.asyncio
async def test_delete_conversation(client: httpx.AsyncClient, auth_headers):
    r = await client.post("/api/v1/chat/conversations", headers=auth_headers)
    conv_id = r.json()["id"]

    r = await client.delete(f"/api/v1/chat/conversations/{conv_id}", headers=auth_headers)
    assert r.status_code == 204

    r = await client.get(f"/api/v1/chat/conversations/{conv_id}/messages", headers=auth_headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_chat_endpoints_require_auth(client: httpx.AsyncClient):
    r = await client.post("/api/v1/chat/conversations")
    assert r.status_code == 401  # No Bearer token
    r = await client.get("/api/v1/chat/conversations")
    assert r.status_code == 401
