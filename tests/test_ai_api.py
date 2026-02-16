"""
Day 5 — Integration tests: AI complete endpoint (Gemini mocked).
"""
import pytest
import httpx


@pytest.mark.asyncio
async def test_ai_complete_mocked(client: httpx.AsyncClient, mock_gemini_text):
    r = await client.post(
        "/api/v1/ai/complete",
        json={"prompt": "Hello"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("text") == "Mocked AI response"
