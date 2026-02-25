"""JWT utilities (HS256) without external dependencies.

Design goals:
- Works on Win/Linux/macOS
- No hard dependency on python-jose / PyJWT (procurement-friendly minimal base)
- Clear errors for invalid/expired tokens
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


class JWTError(Exception):
    pass


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("utf-8").rstrip("=")


def _json_load(b: bytes) -> Dict[str, Any]:
    return json.loads(b.decode("utf-8"))


def _sign_hs256(message: bytes, secret: str) -> bytes:
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()


def verify_token(
    token: str,
    secret: str,
    *,
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
    leeway_seconds: int = 30,
) -> Dict[str, Any]:
    """Verify HS256 JWT. Returns payload dict on success.

    Validates:
    - signature (HS256)
    - exp (required)
    - nbf (if present)
    - iss/aud (optional if provided)
    """
    if not token or token.count(".") != 2:
        raise JWTError("Malformed token")

    header_b64, payload_b64, sig_b64 = token.split(".", 2)

    try:
        header = _json_load(_b64url_decode(header_b64))
        payload = _json_load(_b64url_decode(payload_b64))
        sig = _b64url_decode(sig_b64)
    except Exception as e:
        raise JWTError("Invalid token encoding") from e

    alg = header.get("alg")
    if alg != "HS256":
        raise JWTError(f"Unsupported alg: {alg}")

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected = _sign_hs256(signing_input, secret)
    if not hmac.compare_digest(expected, sig):
        raise JWTError("Invalid signature")

    now = int(time.time())

    nbf = payload.get("nbf")
    if nbf is not None:
        try:
            nbf_i = int(nbf)
        except Exception:
            raise JWTError("Invalid nbf claim")
        if now + leeway_seconds < nbf_i:
            raise JWTError("Token not yet valid (nbf)")

    exp = payload.get("exp")
    if exp is None:
        raise JWTError("Missing exp claim")
    try:
        exp_i = int(exp)
    except Exception:
        raise JWTError("Invalid exp claim")
    if now - leeway_seconds >= exp_i:
        raise JWTError("Token expired")

    if issuer is not None:
        if payload.get("iss") != issuer:
            raise JWTError("Invalid issuer")

    if audience is not None:
        aud = payload.get("aud")
        if isinstance(aud, str):
            ok = aud == audience
        elif isinstance(aud, list):
            ok = audience in aud
        else:
            ok = False
        if not ok:
            raise JWTError("Invalid audience")

    return payload


def create_token(
    payload: Dict[str, Any],
    secret: str,
    *,
    ttl_seconds: int = 3600,
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
) -> str:
    """Create HS256 JWT for dev/admin tooling."""
    header = {"typ": "JWT", "alg": "HS256"}

    now = int(time.time())
    body = dict(payload)
    body.setdefault("iat", now)
    body.setdefault("nbf", now)
    body.setdefault("exp", now + int(ttl_seconds))
    if issuer is not None:
        body["iss"] = issuer
    if audience is not None:
        body["aud"] = audience

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    sig = _b64url_encode(_sign_hs256(signing_input, secret))
    return f"{header_b64}.{payload_b64}.{sig}"
