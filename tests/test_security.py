"""
Day 5 — Unit tests: password hashing and JWT (app.core.security).
"""

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_hash_password_returns_str():
    h = hash_password("hello")
    assert isinstance(h, str)
    assert len(h) > 0
    assert h != "hello"


def test_verify_password_match():
    h = hash_password("secret123")
    assert verify_password("secret123", h) is True


def test_verify_password_wrong():
    h = hash_password("secret123")
    assert verify_password("wrong", h) is False
    assert verify_password("secret1234", h) is False


def test_create_access_token_returns_str():
    token = create_access_token(user_id=42)
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token_returns_str():
    token = create_refresh_token(user_id=42)
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_token_valid_access():
    token = create_access_token(user_id=99)
    payload = decode_token(token)
    assert payload is not None
    assert payload.get("sub") == "99"
    assert payload.get("type") == "access"
    assert "exp" in payload


def test_decode_token_valid_refresh():
    token = create_refresh_token(user_id=100)
    payload = decode_token(token)
    assert payload is not None
    assert payload.get("sub") == "100"
    assert payload.get("type") == "refresh"


def test_decode_token_invalid_returns_none():
    assert decode_token("not-a-jwt") is None
    assert decode_token("") is None
    assert decode_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIn0.fake") is None
