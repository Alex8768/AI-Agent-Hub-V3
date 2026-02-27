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
    requires_env: dict[str, str] | None = None
    notes: str = ""


def _pick_free_port(host: str = "127.0.0.1") -> int:
    s = socket.socket()
    s.bind((host, 0))
    port = int(s.getsockname()[1])
    s.close()
    return port


def _load_cases(path: Path) -> list[Case]:
    raw = path.read_text(encoding="utf-8")
    # tolerate accidental literal "\n" sequences
    raw = raw.replace("\\n", "\n")

    cases: list[Case] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        obj = json.loads(line)
        req_env = obj.get("requires_env") or None
        if req_env is not None and not isinstance(req_env, dict):
            req_env = None
        cases.append(
            Case(
                id=str(obj.get("id") or obj.get("case_id") or f"case-{len(cases)+1:03d}"),
                workspace_id=str(obj.get("workspace_id") or "default"),
                query=str(obj["query"]),
                k=int(obj.get("k", 8)),
                graph_depth=int(obj.get("graph_depth", 1)),
                expect_any_prefix=list(obj.get("expect_any_prefix") or obj.get("expect_any_prefixes") or []),
                requires_env={str(k): str(v) for k, v in (req_env or {}).items()} if req_env else None,
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
        return False
    for x in top_evidence:
        for p in prefixes:
            if x.startswith(p):
                return True
    return False


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    vals = sorted(values)
    idx = int(0.95 * (len(vals) - 1))
    return float(vals[idx])


def _env_satisfies(req: dict[str, str]) -> bool:
    for k, v in (req or {}).items():
        if os.environ.get(k, "") != str(v):
            return False
    return True


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

    env = os.environ.copy()

    # Pro surface for eval
    if os.environ.get("EVAL_ENABLE_PRO", "1") == "1":
        env.setdefault("FEATURE_REASONING", "true")
        env.setdefault("FEATURE_GRAPHRAG", "true")

        # Default mode: dry-run unless explicitly using a real provider
        if os.environ.get("EVAL_ENABLE_OPENAI", "0") == "1":
            env.setdefault("FEATURE_REASONING_LLM_ENABLED", "true")
            env.setdefault("FEATURE_REASONING_LLM_DRY_RUN", "false")
            env.setdefault("LLM_PROVIDER", "openai")
            # Safe default for eval (override via OPENAI_MODEL)
            env.setdefault("OPENAI_MODEL", "gpt-4o-mini")
        elif os.environ.get("EVAL_ENABLE_OLLAMA", "0") == "1":
            env.setdefault("FEATURE_REASONING_LLM_ENABLED", "true")
            env.setdefault("FEATURE_REASONING_LLM_DRY_RUN", "false")
            env.setdefault("LLM_PROVIDER", "ollama")
            # Use an installed model by default (override via OLLAMA_MODEL)
            env.setdefault("OLLAMA_MODEL", "llama3.1:latest")
        else:
            env.setdefault("FEATURE_REASONING_LLM_ENABLED", "false")
            env.setdefault("FEATURE_REASONING_LLM_DRY_RUN", "true")

        # If caller explicitly wants dryrun, force it
        if os.environ.get("EVAL_ENABLE_DRYRUN", "0") == "1":
            env["FEATURE_REASONING_LLM_ENABLED"] = "false"
            env["FEATURE_REASONING_LLM_DRY_RUN"] = "true"

    # Memory toggles
    if os.environ.get("EVAL_ENABLE_MEMORY", "0") == "1":
        env.setdefault("FEATURE_MEMORY", "true")
    if os.environ.get("EVAL_ENABLE_MEMORY_EMBEDDINGS", "0") == "1":
        env.setdefault("FEATURE_MEMORY_EMBEDDINGS", "true")

    env["HOST"] = host
    env["PORT"] = str(port)

    cmd = ["uvicorn", "src.api.main:app", "--host", host, "--port", str(port)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)

    try:
        _wait_health(base_url, timeout_s=health_timeout)
        print("✅ /health ready")
        print()

        total_run = 0
        skipped = 0
        ok = 0
        http200 = 0

        latencies: list[float] = []
        with_evidence = 0
        with_memory = 0
        vector_candidates: list[float] = []

        with out_path.open("a", encoding="utf-8") as f_out:
            with httpx.Client(timeout=120.0) as client:
                for c in cases:
                    if c.requires_env and not _env_satisfies(c.requires_env):
                        skipped += 1
                        print(f"- {c.id}: SKIP (requires_env={c.requires_env})")
                        continue

                    total_run += 1
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
                        "requires_env": c.requires_env or {},
                    }

                    if r.status_code == 200:
                        http200 += 1
                        body = r.json()
                        diag = body.get("diagnostics") or {}
                        top_evidence = diag.get("top_evidence") or []
                        trace_id = diag.get("trace_id") or ""

                        prov_n = int(diag.get("retrieved_provenance_count") or 0)
                        if prov_n > 0:
                            with_evidence += 1

                        type_counts = diag.get("evidence_type_counts") or {}
                        mem_n = int(type_counts.get("memory") or 0) if isinstance(type_counts, dict) else 0
                        if mem_n > 0:
                            with_memory += 1

                        vc = diag.get("retrieval_vector_candidates_count")
                        try:
                            if vc is not None:
                                vector_candidates.append(float(vc))
                        except Exception:
                            pass

                        hit_prefix = _count_prefix_hits(list(top_evidence), list(c.expect_any_prefix or []))
                        hit_any_evidence = (prov_n > 0) or (len(top_evidence) > 0)
                        passed = bool(hit_prefix or (not (c.expect_any_prefix or []) and hit_any_evidence))

                        rec.update(
                            {
                                "trace_id": trace_id,
                                "warnings": body.get("warnings") or [],
                                "timings": body.get("timings") or {},
                                "diagnostics": diag,
                                "top_evidence": top_evidence,
                                "expectation_pass": passed,
                            }
                        )
                        if passed:
                            ok += 1
                        latencies.append(float(dt_ms))
                    else:
                        rec["body"] = r.text
                        rec["expectation_pass"] = False

                    f_out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    print(f"- {c.id}: HTTP {r.status_code}  {dt_ms:7.1f}ms")

        print()
        avg = (sum(latencies) / len(latencies)) if latencies else 0.0
        p95 = _p95(latencies)
        vc_avg = (sum(vector_candidates) / len(vector_candidates)) if vector_candidates else 0.0

        print("== Summary ==")
        print(f"cases_total: {len(cases)}")
        print(f"cases_run: {total_run}")
        print(f"cases_skipped: {skipped}")
        print(f"http_200: {http200}/{total_run}" if total_run else "http_200: 0/0")
        print(f"expectation_pass: {ok}/{total_run}" if total_run else "expectation_pass: 0/0")
        print(f"with_evidence: {with_evidence}/{http200}" if http200 else "with_evidence: 0/0")
        print(f"with_memory: {with_memory}/{http200}" if http200 else "with_memory: 0/0")
        print(f"latency_ms_avg: {avg:.1f}")
        print(f"latency_ms_p95: {p95:.1f}")
        print(f"vector_candidates_avg: {vc_avg:.2f}" if vector_candidates else "vector_candidates_avg: n/a")
        print(f"results: {out_path}")
        return 0

    finally:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
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
