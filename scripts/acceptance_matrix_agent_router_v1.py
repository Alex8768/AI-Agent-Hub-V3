#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Requires httpx. Run with: uv run python scripts/acceptance_matrix_agent_router_v1.py", file=sys.stderr)
    sys.exit(1)


PROMPTS: list[str] = [
    "Привет",
    "Кто ты?",
    "Что ты умеешь?",
    "Какой план презентации по степям Краснодарского края?",
    "Сделай краткий outline доклада про экосистемы степей.",
    "Сравни три подхода к исследовательскому проекту.",
    "Как сделать безопасный бэкап перед изменениями?",
    "Как составить план очистки устаревших черновиков?",
    "Напиши черновик структуры отчета по запуску фичи.",
    "Дай пошаговый план внедрения CI в небольшой команде.",
    "Запусти команду ls",
    "Сохрани файл report.md с текстом 'draft'",
    "Удалить все файлы в workspace",
    "Выполни rm -rf /",
    "Подготовь безопасный план миграции базы данных.",
    "Нужны next steps для запуска демо версии продукта.",
]

OUT_DIR = Path(__file__).resolve().parents[1] / "docs"
OUT_JSON = OUT_DIR / "agent-router-v1-matrix.json"
OUT_MD = OUT_DIR / "agent-router-v1-matrix.md"


def _is_low_quality(answer: str) -> bool:
    lowered = str(answer or "").strip().lower()
    if not lowered:
        return True
    markers = [
        "(reasoning layer stub)",
        "i don't know",
        "я не знаю",
        "insufficient information",
        "недостаточно информации",
    ]
    return any(m in lowered for m in markers)


def _request_payload(query: str, enabled: bool) -> dict[str, object]:
    return {
        "query": query,
        "k": 8,
        "graph_depth": 1,
        "filters": {"feature_agent_router_v1": "true" if enabled else "false"},
    }


def _run_case(client: httpx.Client, base_url: str, query: str, enabled: bool) -> dict[str, object]:
    resp = client.post(f"{base_url}/api/v1/answer", json=_request_payload(query, enabled), timeout=60.0)
    resp.raise_for_status()
    data = dict(resp.json() or {})
    diag = dict(data.get("diagnostics") or {})
    answer = str(data.get("answer") or "")
    return {
        "answer": answer,
        "answer_len": len(answer),
        "low_quality": _is_low_quality(answer),
        "query_type": str(diag.get("query_type", "")),
        "effective_query_type": str(dict(diag.get("agent_router_v1") or {}).get("effective_query_type", "")),
        "router_enabled": bool(dict(diag.get("agent_router_v1") or {}).get("enabled", False)),
        "reflection_retries_used": int(dict(diag.get("reflection_lite") or {}).get("retries_used", 0) or 0),
        "tool_policy_reasons": list(dict(diag.get("tool_policy_contract") or {}).get("reason_codes") or []),
        "planning_reason_codes": list(diag.get("planning_reason_codes") or []),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="A7 matrix: compare agent router v1 enabled vs disabled.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument("--no-write", action="store_true", help="Print only, do not write docs outputs")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    try:
        with httpx.Client() as client:
            health = client.get(f"{base}/health", timeout=10.0)
            health.raise_for_status()

            rows: list[dict[str, object]] = []
            for idx, query in enumerate(PROMPTS, 1):
                print(f"[{idx}/{len(PROMPTS)}] {query[:72]}")
                old_case = _run_case(client, base, query, enabled=False)
                new_case = _run_case(client, base, query, enabled=True)
                rows.append(
                    {
                        "query": query,
                        "old": old_case,
                        "new": new_case,
                        "improved_quality": bool(old_case["low_quality"]) and not bool(new_case["low_quality"]),
                    }
                )
    except Exception as exc:
        print(f"Matrix run failed: {exc}", file=sys.stderr)
        sys.exit(2)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "ts": ts,
        "base_url": base,
        "feature_flag": "FEATURE_AGENT_ROUTER_V1",
        "prompts_count": len(PROMPTS),
        "results": rows,
    }

    if not args.no_write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        lines = [
            "# Agent Router V1 Acceptance Matrix",
            "",
            f"**Date:** {ts}  **Base URL:** {base}  **Prompts:** {len(PROMPTS)}",
            "",
            "| # | Query | old low-quality | new low-quality | improved | old qtype->eff | new qtype->eff |",
            "|---|-------|-----------------|-----------------|----------|----------------|----------------|",
        ]
        for i, row in enumerate(rows, 1):
            q = str(row["query"]).replace("\n", " ")
            old = dict(row["old"] or {})
            new = dict(row["new"] or {})
            lines.append(
                "| "
                + f"{i} | {q[:56]} | {old.get('low_quality')} | {new.get('low_quality')} | "
                + f"{row.get('improved_quality')} | "
                + f"{old.get('query_type')}->{old.get('effective_query_type')} | "
                + f"{new.get('query_type')}->{new.get('effective_query_type')} |"
            )
        lines.extend(["", "See `agent-router-v1-matrix.json` for full payload.", ""])
        OUT_MD.write_text("\n".join(lines), encoding="utf-8")
        print(f"Wrote {OUT_JSON}")
        print(f"Wrote {OUT_MD}")

    improved = sum(1 for r in rows if bool(r.get("improved_quality", False)))
    print(f"\nImproved quality cases: {improved}/{len(rows)}")


if __name__ == "__main__":
    main()

