"""JWT provider facade.

Single entrypoint for JWT operations across the codebase.

Design:
- Default backend: "internal" (no external deps).
- Optional backend: "jose" (python-jose), loaded lazily to avoid hard dependency.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Literal

Backend = Literal["internal", "jose"]


class JWTError(Exception):
    pass


def _load_backend(backend: Backend):
    if backend == "internal":
        from . import jwt as impl
        return impl
    if backend == "jose":
        try:
            from . import jwt_jose as impl
        except Exception as e:  # pragma: no cover
            raise JWTError(
                "JWT backend 'jose' requested but dependency is missing or failed to import. "
                "Install 'python-jose' or switch backend to 'internal'."
            ) from e
        return impl
    raise JWTError(f"Unknown JWT backend: {backend}")


def create_token(
    payload: Dict[str, Any],
    secret: str,
    *,
    ttl_seconds: int = 3600,
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
    backend: Backend = "internal",
) -> str:
    impl = _load_backend(backend)
    try:
        return impl.create_token(
            payload,
            secret,
            ttl_seconds=ttl_seconds,
            issuer=issuer,
            audience=audience,
        )
    except Exception as e:
        # Normalize errors to a single type
        raise JWTError(str(e)) from e


def verify_token(
    token: str,
    secret: str,
    *,
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
    leeway_seconds: int = 30,
    backend: Backend = "internal",
) -> Dict[str, Any]:
    impl = _load_backend(backend)
    try:
        return impl.verify_token(
            token,
            secret,
            issuer=issuer,
            audience=audience,
            leeway_seconds=leeway_seconds,
        )
    except Exception as e:
        raise JWTError(str(e)) from e
