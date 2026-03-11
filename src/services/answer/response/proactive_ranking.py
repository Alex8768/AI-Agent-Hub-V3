from __future__ import annotations


def rank_proactive_bundle(bundle: dict[str, object]) -> dict[str, object]:
    suggestions = [dict(row or {}) for row in list(bundle.get("suggestions") or [])]
    normalized: list[dict[str, object]] = []
    for row in suggestions:
        try:
            confidence = float(row.get("confidence", 0.0) or 0.0)
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))
        priority = int(round(confidence * 100))
        normalized.append(
            {
                **row,
                "priority": priority,
            }
        )

    normalized.sort(
        key=lambda x: (
            -int(x.get("priority", 0) or 0),
            str(x.get("suggestion_type", "") or ""),
            str(x.get("suggestion_id", "") or ""),
        )
    )
    ranked: list[dict[str, object]] = []
    for idx, row in enumerate(normalized, start=1):
        ranked.append(
            {
                **row,
                "rank": idx,
            }
        )

    reason_codes = sorted(
        set(
            [
                str(x)
                for x in list(bundle.get("reason_codes") or [])
                if str(x or "").strip()
            ]
            + (["ranked_by_priority"] if ranked else [])
        )
    )
    top_suggestion_id = str((ranked[0] or {}).get("suggestion_id", "") or "") if ranked else ""
    status = "active" if ranked else str(bundle.get("status", "idle") or "idle")
    return {
        "status": status,
        "suggestions": ranked,
        "top_suggestion_id": top_suggestion_id,
        "reason_codes": reason_codes,
        "warnings": list(bundle.get("warnings") or []),
    }
