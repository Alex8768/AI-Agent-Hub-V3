from typing import Any
from functools import partial

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
    builder.add_node("think", partial(think_node, llm=llm))
    builder.add_node("search", partial(search_node, retriever=retriever))
    builder.add_node("reason", partial(reason_node, llm=llm))
    builder.add_node("answer", partial(answer_node, llm=llm))
    
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
