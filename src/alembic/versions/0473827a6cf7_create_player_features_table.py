"""create player_features table

Cria a tabela `player_features` conforme especificado no design da change
`add-worker-subscriber` (ver ADR 0008): histórico de features agregadas
por lote de eventos processado pelo worker subscriber, com um índice
composto em `(player_id, id)` para buscar eficientemente a linha mais
recente de um jogador.

Revision ID: 0473827a6cf7
Revises: 3977097f2a32
Create Date: 2026-09-11 22:39:17.936150

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0473827a6cf7"
down_revision: str | Sequence[str] | None = "3977097f2a32"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria a tabela `player_features` e o índice composto `(player_id, id)`."""
    op.create_table(
        "player_features",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("player_id", sa.String(100), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("n_events", sa.Integer, nullable=False),
        sa.Column("pct_attack", sa.Float, nullable=False),
        sa.Column("pct_explore", sa.Float, nullable=False),
        sa.Column("pct_social", sa.Float, nullable=False),
        sa.Column("pct_quest_complete", sa.Float, nullable=False),
        sa.Column("pct_retry", sa.Float, nullable=False),
        sa.Column("avg_decision_time_ms", sa.Float, nullable=False),
        sa.Column("fail_rate", sa.Float, nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sqlite_autoincrement=True,
    )
    op.create_index(
        "ix_player_features_player_id_id",
        "player_features",
        ["player_id", "id"],
    )


def downgrade() -> None:
    """Remove o índice composto e a tabela `player_features`."""
    op.drop_index("ix_player_features_player_id_id", table_name="player_features")
    op.drop_table("player_features")
