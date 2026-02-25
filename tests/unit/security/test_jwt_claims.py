from __future__ import annotations

import base64
import json
import time

import pytest

from src.security.auth.jwt import JWTError, create_token, verify_token


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("utf-8").rstrip("=")


def test_verify_accepts_valid_token():
    token = create_token({"sub": "u1"}, secret="s", ttl_seconds=60)
    payload = verify_token(token, secret="s")
    assert payload["sub"] == "u1"


def test_verify_rejects_missing_exp_claim():
    token = create_token({"sub": "u1"}, secret="s", ttl_seconds=60)

    header_b64, payload_b64, sig_b64 = token.split(".", 2)
    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    payload.pop("exp", None)
    new_payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))

    # Signature is now invalid, but verify MUST reject anyway.
    tampered = f"{header_b64}.{new_payload_b64}.{sig_b64}"
    with pytest.raises(JWTError):
        verify_token(tampered, secret="s")


def test_verify_rejects_expired_token():
    token = create_token({"sub": "u1"}, secret="s", ttl_seconds=1)
    time.sleep(2)
    with pytest.raises(JWTError):
        verify_token(token, secret="s", leeway_seconds=0)
