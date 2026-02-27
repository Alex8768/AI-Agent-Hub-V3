from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

from src.layers.pro.reasoning.contracts import ProvenanceItem


class AgentState(BaseModel):
    """Состояние агента для графа рассуждений."""
    
    # Входные данные
    query: str
    workspace_id: str
    k: int = 8
    graph_depth: int = 1
    max_context_chars: int = 12000
    
    # Текущий контекст
    messages: List[Dict[str, str]] = Field(default_factory=list)  # роль, контент
    plan: List[str] = Field(default_factory=list)  # список запланированных действий
    current_step: int = 0
    
    # Накопленные свидетельства
    provenance: List[ProvenanceItem] = Field(default_factory=list)
    used_chunks: List[str] = Field(default_factory=list)
    used_nodes: List[str] = Field(default_factory=list)
    used_edges: List[str] = Field(default_factory=list)
    
    # Промежуточные результаты
    context_preview: str = ""
    final_answer: Optional[str] = None
    
    # Диагностика
    error: Optional[str] = None
    iteration_count: int = 0
    max_iterations: int = 10
    
    class Config:
        arbitrary_types_allowed = True
