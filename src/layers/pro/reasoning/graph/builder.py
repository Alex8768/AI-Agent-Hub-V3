from typing import Any

from langgraph.graph import StateGraph, END

from src.layers.pro.reasoning.graph.state import AgentState
from src.layers.pro.reasoning.graph.nodes import think_node, search_node, reason_node, answer_node


def build_reasoning_graph(llm: Any, retriever: Any) -> StateGraph:
    """
    Строит граф рассуждений с циклами.
    """
    # Определяем conditional edge: на основе current_action выбираем следующий узел
    def route_action(state: AgentState) -> str:
        action = getattr(state, "current_action", "REASON")
        if action == "SEARCH":
            return "search"
        elif action == "REASON":
            return "reason"
        elif action == "ANSWER":
            return "answer"
        else:
            return "reason"  # fallback
    
    # Создаём граф
    builder = StateGraph(AgentState)
    
    # Добавляем узлы
    builder.add_node("think", lambda state: think_node(state, llm))
    builder.add_node("search", lambda state: search_node(state, retriever))
    builder.add_node("reason", lambda state: reason_node(state, llm))
    builder.add_node("answer", answer_node)
    
    # Устанавливаем входную точку
    builder.set_entry_point("think")
    
    # Добавляем conditional edges из think
    builder.add_conditional_edges("think", route_action)
    
    # После search и reason возвращаемся к think (цикл)
    builder.add_edge("search", "think")
    builder.add_edge("reason", "think")
    
    # answer завершает граф
    builder.add_edge("answer", END)
    
    return builder
