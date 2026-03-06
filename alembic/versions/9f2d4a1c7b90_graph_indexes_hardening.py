"""graph indexes hardening

Revision ID: 9f2d4a1c7b90
Revises: 13c1a7ddc173
Create Date: 2026-03-06 18:40:00.000000
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9f2d4a1c7b90"
down_revision: Union[str, Sequence[str], None] = "13c1a7ddc173"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add graph indexes for common GraphRAG access patterns."""
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_graph_nodes_ws_name "
        "ON graph_nodes (workspace_id, name)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_graph_nodes_ws_type "
        "ON graph_nodes (workspace_id, node_type)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_graph_edges_ws_src "
        "ON graph_edges (workspace_id, src_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_graph_edges_ws_dst "
        "ON graph_edges (workspace_id, dst_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_graph_edges_ws_rel_type "
        "ON graph_edges (workspace_id, rel_type)"
    )


def downgrade() -> None:
    """Drop indexes introduced by this migration."""
    op.execute("DROP INDEX IF EXISTS ix_graph_edges_ws_rel_type")
    op.execute("DROP INDEX IF EXISTS ix_graph_edges_ws_dst")
    op.execute("DROP INDEX IF EXISTS ix_graph_edges_ws_src")
    op.execute("DROP INDEX IF EXISTS ix_graph_nodes_ws_type")
    op.execute("DROP INDEX IF EXISTS ix_graph_nodes_ws_name")
