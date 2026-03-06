from src.infrastructure.database.models.graph_node import GraphNode
from src.infrastructure.database.models.graph_edge import GraphEdge


def _index_names(table) -> set[str]:
    return {idx.name for idx in table.indexes}


def test_graph_node_has_workspace_scoped_indexes():
    names = _index_names(GraphNode.__table__)
    assert "ix_graph_nodes_ws_nodeid" in names
    assert "ix_graph_nodes_ws_name" in names
    assert "ix_graph_nodes_ws_type" in names


def test_graph_edge_has_workspace_scoped_indexes():
    names = _index_names(GraphEdge.__table__)
    assert "ix_graph_edges_ws_edgeid" in names
    assert "ix_graph_edges_ws_src_dst" in names
    assert "ix_graph_edges_ws_src" in names
    assert "ix_graph_edges_ws_dst" in names
    assert "ix_graph_edges_ws_rel_type" in names
