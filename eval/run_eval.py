from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


@dataclass(frozen=True)
class Case:
    id: str
    workspace_id: str
    query: str
    k: int = 8
    graph_depth: int = 1
    expect_any_prefix: list[str] | None = None
    notes: str = ""


def _pick_free_port(host: str = "127.0.0.1") -> int:
    s = socket.socket()
    s.bind((host, 0))
    port = int(s.getsockname()[1])
    s.close()
    return port


def _load_cases(path: Path) -> list[Case]:
    cases: list[Case] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        obj = json.loads(line)
        cases.append(
            Case(
                id=str(obj.get("id") or obj.get("case_id") or f"case-{len(cases)+1:03d}"),
                workspace_id=str(obj.get("workspace_id") or "default"),
                query=str(obj["query"]),
                k=int(obj.get("k", 8)),
                graph_depth=int(obj.get("graph_depth", 1)),
                expect_any_prefix=list(obj.get("expect_any_prefix") or obj.get("expect_any_prefixes") or []),
                notes=str(obj.get("notes") or ""),
            )
        )
    return cases


def _wait_health(base_url: str, timeout_s: float = 25.0) -> None:
    deadline = time.time() + float(timeout_s)
    while True:
        try:
            r = httpx.get(f"{base_url}/health", timeout=2.0)
            if r.status_code == 200:
                return
        except Exception:
            pass
        if time.time() >= deadline:
            raise RuntimeError(f"Server did not become healthy within {timeout_s}s")
        time.sleep(0.35)


def _count_prefix_hits(top_evidence: list[str], prefixes: list[str]) -> bool:
    if not prefixes:
        return True
    for x in top_evidence:
        for p in prefixes:
            if x.startswith(p):
                return True
    return False


def main() -> int:
    cases_path = Path(os.environ.get("CASES", "eval/cases.jsonl"))
    out_path = Path(os.environ.get("OUT", "eval/results.jsonl"))
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "") or _pick_free_port(host))
    base_url = os.environ.get("BASE_URL", f"http://{host}:{port}")
    health_timeout = float(os.environ.get("HEALTH_TIMEOUT", "25"))

    if not cases_path.exists():
        print(f"ERROR: cases file not found: {cases_path}", file=sys.stderr)
        return 2

    cases = _load_cases(cases_path)
    if not cases:
        print("ERROR: no cases loaded", file=sys.stderr)
        return 2

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()

    print("== AI Agent Hub V3 :: Eval Runner ==")
    print(f"BASE_URL={base_url}")
    print(f"CASES={cases_path}")
    print(f"OUT={out_path}")
    print()

    # Start server (same idea as scripts/run_and_smoke.sh)
    env = os.environ.copy()
    env["HOST"] = host
    env["PORT"] = str(port)

    cmd = ["uvicorn", "src.api.main:app", "--host", host, "--port", str(port)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)

    try:
        _wait_health(base_url, timeout_s=health_timeout)
        print("✅ /health ready")
        print()

        total = 0
        ok = 0
        latencies: list[float] = []
        with out_path.open("a", encoding="utf-8") as f_out:
            with httpx.Client(timeout=60.0) as client:
                for c in cases:
                    total += 1
                    t0 = time.time()
                    r = client.post(
                        f"{base_url}/api/v1/answer",
                        headers={"X-Workspace-Id": c.workspace_id},
                        json={"query": c.query, "k": c.k, "graph_depth": c.graph_depth},
                    )
                    dt_ms = (time.time() - t0) * 1000.0

                    rec: dict[str, Any] = {
                        "case_id": c.id,
                        "workspace_id": c.workspace_id,
                        "status_code": r.status_code,
                        "latency_ms": float(dt_ms),
                    }

                    if r.status_code == 200:
                        body = r.json()
                        diag = body.get("diagnostics") or {}
                        top_evidence = diag.get("top_evidence") or []
                        trace_id = diag.get("trace_id") or ""
                        rec.update(
                            {
                                "trace_id": trace_id,
                                "warnings": body.get("warnings") or [],
                                "timings": body.get("timings") or {},
                                "diagnostics": diag,
                                "top_evidence": top_evidence,
                            }
                        )
                        hit = _count_prefix_hits(list(top_evidence), list(c.expect_any_prefix or []))
                        rec["expectation_pass"] = bool(hit)
                        if hit:
                            ok += 1
                        latencies.append(float(dt_ms))
                    else:
                        rec["body"] = r.text

                    f_out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    print(f"- {c.id}: HTTP {r.status_code}  {dt_ms:7.1f}ms")

        print()
        avg = (sum(latencies) / len(latencies)) if latencies else 0.0
        p95 = sorted(latencies)[int(0.95 * (len(latencies) - 1))] if len(latencies) >= 2 else (latencies[0] if latencies else 0.0)
        print("== Summary ==")
        print(f"cases: {total}")
        print(f"expectation_pass: {ok}/{total}")
        print(f"latency_ms_avg: {avg:.1f}")
        print(f"latency_ms_p95: {p95:.1f}")
        print(f"results: {out_path}")
        return 0

    finally:
        # shutdown server
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        # if failed, print tail of logs
        if proc.stdout is not None:
            try:
                tail = proc.stdout.read()[-4000:]
                if tail:
                    print("\n--- uvicorn log tail ---")
                    print(tail)
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
