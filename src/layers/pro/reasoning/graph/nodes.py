import json
from typing import Dict, Any, List, Optional

from src.layers.pro.reasoning.graph.state import AgentState
from src.layers.pro.reasoning.prompt_builder import build_reasoning_prompt
from src.core.exceptions import LLMError


async def think_node(state: AgentState, llm: Any) -> AgentState:
    """
    Узел "мышления": анализирует состояние и решает, что делать дальше.
    
    Возможные действия:
    - SEARCH: выполнить поиск (вызов ретривера)
    - REASON: сделать логический вывод
    - ANSWER: дать финальный ответ
    - TOOL: вызвать инструмент (позже)
    """
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
        
        # Логируем
        state.messages.append({"role": "assistant", "content": f"Action: {action} ({reason})"})
        
        # Обновляем план (если нужно)
        if action not in ["ANSWER"]:
            state.plan.append(action)
        
        # Сохраняем выбранное действие в состоянии для следующего узла
        state.current_action = action
        
    except Exception as e:
        state.error = f"Think node failed: {str(e)}"
        state.current_action = "ANSWER"  # fallback
    
    state.iteration_count += 1
    return state


async def search_node(state: AgentState, retriever: Any) -> AgentState:
    """
    Узел поиска: вызывает ретривер для получения дополнительной информации.
    """
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
        state.error = f"Search node failed: {str(e)}"
    
    return state


async def reason_node(state: AgentState, llm: Any) -> AgentState:
    """
    Узел рассуждения: делает логический вывод на основе имеющихся свидетельств.
    """
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
        state.messages.append({"role": "assistant", "content": f"Reasoning: {reasoning}"})
    except Exception as e:
        state.error = f"Reason node failed: {str(e)}"
    
    return state


async def answer_node(state: AgentState, llm: Any) -> AgentState:
    """
    Узел ответа: генерирует финальный ответ пользователю.
    """
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
        state.final_answer = answer
        state.messages.append({"role": "assistant", "content": f"Final answer: {answer[:100]}..."})
    except Exception as e:
        state.error = f"Answer node failed: {str(e)}"
        state.final_answer = "(reasoning layer stub)"
    
    return state
