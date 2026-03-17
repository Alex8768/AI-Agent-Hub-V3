from __future__ import annotations


_DIRECT_DESTRUCTIVE_PATTERNS: tuple[str, ...] = (
    "rm -rf",
    "удалить все файлы",
    "delete all files",
    "wipe workspace",
    "truncate table",
    "drop table",
)

_DESTRUCTIVE_MARKERS: tuple[str, ...] = (
    "удалить",
    "delete",
    "wipe",
    "destroy",
    "erase",
    "truncate",
    "drop table",
)

_OPERATIONAL_MARKERS: tuple[str, ...] = (
    "выполни",
    "запусти",
    "run command",
    "execute",
    "apply patch",
    "write file",
    "save_file",
    "измени файл",
)

_PLANNING_KNOWLEDGE_MARKERS: tuple[str, ...] = (
    "план",
    "как",
    "объясни",
    "структур",
    "steps",
    "plan",
    "outline",
    "strategy",
    "tell me about",
    "what do you know",
    "без выполнения",
    "without execution",
    "without executing",
)


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def classify_risk_tier(query: str) -> str:
    lowered = str(query or "").strip().lower()
    if not lowered:
        return "L0"

    if _contains_any(lowered, _DIRECT_DESTRUCTIVE_PATTERNS):
        return "L3"

    destructive = _contains_any(lowered, _DESTRUCTIVE_MARKERS)
    operational = _contains_any(lowered, _OPERATIONAL_MARKERS)
    planning_or_knowledge = _contains_any(lowered, _PLANNING_KNOWLEDGE_MARKERS)

    if destructive and operational and not planning_or_knowledge:
        return "L3"
    if operational:
        return "L2"

    token_count = len([t for t in lowered.replace("?", " ").split() if t.strip()])
    if planning_or_knowledge or token_count >= 7:
        return "L1"
    return "L0"


def build_risk_tier_reason(query: str, tier: str) -> str:
    lowered = str(query or "").strip().lower()
    if not lowered:
        return "empty_query_default_l0"

    if tier == "L3":
        if _contains_any(lowered, _DIRECT_DESTRUCTIVE_PATTERNS):
            return "destructive_direct_pattern"
        return "destructive_operational_request"
    if tier == "L2":
        return "operational_execution_request"
    if tier == "L1":
        if _contains_any(lowered, _PLANNING_KNOWLEDGE_MARKERS):
            return "planning_or_knowledge_request"
        return "substantive_query_length"
    return "low_risk_general_query"


def should_force_fallback(*, risk_tier: str, policy_violations: list[str], runtime_error: bool = False) -> bool:
    if runtime_error:
        return True
    if risk_tier == "L3":
        return True
    return bool(policy_violations) and risk_tier == "L2"
