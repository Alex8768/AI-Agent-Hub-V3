from __future__ import annotations

from typing import TypedDict

DEFAULT_RISK_LEVEL = "medium"
DEFAULT_CAPABILITIES = ["read"]
DEFAULT_REQUIRES_NETWORK = False
DEFAULT_REQUIRES_FILESYSTEM = True
DEFAULT_REQUIRES_EXECUTION = False

MAX_CAPABILITIES = 32


class ToolCatalogEntry(TypedDict):
    tool_name: str
    risk_level: str
    capabilities: list[str]
    requires_network: bool
    requires_filesystem: bool
    requires_execution: bool


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


def _normalize_capabilities(values: object) -> list[str]:
    items = list(values) if isinstance(values, list) else list(DEFAULT_CAPABILITIES)
    normalized: list[str] = []
    for raw in items:
        value = _normalize_string(raw).lower()
        if not value:
            continue
        normalized.append(value)
    return sorted(set(normalized))[:MAX_CAPABILITIES]


def build_tool_catalog_entry(
    *,
    tool_name: object,
    risk_level: object = DEFAULT_RISK_LEVEL,
    capabilities: object = None,
    requires_network: object = DEFAULT_REQUIRES_NETWORK,
    requires_filesystem: object = DEFAULT_REQUIRES_FILESYSTEM,
    requires_execution: object = DEFAULT_REQUIRES_EXECUTION,
) -> ToolCatalogEntry:
    """Build normalized tool metadata row for sandbox decisions."""
    normalized_risk = _normalize_string(risk_level).lower() or DEFAULT_RISK_LEVEL
    if normalized_risk not in {"low", "medium", "high", "critical"}:
        normalized_risk = DEFAULT_RISK_LEVEL
    return {
        "tool_name": _normalize_string(tool_name),
        "risk_level": normalized_risk,
        "capabilities": _normalize_capabilities(capabilities),
        "requires_network": _normalize_bool(
            requires_network,
            default=DEFAULT_REQUIRES_NETWORK,
        ),
        "requires_filesystem": _normalize_bool(
            requires_filesystem,
            default=DEFAULT_REQUIRES_FILESYSTEM,
        ),
        "requires_execution": _normalize_bool(
            requires_execution,
            default=DEFAULT_REQUIRES_EXECUTION,
        ),
    }


def build_tool_catalog(
    *,
    rows: list[dict[str, object]],
) -> list[ToolCatalogEntry]:
    """Build deterministic tool catalog from raw metadata rows."""
    entries: list[ToolCatalogEntry] = []
    for raw in list(rows or []):
        row = raw if isinstance(raw, dict) else {}
        entry = build_tool_catalog_entry(
            tool_name=row.get("tool_name", ""),
            risk_level=row.get("risk_level", DEFAULT_RISK_LEVEL),
            capabilities=row.get("capabilities", None),
            requires_network=row.get("requires_network", DEFAULT_REQUIRES_NETWORK),
            requires_filesystem=row.get(
                "requires_filesystem",
                DEFAULT_REQUIRES_FILESYSTEM,
            ),
            requires_execution=row.get(
                "requires_execution",
                DEFAULT_REQUIRES_EXECUTION,
            ),
        )
        if not entry["tool_name"]:
            continue
        entries.append(entry)
    entries.sort(key=lambda x: str(x["tool_name"]))
    return entries
