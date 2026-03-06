import json
from typing import Dict, Any, List, Optional
# Optional OpenTelemetry (CI may not install it)
try:
    from opentelemetry import trace as _otel_trace  # type: ignore
except Exception:  # pragma: no cover
    _otel_trace = None

class _NoopSpan:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

class _NoopTracer:
    def start_as_current_span(self, *args, **kwargs):
        return _NoopSpan()

class _TraceShim:
    def get_tracer(self, name: str):
        if _otel_trace is not None:
            return _otel_trace.get_tracer(name)
        return _NoopTracer()

trace = _TraceShim()

from src.layers.pro.reasoning.graph.state import AgentState
from src.layers.pro.reasoning.prompt_builder import build_reasoning_prompt
from src.core.exceptions import LLMError

# Получаем трейсер
tracer = trace.get_tracer(__name__)


async def think_node(state: AgentState, llm: Any) -> AgentState:
    """
    Узел "мышления": анализирует состояние и решает, что делать дальше.
    
    Возможные действия:
    - SEARCH: выполнить поиск (вызов ретривера)
    - REASON: сделать логический вывод
    - ANSWER: дать финальный ответ
    - TOOL: вызвать инструмент (позже)
    """
    with tracer.start_as_current_span("agent.think") as span:
        span.set_attribute("agent.iteration", state.iteration_count)
        span.set_attribute("agent.current_action", getattr(state, "current_action", "unknown"))

        # Hard stop for planner loop safety.
        if int(getattr(state, "iteration_count", 0) or 0) >= int(getattr(state, "max_iterations", 10) or 10):
            state.current_action = "ANSWER"
            state.messages.append({"role": "system", "content": "Planner reached max_iterations; forcing ANSWER"})
            state.iteration_count += 1
            return state
        
        # Собираем контекст для промпта
        prompt = build_reasoning_prompt(
            query=state.query,
            context_preview=state.context_preview,
            provenance=state.provenance,
            instruction=(
                "You are a reasoning agent. Based on the current state, decide the next action.\n"
                "Available actions:\n"
                "- SEARCH: retrieve more information from the knowledge base\n"
                "- REASON: perform logical deduction based on available evidence\n"
                "- ANSWER: provide the final answer to the user\n\n"
                "Output format: {\"action\": \"ACTION_NAME\", \"reason\": \"why this action\"}\n"
                "Output ONLY valid JSON, no other text."
            )
        )
        
        try:
            response = await llm.generate(prompt)
            # Парсим JSON (предпочтительный формат). If raw text is returned,
            # recover action from keywords to keep planner flow robust.
            txt = str(response or "").strip()
            try:
                data = json.loads(txt)
            except Exception:
                up = txt.upper()
                if "SEARCH" in up:
                    data = {"action": "SEARCH", "reason": "parsed from plain text"}
                elif "REASON" in up:
                    data = {"action": "REASON", "reason": "parsed from plain text"}
                elif "ANSWER" in up:
                    data = {"action": "ANSWER", "reason": "parsed from plain text"}
                else:
                    raise
            raw_plan = data.get("plan")
            parsed_plan: list[str] = []
            if isinstance(raw_plan, list):
                allowed = {"SEARCH", "REASON", "ANSWER"}
                for item in raw_plan:
                    step = str(item or "").strip().upper()
                    if step in allowed:
                        parsed_plan.append(step)
                parsed_plan = parsed_plan[:5]
                if parsed_plan:
                    state.plan = parsed_plan

            allowed_actions = {"SEARCH", "REASON", "ANSWER"}
            action = str(data.get("action") or "").strip().upper()
            if parsed_plan:
                # Planner is the source of truth for routing when structured plan exists.
                step_idx = int(getattr(state, "current_step", 0) or 0)
                if step_idx < 0:
                    step_idx = 0
                if step_idx >= len(parsed_plan):
                    step_idx = len(parsed_plan) - 1
                action = parsed_plan[step_idx]
                if step_idx < len(parsed_plan) - 1:
                    state.current_step = step_idx + 1
                else:
                    state.current_step = step_idx
            if not action or action not in allowed_actions:
                action = "REASON"
            reason = data.get("reason", "")
            
            # Добавляем атрибуты в спан
            span.set_attribute("agent.decision.action", action)
            span.set_attribute("agent.decision.reason", reason)
            
            # Логируем
            state.messages.append({"role": "assistant", "content": f"Action: {action} ({reason})"})
            
            # Обновляем план (если нужно)
            if action not in ["ANSWER"] and not parsed_plan:
                state.plan.append(action)
            
            # Сохраняем выбранное действие в состоянии для следующего узла
            state.current_action = action
            
        except Exception as e:
            span.record_exception(e)
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            state.error = f"Think node failed: {str(e)}"
            state.current_action = "ANSWER"  # fallback
        
        state.iteration_count += 1
        return state


