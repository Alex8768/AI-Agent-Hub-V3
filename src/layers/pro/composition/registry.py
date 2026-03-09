from __future__ import annotations

from typing import TypedDict


class RegisteredAgentSpec(TypedDict):
    agent_id: str
    display_name: str
    capabilities: list[str]
    input_schema: dict[str, object]
    output_schema: dict[str, object]
    enabled: bool
    version: str


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _normalize_string_list(values: object) -> list[str]:
    rows: list[str] = []
    for raw in list(values or []):
        item = _normalize_string(raw).lower()
        if item:
            rows.append(item)
    return sorted(set(rows))


def _normalize_schema(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


def build_registered_agent_spec(
    *,
    agent_id: object,
    display_name: object,
    capabilities: object = None,
    input_schema: object = None,
    output_schema: object = None,
    enabled: object = True,
    version: object = "v1",
) -> RegisteredAgentSpec:
    """Build normalized agent registry contract row."""
    return {
        "agent_id": _normalize_string(agent_id),
        "display_name": _normalize_string(display_name),
        "capabilities": _normalize_string_list(capabilities),
        "input_schema": _normalize_schema(input_schema),
        "output_schema": _normalize_schema(output_schema),
        "enabled": bool(enabled),
        "version": _normalize_string(version) or "v1",
    }


class AgentRegistry:
    """Deterministic in-memory registry for micro-agents."""

    def __init__(self) -> None:
        self._agents: dict[str, RegisteredAgentSpec] = {}

    def register(self, spec: dict[str, object] | RegisteredAgentSpec) -> RegisteredAgentSpec:
        row = dict(spec or {})
        normalized = build_registered_agent_spec(
            agent_id=row.get("agent_id", ""),
            display_name=row.get("display_name", ""),
            capabilities=row.get("capabilities", []),
            input_schema=row.get("input_schema", {}),
            output_schema=row.get("output_schema", {}),
            enabled=row.get("enabled", True),
            version=row.get("version", "v1"),
        )
        if not normalized["agent_id"]:
            raise ValueError("agent_id is required")
        if not normalized["display_name"]:
            raise ValueError("display_name is required")
        self._agents[normalized["agent_id"]] = normalized
        return dict(normalized)

    def get(self, agent_id: object) -> RegisteredAgentSpec | None:
        key = _normalize_string(agent_id)
        row = self._agents.get(key)
        return dict(row) if row else None

    def list(self, *, enabled_only: bool = False) -> list[RegisteredAgentSpec]:
        rows = [dict(x) for x in self._agents.values()]
        if enabled_only:
            rows = [row for row in rows if bool(row.get("enabled", False))]
        rows.sort(key=lambda x: str(x.get("agent_id", "")))
        return rows

    def find_by_capabilities(self, capabilities: list[str] | None) -> list[RegisteredAgentSpec]:
        requested = _normalize_string_list(capabilities or [])
        if not requested:
            return self.list(enabled_only=True)
        rows: list[RegisteredAgentSpec] = []
        for row in self.list(enabled_only=True):
            supported = set(_normalize_string_list(row.get("capabilities", [])))
            if set(requested).issubset(supported):
                rows.append(row)
        rows.sort(key=lambda x: str(x.get("agent_id", "")))
        return rows
