from __future__ import annotations

from src.layers.pro.reasoning.contracts import ProvenanceItem


def clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def compute_confidence(provenance: list[ProvenanceItem]) -> float:
    """Deterministic confidence heuristic (MVP).

    Rules:
      - no provenance => 0.0
      - provenance but no per-item confidence => 0.2
      - otherwise => average of item confidence values, clamped [0, 1]
    """
    if not provenance:
        return 0.0

    vals: list[float] = [p.confidence for p in provenance if p.confidence is not None]  # type: ignore[list-item]
    if not vals:
        return 0.2

    avg = sum(vals) / len(vals)
    return clamp01(float(avg))
