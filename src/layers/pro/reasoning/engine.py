from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from src.layers.pro.reasoning.graph.builder import build_reasoning_graph
from src.layers.pro.reasoning.graph.state import AgentState
from src.layers.pro.reasoning.contracts import AnswerRequest, AnswerResponse
from src.layers.pro.reasoning.confidence import compute_confidence
from src.layers.pro.reasoning.evidence_normalizer import normalize_retrieval_result
from src.layers.pro.reasoning.context_packer import pack_context
from src.core.config import get_settings


@dataclass(frozen=True, slots=True)
class ReasoningEngine:
    """Graph-aware reasoning answer synthesis (Pro) with agentic loop."""

    retriever: object
    llm: object | None = None
    llm_timeout_s: float = 15.0

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
            final_state = await graph.ainvoke(initial_state)
        except Exception as e:
            # В случае ошибки графа - падаем на старый путь
            return await self._synthesize_fallback(request, error=str(e))

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
            diag["session_id"] = str(getattr(final_state, "session_id", "") or "")
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
            diag.setdefault("agent_current_action", "")
            diag.setdefault("agent_current_step", 0)
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
