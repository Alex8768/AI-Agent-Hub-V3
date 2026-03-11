"""Durable record key builders extracted from answer service."""

from __future__ import annotations


def durable_approval_record_key(*, session_id: str) -> str:
    sid = str(session_id or "default")
    return f"session:{sid}:durable:approval_session_record"


def durable_idempotency_record_key(*, session_id: str, idempotency_key: str = "") -> str:
    sid = str(session_id or "default")
    ikey = str(idempotency_key or "").strip()
    if ikey:
        return f"session:{sid}:durable:idempotency_record:{ikey}"
    return f"session:{sid}:durable:idempotency_record:last"