async def search_node(state: AgentState, retriever: Any) -> AgentState:
    """
    Узел поиска: вызывает ретривер для получения дополнительной информации.
    """
    with tracer.start_as_current_span("agent.search") as span:
        span.set_attribute("agent.iteration", state.iteration_count)
        span.set_attribute("agent.query", state.query)
        
        try:
            # Вызываем гибридный ретривер
            result = await retriever.retrieve(
                query=state.query,
                k=state.k,
                graph_depth=state.graph_depth,
            )
            
            # Обновляем состояние из результатов поиска
            from src.layers.pro.reasoning.evidence_normalizer import normalize_retrieval_result
            
            prov, chunks, nodes, edges, preview_items = normalize_retrieval_result({
                "results": [{"chunk_id": c} for c in getattr(result, "results", [])],
                "graph": getattr(result, "graph", {}),
                "evidence": getattr(result, "evidence", [])
            })
            
            # Добавляем метрики в спан
            span.set_attribute("evidence.provenance_count", len(prov))
            span.set_attribute("evidence.chunks_count", len(chunks))
            span.set_attribute("evidence.nodes_count", len(nodes))
            span.set_attribute("evidence.edges_count", len(edges))
            
            state.provenance.extend(prov)
            state.used_chunks.extend(chunks)
            state.used_nodes.extend(nodes)
            state.used_edges.extend(edges)
            
            # Обновляем контекст
            from src.layers.pro.reasoning.context_packer import pack_context
            context, _ = pack_context(preview_items, max_chars=state.max_context_chars)
            state.context_preview = context
            
            state.messages.append({"role": "system", "content": f"Retrieved {len(prov)} evidence items"})
            
        except Exception as e:
            span.record_exception(e)
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            state.error = f"Search node failed: {str(e)}"
        
        return state


async def reason_node(state: AgentState, llm: Any) -> AgentState:
    """
    Узел рассуждения: делает логический вывод на основе имеющихся свидетельств.
    """
    with tracer.start_as_current_span("agent.reason") as span:
        span.set_attribute("agent.iteration", state.iteration_count)
        span.set_attribute("evidence.provenance_count", len(state.provenance))
        
        prompt = build_reasoning_prompt(
            query=state.query,
            context_preview=state.context_preview,
            provenance=state.provenance,
            instruction=(
                "Based on the evidence above, provide a partial reasoning step. "
                "Do not give the final answer yet, just the next logical inference."
            )
        )
        
        try:
            reasoning = await llm.generate(prompt)
            span.set_attribute("reasoning.length", len(reasoning))
            state.messages.append({"role": "assistant", "content": f"Reasoning: {reasoning}"})
        except Exception as e:
            span.record_exception(e)
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            state.error = f"Reason node failed: {str(e)}"
        
        return state


async def answer_node(state: AgentState, llm: Any) -> AgentState:
    """
    Узел ответа: генерирует финальный ответ пользователю.
    """
    with tracer.start_as_current_span("agent.answer") as span:
        span.set_attribute("agent.iteration", state.iteration_count)
        span.set_attribute("evidence.total_count", len(state.provenance))
        
        prompt = build_reasoning_prompt(
            query=state.query,
            context_preview=state.context_preview,
            provenance=state.provenance,
            instruction=(
                "Based on all available evidence, provide a comprehensive final answer. "
                "If the evidence is insufficient, say so."
            )
        )
        
        try:
            answer = await llm.generate(prompt)
            span.set_attribute("answer.length", len(answer))
            state.final_answer = answer
            state.messages.append({"role": "assistant", "content": f"Final answer: {answer[:100]}..."})
        except Exception as e:
            span.record_exception(e)
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            state.error = f"Answer node failed: {str(e)}"
            state.final_answer = "(reasoning layer stub)"
        
        return state
