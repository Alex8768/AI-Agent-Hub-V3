from __future__ import annotations

from enum import Enum


class QueryType(str, Enum):
    DIALOG = "dialog"
    ADVICE = "advice"
    ACTION = "action"


_ACTION_MARKERS: tuple[str, ...] = (
    "удали",
    "delete",
    "remove",
    "создай файл",
    "create file",
    "измени файл",
    "modify file",
    "выполни",
    "run command",
    "execute",
    "rm -rf",
)

_ADVICE_MARKERS: tuple[str, ...] = (
    "напиши код",
    "write code",
    "сделай план",
    "план",
    "как сделать",
    "how to",
    "предложи",
    "suggest",
    "можешь сделать документ",
)

_DIALOG_MARKERS: tuple[str, ...] = (
    "привет",
    "кто ты",
    "ты кто",
    "как дела",
    "что думаешь",
    "hello",
    "hi",
    "who are you",
)


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _classify_with_rules(query: str) -> tuple[QueryType, str]:
    lowered = str(query or "").strip().lower()
    if not lowered:
        return QueryType.DIALOG, "rules:empty_query_default_dialog"
    if _contains_any(lowered, _ACTION_MARKERS):
        return QueryType.ACTION, "rules:action_marker"
    if _contains_any(lowered, _DIALOG_MARKERS):
        return QueryType.DIALOG, "rules:dialog_marker"
    if _contains_any(lowered, _ADVICE_MARKERS):
        return QueryType.ADVICE, "rules:advice_marker"
    # Neutral default keeps routing safe and useful.
    return QueryType.DIALOG, "rules:default_dialog"


async def classify_query_type(*, query: str, llm: object | None = None) -> tuple[QueryType, str]:
    rule_type, rule_reason = _classify_with_rules(query)
    lowered = str(query or "").strip().lower()
    if rule_reason != "rules:default_dialog":
        return rule_type, rule_reason

    if llm is None or not hasattr(llm, "generate"):
        return rule_type, rule_reason

    prompt = (
        "Classify user query into exactly one label: DIALOG, ADVICE, ACTION.\n"
        "- DIALOG: greetings, identity, general discussion.\n"
        "- ADVICE: ask for plan/code/recommendations, no direct execution.\n"
        "- ACTION: direct instruction to execute/create/modify/delete.\n"
        f'Query: "{str(query or "").strip()}"\n'
        "Answer with one token only."
    )
    try:
        raw = str(await llm.generate(prompt)).strip().upper()
    except Exception:
        return rule_type, "rules:default_dialog_llm_failed"

    if "ACTION" in raw:
        return QueryType.ACTION, "llm:action"
    if "ADVICE" in raw:
        return QueryType.ADVICE, "llm:advice"
    if "DIALOG" in raw:
        return QueryType.DIALOG, "llm:dialog"

    # Safety default
    if any(token in lowered for token in ("удали", "delete", "execute", "run command")):
        return QueryType.ACTION, "llm:unparseable_action_fallback"
    return QueryType.DIALOG, "llm:unparseable_default_dialog"

