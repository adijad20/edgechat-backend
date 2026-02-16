"""
AI service: wrapper around Google Gemini API.
Single place for model calls, error handling, and timeouts.
"""
from typing import NoReturn

from google import genai
from google.genai import types

from app.config import settings


class GeminiQuotaExceededError(Exception):
    """Raised when Gemini returns 429 RESOURCE_EXHAUSTED (rate limit / quota)."""
    def __init__(self, message: str, retry_after_seconds: float | None = None):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


# Lazy client: created on first use when API key is set
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Return Gemini client. Raises ValueError if API key is missing."""
    global _client
    if not settings.GEMINI_API_KEY or not settings.GEMINI_API_KEY.strip():
        raise ValueError("GEMINI_API_KEY is not set. Add it to .env (get a key from https://aistudio.google.com/)")
    if _client is None:
        _client = genai.Client(
            api_key=settings.GEMINI_API_KEY.strip(),
        )
    return _client


def _handle_gemini_error(e: Exception) -> NoReturn:
    """
    Inspect a Gemini API exception and raise GeminiQuotaExceededError or RuntimeError.
    Called from generate_text and generate_chat to avoid duplicated handling.
    """
    import re
    msg = str(e).strip() or type(e).__name__
    if "429" in msg or "RESOURCE_EXHAUSTED" in msg.upper() or "quota" in msg.lower():
        retry_s = None
        match = re.search(r"retry in (\d+(?:\.\d+)?)\s*s", msg, re.I)
        if match:
            retry_s = float(match.group(1))
        raise GeminiQuotaExceededError(
            "Gemini rate limit or quota exceeded. Try again in a minute.",
            retry_after_seconds=retry_s,
        ) from e
    if "404" in msg or "NOT_FOUND" in msg.upper():
        raise RuntimeError(
            "Gemini model not found for this API version. Try GEMINI_MODEL=gemini-2.0-flash or gemini-2.5-flash in .env."
        ) from e
    raise RuntimeError(f"Gemini API error: {msg}") from e


async def generate_text(prompt: str) -> str:
    """
    Send a text prompt to Gemini and return the reply text.
    Raises ValueError if API key is missing; returns error message string on API/network errors.
    """
    try:
        client = _get_client()
    except ValueError:
        raise
    model = settings.GEMINI_MODEL
    try:
        response = await client.aio.models.generate_content(
            model=model,
            contents=prompt,
        )
        if response.text:
            return response.text
        return "(No text in response)"
    except Exception as e:
        _handle_gemini_error(e)


async def generate_chat(messages: list[dict[str, str]]) -> str:
    """
    Multi-turn chat: pass list of {"role": "user"|"model", "content": "..."}.
    Returns the model's reply text. Same error handling as generate_text.
    """
    try:
        client = _get_client()
    except ValueError:
        raise
    model_name = settings.GEMINI_MODEL
    contents = [
        types.Content(
            role=m["role"],
            parts=[types.Part.from_text(text=m["content"])],
        )
        for m in messages
    ]
    try:
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=contents,
        )
        if response.text:
            return response.text
        return "(No text in response)"
    except Exception as e:
        _handle_gemini_error(e)
