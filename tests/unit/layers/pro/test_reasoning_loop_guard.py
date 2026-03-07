from __future__ import annotations

from src.layers.pro.reasoning.control.loop_guard import (
    apply_reasoning_loop_guard,
    build_reasoning_loop_guard_state,
)


def test_build_reasoning_loop_guard_state_normalizes_bounds_and_counts():
    state = build_reasoning_loop_guard_state(
        max_visits_per_signature=0,
        seen_signatures={"  STEP A  ": "2", "step b": -3},
    )
    assert state["max_visits_per_signature"] == 1
    assert state["seen_signatures"] == {"step a": 2, "step b": 0}


def test_apply_reasoning_loop_guard_triggers_after_budget_exhausted():
    state = build_reasoning_loop_guard_state(max_visits_per_signature=2)

    first = apply_reasoning_loop_guard(state=state, step_description="Repeat me")
    second = apply_reasoning_loop_guard(
        state=first["state"],
        step_description="repeat   me",
    )
    third = apply_reasoning_loop_guard(
        state=second["state"],
        step_description=" REPEAT ME ",
    )

    assert first["decision"]["should_stop"] is False
    assert second["decision"]["should_stop"] is False
    assert third["decision"]["should_stop"] is True
    assert third["decision"]["reason"] == "loop_guard_stop_visit_limit_exceeded"
    assert third["state"]["seen_signatures"]["repeat me"] == 3


def test_apply_reasoning_loop_guard_tracks_signatures_independently():
    state = build_reasoning_loop_guard_state(max_visits_per_signature=1)

    step_a = apply_reasoning_loop_guard(state=state, step_description="a")
    step_b = apply_reasoning_loop_guard(state=step_a["state"], step_description="b")
    step_a_second = apply_reasoning_loop_guard(
        state=step_b["state"],
        step_description="a",
    )

    assert step_a["decision"]["should_stop"] is False
    assert step_b["decision"]["should_stop"] is False
    assert step_a_second["decision"]["should_stop"] is True
    assert step_a_second["state"]["seen_signatures"] == {"a": 2, "b": 1}


def test_apply_reasoning_loop_guard_normalizes_empty_step_signature():
    result = apply_reasoning_loop_guard(
        state=build_reasoning_loop_guard_state(max_visits_per_signature=1),
        step_description="   ",
    )
    assert result["decision"]["signature"] == "__empty_step__"
    assert result["state"]["seen_signatures"]["__empty_step__"] == 1
