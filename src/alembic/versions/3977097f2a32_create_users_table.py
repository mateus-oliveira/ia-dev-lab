"""create users table

Cria a tabela `users` conforme especificado na ADR 0004, reproduzindo o
schema que hoje era criado por `init_db()` (ver ADR 0006).

Revision ID: 3977097f2a32
Revises:
Create Date: 2026-09-11 17:30:00.142217

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "3977097f2a32"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria a tabela `users` com o schema definido na ADR 0004."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("password", sa.String(255), nullable=False),
        sqlite_autoincrement=True,
    )


def downgrade() -> None:
    """Remove a tabela `users`."""
    op.drop_table("users")
