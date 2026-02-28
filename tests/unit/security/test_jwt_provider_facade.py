from __future__ import annotations

import time

from src.security.auth.jwt_provider import create_token, verify_token, JWTError


def test_jwt_provider_default_internal_roundtrip():
    secret = "test-secret"
    now = int(time.time())
    token = create_token({"sub": "u1", "iat": now}, secret, ttl_seconds=60)
    payload = verify_token(token, secret)
    assert payload["sub"] == "u1"
    assert int(payload["exp"]) >= now


def test_jwt_provider_rejects_malformed():
    secret = "test-secret"
    try:
        verify_token("not-a-jwt", secret)
        assert False, "Expected JWTError"
    except JWTError:
        assert True
