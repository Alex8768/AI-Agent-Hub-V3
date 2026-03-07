from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from src.layers.pro.reasoning.graph.builder import build_reasoning_graph
from src.layers.pro.reasoning.graph.state import AgentState
from src.layers.pro.reasoning.contracts import (
    EVIDENCE_CONTRACT_VERSION,
    SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN,
    SELF_CHECK_MISSING_MINIMAL_COUNT_MAX,
    VERIFY_DIAGNOSTICS_VERSION,
    VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED,
    VERIFY_SELF_CHECK_REASONS_COUNT_MAX,
    VERIFY_SELF_CHECK_STATUS_REQUIRED,
    AnswerRequest,
    AnswerResponse,
)
from src.layers.pro.reasoning.confidence import compute_confidence
from src.layers.pro.reasoning.evidence_normalizer import normalize_retrieval_result
from src.layers.pro.reasoning.context_packer import pack_context
from src.layers.pro.reasoning.quality_claims import extract_claims
from src.layers.pro.reasoning.quality_confidence import compute_reasoning_quality_confidence
from src.layers.pro.reasoning.quality_coverage import score_claim_coverage
from src.layers.pro.reasoning.quality_retry import decide_reasoning_quality_retry
from src.layers.pro.reasoning.planner.planner import create_reasoning_plan
from src.layers.pro.reasoning.planner.step_executor import execute_plan_steps
from src.layers.pro.reasoning.trace.trace_collector import collect_reasoning_trace
from src.core.config import get_settings


