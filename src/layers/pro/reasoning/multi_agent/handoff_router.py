from __future__ import annotations

from typing import TypedDict

from src.layers.pro.reasoning.multi_agent.coordination_model import MultiAgentCoordinationPlan


class MultiAgentHandoffTransition(TypedDict):
    from_step_index: int
    to_step_index: int
    from_role: str
    to_role: str
    output_key: str
    accepted: bool
    reason: str


def _normalize_index(value: object) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except Exception:
        return 0
    return max(0, int(parsed))


def _normalize_string(value: object) -> str:
    return str(value or "").strip()


def _build_step_map(plan: MultiAgentCoordinationPlan) -> dict[int, dict[str, object]]:
    step_map: dict[int, dict[str, object]] = {}
    for raw in list(plan.get("steps") or []):
        row = raw if isinstance(raw, dict) else {}
        idx = _normalize_index(row.get("step_index", 0))
        step_map[idx] = row
    return step_map


def route_multi_agent_handoffs(
    *,
    plan: MultiAgentCoordinationPlan,
) -> list[MultiAgentHandoffTransition]:
    """Build deterministic handoff transitions from coordination plan dependencies."""
    step_map = _build_step_map(plan)
    transitions: list[MultiAgentHandoffTransition] = []

    for raw in list(plan.get("steps") or []):
        step = raw if isinstance(raw, dict) else {}
        to_idx = _normalize_index(step.get("step_index", 0))
        to_role = _normalize_string(step.get("agent_role", ""))
        depends_on = list(step.get("depends_on") or [])

        for raw_dep in depends_on:
            from_idx = _normalize_index(raw_dep)
            from_step = step_map.get(from_idx, {})
            from_role = _normalize_string(from_step.get("agent_role", ""))
            output_key = _normalize_string(from_step.get("output_key", ""))
            input_keys = [str(x or "").strip() for x in list(step.get("input_keys") or [])]
            accepted = bool(output_key and output_key in input_keys)
            reason = (
                "handoff_output_key_consumed"
                if accepted
                else "handoff_output_key_not_consumed"
            )
            transitions.append(
                {
                    "from_step_index": from_idx,
                    "to_step_index": to_idx,
                    "from_role": from_role,
                    "to_role": to_role,
                    "output_key": output_key,
                    "accepted": accepted,
                    "reason": reason,
                }
            )

    transitions.sort(
        key=lambda x: (
            int(x["from_step_index"]),
            int(x["to_step_index"]),
            str(x["output_key"]),
            str(x["to_role"]),
        )
    )
    return transitions
