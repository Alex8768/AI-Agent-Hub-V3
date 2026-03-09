from __future__ import annotations

from typing import TypedDict

DEFAULT_MODE = "deny_by_default"
DEFAULT_ALLOWED_TOOLS = ["search"]
DEFAULT_DENIED_TOOLS = ["shell"]
DEFAULT_ALLOWED_PATH_PREFIXES = ["/workspace"]
DEFAULT_ALLOW_NETWORK = False
DEFAULT_MAX_EXECUTION_SECONDS = 30

MAX_LIST_ITEMS = 128
MAX_EXECUTION_SECONDS_CAP = 600


class ToolSafetySandboxPolicy(TypedDict):
    mode: str
    allowed_tools: list[str]
    denied_tools: list[str]
    allowed_path_prefixes: list[str]
    allow_network: bool
    max_execution_seconds: int


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_bool(value: object, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return bool(default)


def _normalize_int(value: object, *, default: int, min_value: int, max_value: int) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except Exception:
        parsed = int(default)
    return max(min_value, min(int(parsed), max_value))


def _normalize_string_list(
    values: object,
    *,
    default: list[str],
) -> list[str]:
    items = list(values) if isinstance(values, list) else list(default)
    normalized: list[str] = []
    for raw in items:
        value = _normalize_string(raw)
        if not value:
            continue
        normalized.append(value)
    # deterministic de-duplication + stable order
    return sorted(set(normalized))[:MAX_LIST_ITEMS]


def build_tool_safety_sandbox_policy(
    *,
    mode: object = DEFAULT_MODE,
    allowed_tools: object = None,
    denied_tools: object = None,
    allowed_path_prefixes: object = None,
    allow_network: object = DEFAULT_ALLOW_NETWORK,
    max_execution_seconds: object = DEFAULT_MAX_EXECUTION_SECONDS,
) -> ToolSafetySandboxPolicy:
    """Build deterministic sandbox policy contract for tool execution."""
    normalized_mode = _normalize_string(mode).lower() or DEFAULT_MODE
    if normalized_mode not in {"deny_by_default", "allow_by_default"}:
        normalized_mode = DEFAULT_MODE
    return {
        "mode": normalized_mode,
        "allowed_tools": _normalize_string_list(
            allowed_tools,
            default=list(DEFAULT_ALLOWED_TOOLS),
        ),
        "denied_tools": _normalize_string_list(
            denied_tools,
            default=list(DEFAULT_DENIED_TOOLS),
        ),
        "allowed_path_prefixes": _normalize_string_list(
            allowed_path_prefixes,
            default=list(DEFAULT_ALLOWED_PATH_PREFIXES),
        ),
        "allow_network": _normalize_bool(allow_network, default=DEFAULT_ALLOW_NETWORK),
        "max_execution_seconds": _normalize_int(
            max_execution_seconds,
            default=DEFAULT_MAX_EXECUTION_SECONDS,
            min_value=1,
            max_value=MAX_EXECUTION_SECONDS_CAP,
        ),
    }


def build_tool_safety_sandbox_policy_from_dict(
    *,
    raw: dict[str, object] | None,
) -> ToolSafetySandboxPolicy:
    payload = raw if isinstance(raw, dict) else {}
    return build_tool_safety_sandbox_policy(
        mode=payload.get("mode", DEFAULT_MODE),
        allowed_tools=payload.get("allowed_tools", None),
        denied_tools=payload.get("denied_tools", None),
        allowed_path_prefixes=payload.get("allowed_path_prefixes", None),
        allow_network=payload.get("allow_network", DEFAULT_ALLOW_NETWORK),
        max_execution_seconds=payload.get(
            "max_execution_seconds",
            DEFAULT_MAX_EXECUTION_SECONDS,
        ),
    )