@dataclass(frozen=True, slots=True)
class ReasoningEngine:
    """Graph-aware reasoning answer synthesis (Pro) with agentic loop."""

    retriever: object
    llm: object | None = None
    llm_timeout_s: float = 15.0

    @staticmethod
    def _evidence_summary(provenance: list) -> dict[str, object]:
        origins: dict[str, int] = {}
        rel_vals: list[float] = []
        for p in provenance or []:
            origin = str(getattr(p, "origin", "unknown") or "unknown")
            origins[origin] = int(origins.get(origin, 0)) + 1
            rel = getattr(p, "reliability", None)
            if isinstance(rel, (int, float)):
                rel_vals.append(float(rel))
        avg = (sum(rel_vals) / len(rel_vals)) if rel_vals else None
        return {
            "origin_counts": origins,
            "reliability_avg": avg,
            "count": int(len(provenance or [])),
        }

    @staticmethod
    def _evidence_contract_status(provenance: list) -> dict[str, object]:
        total = int(len(provenance or []))
        with_source_refs = 0
        with_known_origin = 0
        with_reliability = 0
        for p in provenance or []:
            if list(getattr(p, "source_refs", []) or []):
                with_source_refs += 1
            if str(getattr(p, "origin", "unknown") or "unknown") != "unknown":
                with_known_origin += 1
            rel = getattr(p, "reliability", None)
            if isinstance(rel, (int, float)):
                with_reliability += 1
        denom = float(total) if total > 0 else 1.0
        missing_minimal_fields: list[str] = []
        if total <= 0:
            missing_minimal_fields.extend(["source_refs", "origin"])
        else:
            if with_source_refs <= 0:
                missing_minimal_fields.append("source_refs")
            if with_known_origin <= 0:
                missing_minimal_fields.append("origin")
        minimal_coverage_score = float(
            (float(with_source_refs > 0) + float(with_known_origin > 0)) / 2.0
            if total > 0
            else 0.0
        )
        return {
            "version": EVIDENCE_CONTRACT_VERSION,
            "minimal_requirements": {
                "min_total": 1,
                "requires_source_refs": True,
                "requires_known_origin": True,
            },
            "total": total,
            "with_source_refs": with_source_refs,
            "with_known_origin": with_known_origin,
            "with_reliability": with_reliability,
            "source_refs_coverage": float(with_source_refs / denom) if total > 0 else 0.0,
            "known_origin_coverage": float(with_known_origin / denom) if total > 0 else 0.0,
            "reliability_coverage": float(with_reliability / denom) if total > 0 else 0.0,
            "missing_minimal_fields": missing_minimal_fields,
            "missing_minimal_count": int(len(missing_minimal_fields)),
            "minimal_coverage_score": minimal_coverage_score,
            "valid_minimal": bool(total > 0 and with_source_refs > 0 and with_known_origin > 0),
        }

    @staticmethod
    def _evidence_contract_gate_reason(contract: dict[str, object]) -> str:
        if bool(contract.get("valid_minimal", False)):
            return "ok"
        missing = list(contract.get("missing_minimal_fields") or [])
        if missing:
            return "missing:" + ",".join(str(x) for x in missing)
        return "invalid"

    @staticmethod
    def _self_check_diagnostics(contract: dict[str, object]) -> dict[str, object]:
        """A2.4 Patch 2: warning-only self_check contract (no answer blocking)."""
        minimal_coverage_score = float(contract.get("minimal_coverage_score") or 0.0)
        missing_minimal_count = int(len(contract.get("missing_minimal_fields") or []))
        coverage_ok = minimal_coverage_score >= float(SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN)
        missing_ok = missing_minimal_count <= int(SELF_CHECK_MISSING_MINIMAL_COUNT_MAX)
        missing = list(contract.get("missing_minimal_fields") or [])
        if coverage_ok and missing_ok:
            status = "pass"
            reasons: list[str] = []
        else:
            reasons = []
            if not coverage_ok:
                reasons.append(
                    f"threshold:minimal_coverage_score<{float(SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN):.1f}"
                )
            if not missing_ok:
                reasons.append(
                    f"threshold:missing_minimal_count>{int(SELF_CHECK_MISSING_MINIMAL_COUNT_MAX)}"
                )
            status = "warn"
        return {
            "version": "v1",
            "status": status,
            "reasons": reasons,
            "policy_mode": "warning_only",
            "inputs": {
                "evidence_contract_valid_minimal": bool(contract.get("valid_minimal", False)),
                "evidence_contract_missing_minimal_count": missing_minimal_count,
                "evidence_contract_minimal_coverage_score": minimal_coverage_score,
            },
            "thresholds": {
                "minimal_coverage_score_min": float(SELF_CHECK_MINIMAL_COVERAGE_SCORE_MIN),
                "missing_minimal_count_max": int(SELF_CHECK_MISSING_MINIMAL_COUNT_MAX),
                "missing_minimal_fields": missing,
            },
        }

    @staticmethod
    def _verify_diagnostics_preflight(*, planner_path_used: bool, self_check: dict[str, object]) -> dict[str, object]:
        """A2.5 Patch 1: warning-only verify diagnostics (no answer blocking)."""
        self_check_status = str(self_check.get("status", "") or "")
        self_check_policy_mode = str(self_check.get("policy_mode", "") or "")
        self_check_reasons_count = int(len(self_check.get("reasons") or []))
        reasons: list[str] = []
        if self_check_status != str(VERIFY_SELF_CHECK_STATUS_REQUIRED):
            reasons.append(f"self_check_status!={VERIFY_SELF_CHECK_STATUS_REQUIRED}")
        if self_check_policy_mode != str(VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED):
            reasons.append(f"self_check_policy_mode!={VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED}")
        if self_check_reasons_count > int(VERIFY_SELF_CHECK_REASONS_COUNT_MAX):
            reasons.append(f"self_check_reasons_count>{int(VERIFY_SELF_CHECK_REASONS_COUNT_MAX)}")
        status = "pass" if not reasons else "warn"
        return {
            "version": VERIFY_DIAGNOSTICS_VERSION,
            "status": status,
            "reasons": reasons,
            "policy_mode": "warning_only",
            "inputs": {
                "planner_path_used": bool(planner_path_used),
                "self_check_status": self_check_status,
                "self_check_policy_mode": self_check_policy_mode,
                "self_check_reasons_count": self_check_reasons_count,
            },
            "thresholds": {
                "required_self_check_status": str(VERIFY_SELF_CHECK_STATUS_REQUIRED),
                "required_self_check_policy_mode": str(VERIFY_SELF_CHECK_POLICY_MODE_REQUIRED),
                "self_check_reasons_count_max": int(VERIFY_SELF_CHECK_REASONS_COUNT_MAX),
            },
        }

    @staticmethod
    def _reasoning_quality_diagnostics(
        *,
        answer_text: str,
        provenance: list,
        contract: dict[str, object],
    ) -> dict[str, object]:
        claims = extract_claims(reasoning_output=str(answer_text or ""))
        coverage = score_claim_coverage(
            claims=claims,
            provenance=list(provenance or []),
        )
        unsupported_claims = int(coverage.get("claims_uncovered") or 0)
        missing_claims = int(contract.get("missing_minimal_count") or 0)
        confidence = compute_reasoning_quality_confidence(
            coverage_score=float(coverage.get("coverage_score") or 0.0),
            unsupported_claims=unsupported_claims,
            missing_claims=missing_claims,
        )
        retry = decide_reasoning_quality_retry(
            confidence_score=float(confidence.get("confidence_score") or 0.0),
            attempt=0,
            threshold=0.6,
            max_retries=1,
        )
        return {
            "version": "v1",
            "claims_total": int(len(claims)),
            "claims_sample": list(claims[:5]),
            "coverage": coverage,
            "confidence": confidence,
            "retry": retry,
        }

    @staticmethod
    def _build_reasoning_trace_diagnostics(
        *,
        query: str,
        answer_text: str,
        quality: dict[str, object],
        plan_steps: list[str],
        step_results: list[dict[str, object]],
    ) -> dict[str, object]:
        return collect_reasoning_trace(
            query=query,
            plan={"steps": [{"description": str(x or "")} for x in list(plan_steps or [])]},
            step_results=list(step_results or []),
            quality=dict(quality or {}),
            answer=answer_text,
        )

    async def _execute_planner_steps_mvp(self, *, request: AnswerRequest) -> list[dict[str, object]]:
        """A2.11 Patch 4: execute deterministic planner steps inside engine fallback."""
        plan = create_reasoning_plan(query=str(getattr(request, "query", "") or ""))

        async def _run_reasoning_step(step: dict[str, str]) -> str:
            return str(step.get("description", "") or "")

        async def _run_verify_step(reasoning_output: str) -> dict[str, object]:
            _ = reasoning_output
            return {"status": "pass", "reasons": []}

        return await execute_plan_steps(
            plan=plan,
            run_reasoning_step=_run_reasoning_step,
            run_verify_step=_run_verify_step,
            max_steps=3,
        )

    async def synthesize(self, request: AnswerRequest) -> AnswerResponse:
        """Synthesize an answer using agentic graph."""
        from time import perf_counter
        t0 = perf_counter()

        # Если LLM нет, используем старый путь (dry-run или stub)
        if self.llm is None:
            return await self._synthesize_fallback(request)

        # Строим граф
        graph = build_reasoning_graph(self.llm, self.retriever)
        
        # Инициализируем состояние
        initial_state = AgentState(
            query=request.query,
            workspace_id=getattr(request, "workspace_id", "default"),
            session_id=getattr(request, "session_id", "default"),
            session_memory_last_answer=str(getattr(request, "session_memory_last_answer", "") or ""),
            k=request.k,
            graph_depth=request.graph_depth,
            max_context_chars=request.max_context_chars,
            context_preview=str(getattr(request, "session_memory_last_answer", "") or ""),
        )

        # Запускаем граф
        try:
            runtime_graph = graph.compile() if hasattr(graph, "compile") else graph
            if hasattr(runtime_graph, "ainvoke"):
                raw_state = await runtime_graph.ainvoke(initial_state)
            elif hasattr(runtime_graph, "invoke"):
                import asyncio

                raw_state = await asyncio.to_thread(runtime_graph.invoke, initial_state)
            else:
                raise RuntimeError("Reasoning graph runtime does not support invoke/ainvoke")

            # LangGraph runtime may return dict-like state snapshots.
            if isinstance(raw_state, AgentState):
                final_state = raw_state
            elif isinstance(raw_state, dict):
                final_state = AgentState.model_validate(raw_state)
            else:
                raise RuntimeError(f"Unsupported final state type: {type(raw_state).__name__}")
        except Exception as e:
            # В случае ошибки графа - падаем на старый путь
            return await self._synthesize_fallback(request, error=str(e))

        # Safety net: if planner graph produced an internal error marker,
        # fallback to the one-pass path with established timeout/error behavior.
        if getattr(final_state, "error", None):
            return await self._synthesize_fallback(request, error=str(final_state.error))

        # Собираем ответ из финального состояния
        from src.core.config import get_settings
        s = get_settings()
        dry_run = bool(getattr(s, "feature_reasoning_llm_dry_run", False))

        answer_text = final_state.final_answer or "(no answer generated)"
        if dry_run and not final_state.final_answer:
            # Генерируем dry-run ответ из контекста
            answer_text = self._build_dry_run_answer(final_state)

        # Считаем confidence (пока используем старую логику)
        confidence = compute_confidence(final_state.provenance)

        # Контекст для preview (берём из состояния)
        context_preview = final_state.context_preview or ""

        # Собираем результат
        resp = AnswerResponse(
            answer=answer_text,
            confidence=confidence,
            context_preview=context_preview,
            provenance=final_state.provenance,
            used_chunks=final_state.used_chunks,
            used_nodes=final_state.used_nodes,
            used_edges=final_state.used_edges,
        )

        # Добавляем диагностику
        try:
            diag = dict(getattr(resp, "diagnostics", None) or {})
            diag["agent_iterations"] = final_state.iteration_count
            diag["agent_actions"] = final_state.plan
            diag["agent_current_action"] = str(getattr(final_state, "current_action", "") or "")
            diag["agent_current_step"] = int(getattr(final_state, "current_step", 0) or 0)
            diag["planner_path_used"] = True
            diag["session_id"] = str(getattr(final_state, "session_id", "") or "")
            diag["evidence_summary"] = self._evidence_summary(final_state.provenance)
            diag["evidence_contract_version"] = EVIDENCE_CONTRACT_VERSION
            contract = self._evidence_contract_status(final_state.provenance)
            diag["evidence_contract"] = contract
            diag["evidence_contract_valid_minimal"] = bool(contract.get("valid_minimal", False))
            diag["evidence_contract_missing_minimal_fields"] = list(
                contract.get("missing_minimal_fields") or []
            )
            diag["evidence_contract_missing_minimal_count"] = int(
                len(contract.get("missing_minimal_fields") or [])
            )
            diag["evidence_contract_minimal_coverage_score"] = float(
                contract.get("minimal_coverage_score") or 0.0
            )
            diag["evidence_contract_gate_reason"] = self._evidence_contract_gate_reason(contract)
            self_check = self._self_check_diagnostics(contract)
            diag["self_check"] = self_check
            diag["reasoning_quality"] = self._reasoning_quality_diagnostics(
                answer_text=answer_text,
                provenance=final_state.provenance,
                contract=contract,
            )
            diag["verify"] = self._verify_diagnostics_preflight(
                planner_path_used=True,
                self_check=self_check,
            )
            verify = dict(diag.get("verify") or {})
            planner_actions = [str(x or "") for x in list(getattr(final_state, "plan", []) or [])]
            per_step_results: list[dict[str, object]] = []
            for idx, description in enumerate(planner_actions):
                step_output = answer_text if idx == len(planner_actions) - 1 else description
                per_step_results.append(
                    {
                        "step_index": int(idx),
                        "step_description": str(description or ""),
                        "reasoning_output": str(step_output or ""),
                        "verify_status": str(verify.get("status", "") or ""),
                        "verify_reasons": list(verify.get("reasons") or []),
                    }
                )
            diag["reasoning_trace"] = self._build_reasoning_trace_diagnostics(
                query=str(getattr(request, "query", "") or ""),
                answer_text=answer_text,
                quality=dict(diag.get("reasoning_quality") or {}),
                plan_steps=planner_actions,
                step_results=per_step_results,
            )
            diag["reasoning_timeline"] = dict(
                (dict(diag.get("reasoning_trace") or {}).get("timeline") or {})
            )
            if str(verify.get("status", "")) == "warn":
                resp.warnings = list(getattr(resp, "warnings", []) or [])
                if "verify_warning" not in resp.warnings:
                    resp.warnings.append("verify_warning")
            if str(self_check.get("status", "")) == "warn":
                resp.warnings = list(getattr(resp, "warnings", []) or [])
                if "self_check_warning" not in resp.warnings:
                    resp.warnings.append("self_check_warning")
            if not bool(contract.get("valid_minimal", False)):
                resp.warnings = list(getattr(resp, "warnings", []) or [])
                if "evidence_contract_minimal_invalid" not in resp.warnings:
                    resp.warnings.append("evidence_contract_minimal_invalid")
            if final_state.error:
                diag["agent_error"] = final_state.error
            resp.diagnostics = diag
        except Exception:
            pass

        # Логируем
        try:
            from loguru import logger
            elapsed_ms = int((perf_counter() - t0) * 1000)
            logger.info(
                "reasoning.agent elapsed_ms={} iterations={} conf={}",
                elapsed_ms,
                final_state.iteration_count,
                float(confidence),
            )
        except Exception:
            pass

        return resp

    async def _synthesize_fallback(self, request: AnswerRequest, error: str | None = None) -> AnswerResponse:
        """Fallback к старому однопроходному режиму (если нет LLM или ошибка графа)."""
        from time import perf_counter
        t0 = perf_counter()

        result = await self.retriever.retrieve(request)

        provenance, used_chunks, used_nodes, used_edges, preview_items = normalize_retrieval_result(result)

        context_preview, _ = pack_context(
            preview_items,
            max_chars=int(getattr(request, "max_context_chars", 12000)),
        )
        if not context_preview:
            # A2.1: keep session continuity when retrieval returns empty context.
            context_preview = str(getattr(request, "session_memory_last_answer", "") or "")

        s = get_settings()
        dry_run = bool(getattr(s, "feature_reasoning_llm_dry_run", False))

        fallback_reason: str | None = error or "fallback"
        planner_step_results = await self._execute_planner_steps_mvp(request=request)
        planner_step_count = int(len(planner_step_results or []))
        planner_current_step = int(max(planner_step_count - 1, 0)) if planner_step_count > 0 else 0
        planner_current_action = "ANSWER" if planner_step_count > 0 else ""

        if self.llm is not None and not dry_run:
            # Пробуем вызвать LLM напрямую (один раз)
            from src.layers.pro.reasoning.prompt_builder import build_reasoning_prompt
            import asyncio

            prompt = build_reasoning_prompt(
                request,
                context_preview=context_preview,
                provenance=provenance,
            )
            try:
                answer_text = await asyncio.wait_for(
                    self.llm.generate(prompt),
                    timeout=float(self.llm_timeout_s),
                )
            except Exception:
                answer_text = "(reasoning layer stub)"
        else:
            if dry_run:
                answer_text = self._build_dry_run_answer_from_parts(provenance, context_preview)
            else:
                answer_text = "(reasoning layer stub)"

        confidence = compute_confidence(provenance)

        resp = AnswerResponse(
            answer=answer_text,
            confidence=confidence,
            context_preview=context_preview,
            provenance=provenance,
            used_chunks=[c for c in used_chunks if c],
            used_nodes=[n for n in used_nodes if n],
            used_edges=[e for e in used_edges if e],
        )

        # Добавляем диагностику
        try:
            diag = dict(getattr(resp, "diagnostics", None) or {})
            diag["fallback_reason"] = fallback_reason
            diag.setdefault("agent_current_action", planner_current_action)
            diag.setdefault("agent_current_step", planner_current_step)
            diag.setdefault("planner_path_used", False)
            diag.setdefault("evidence_summary", self._evidence_summary(provenance))
            diag.setdefault("evidence_contract_version", EVIDENCE_CONTRACT_VERSION)
            contract = self._evidence_contract_status(provenance)
            diag.setdefault("evidence_contract", contract)
            diag.setdefault(
                "evidence_contract_valid_minimal",
                bool(contract.get("valid_minimal", False)),
            )
            diag.setdefault(
                "evidence_contract_missing_minimal_fields",
                list(contract.get("missing_minimal_fields") or []),
            )
            diag.setdefault(
                "evidence_contract_missing_minimal_count",
                int(len(contract.get("missing_minimal_fields") or [])),
            )
            diag.setdefault(
                "evidence_contract_minimal_coverage_score",
                float(contract.get("minimal_coverage_score") or 0.0),
            )
            diag.setdefault(
                "evidence_contract_gate_reason",
                self._evidence_contract_gate_reason(contract),
            )
            diag.setdefault("self_check", self._self_check_diagnostics(contract))
            diag.setdefault(
                "reasoning_quality",
                self._reasoning_quality_diagnostics(
                    answer_text=answer_text,
                    provenance=provenance,
                    contract=contract,
                ),
            )
            self_check = dict(diag.get("self_check") or {})
            diag.setdefault(
                "verify",
                self._verify_diagnostics_preflight(
                    planner_path_used=False,
                    self_check=self_check,
                ),
            )
            verify = dict(diag.get("verify") or {})
            fallback_plan_steps = [
                str((row or {}).get("step_description", "") or "")
                for row in list(planner_step_results or [])
            ]
            diag.setdefault(
                "reasoning_trace",
                self._build_reasoning_trace_diagnostics(
                    query=str(getattr(request, "query", "") or ""),
                    answer_text=answer_text,
                    quality=dict(diag.get("reasoning_quality") or {}),
                    plan_steps=fallback_plan_steps,
                    step_results=list(planner_step_results or []),
                ),
            )
            diag.setdefault(
                "reasoning_timeline",
                dict((dict(diag.get("reasoning_trace") or {}).get("timeline") or {})),
            )
            if str(verify.get("status", "")) == "warn":
                resp.warnings = list(getattr(resp, "warnings", []) or [])
                if "verify_warning" not in resp.warnings:
                    resp.warnings.append("verify_warning")
            if str(self_check.get("status", "")) == "warn":
                resp.warnings = list(getattr(resp, "warnings", []) or [])
                if "self_check_warning" not in resp.warnings:
                    resp.warnings.append("self_check_warning")
            if not bool(contract.get("valid_minimal", False)):
                resp.warnings = list(getattr(resp, "warnings", []) or [])
                if "evidence_contract_minimal_invalid" not in resp.warnings:
                    resp.warnings.append("evidence_contract_minimal_invalid")
            resp.diagnostics = diag
        except Exception:
            pass

        return resp

    def _build_dry_run_answer(self, state: AgentState) -> str:
        """Строит dry-run ответ из состояния агента."""
        ids = []
        for p in state.provenance[:5]:
            try:
                ids.append(f"{p.type}:{p.id}")
            except Exception:
                continue

        snippet = (state.context_preview or "").strip()
        if len(snippet) > 400:
            snippet = snippet[:400].rstrip() + "…"

        parts = []
        if snippet:
            parts.append("Draft answer (dry-run):")
            parts.append(snippet)
        else:
            parts.append("Draft answer (dry-run): (no context)")

        if ids:
            parts.append("")
            parts.append("Evidence:")
            for x in ids:
                parts.append(f"- {x}")

        return "\n".join(parts)

    def _build_dry_run_answer_from_parts(self, provenance: list, context_preview: str) -> str:
        """Строит dry-run ответ из частей (для fallback)."""
        ids = []
        for p in provenance[:5]:
            try:
                ids.append(f"{p.type}:{p.id}")
            except Exception:
                continue

        snippet = (context_preview or "").strip()
        if len(snippet) > 400:
            snippet = snippet[:400].rstrip() + "…"

        parts = []
        if snippet:
            parts.append("Draft answer (dry-run):")
            parts.append(snippet)
        else:
            parts.append("Draft answer (dry-run): (no context)")

        if ids:
            parts.append("")
            parts.append("Evidence:")
            for x in ids:
                parts.append(f"- {x}")

        return "\n".join(parts)
