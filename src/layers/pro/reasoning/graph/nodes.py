import json
from typing import Dict, Any, List, Optional
from opentelemetry import trace

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
            # Парсим JSON
            data = json.loads(response.strip())
            action = data.get("action", "REASON")
            reason = data.get("reason", "")
            
            # Добавляем атрибуты в спан
            span.set_attribute("agent.decision.action", action)
            span.set_attribute("agent.decision.reason", reason)
            
            # Логируем
            state.messages.append({"role": "assistant", "content": f"Action: {action} ({reason})"})
            
            # Обновляем план (если нужно)
            if action not in ["ANSWER"]:
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
