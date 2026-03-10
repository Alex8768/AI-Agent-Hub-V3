from __future__ import annotations

from typing import Callable


def build_reasoning_planner_runtime() -> dict[str, Callable[..., object]]:
    """Build planner runtime composition seam.

    Keeps planner/prompt wiring behind a stable kernel boundary so callers do not
    depend on concrete planner module paths.
    """
    from src.layers.pro.reasoning.planner.planner import create_reasoning_plan
    from src.layers.pro.reasoning.planner.step_executor import execute_plan_steps
    from src.layers.pro.reasoning.prompt_builder import build_reasoning_prompt

    return {
        "create_plan": create_reasoning_plan,
        "execute_steps": execute_plan_steps,
        "build_prompt": build_reasoning_prompt,
    }
