from __future__ import annotations

from typing import Any

from src.services.answer.containers.shared import run_container_pipeline


async def run_dialog_container(**kwargs: Any) -> Any:
    return await run_container_pipeline(**kwargs)

