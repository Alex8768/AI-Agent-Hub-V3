from __future__ import annotations

from src.services.answer.risk_tier import (
    build_l2_safe_terminal,
    build_risk_tier_reason,
    classify_risk_tier,
)


def test_build_l2_safe_terminal_includes_plan_and_confirm_ru():
    text = build_l2_safe_terminal("Выполни команду ls", "ru")
    assert "план" in text or "подтвержд" in text
    assert len(text) > 50


def test_build_l2_safe_terminal_includes_plan_and_confirm_en():
    text = build_l2_safe_terminal("Run command ls", "en")
    assert "plan" in text.lower() or "confirm" in text.lower()
    assert len(text) > 50


def test_classify_risk_tier_marks_direct_destructive_as_l3():
    assert classify_risk_tier("Удалить все файлы в workspace") == "L3"


def test_classify_risk_tier_marks_operational_as_l2():
    assert classify_risk_tier("Выполни команду ls в корне проекта") == "L2"


def test_classify_risk_tier_marks_planning_query_as_l1():
    assert classify_risk_tier("Какой план презентации по географии ты предложишь?") == "L1"


def test_classify_risk_tier_avoids_false_positive_l3_for_safe_planning():
    query = "Составь план безопасной очистки: что проверить перед тем как удалять старые черновики, без выполнения команд."
    assert classify_risk_tier(query) == "L1"
    assert build_risk_tier_reason(query, "L1") == "planning_or_knowledge_request"
