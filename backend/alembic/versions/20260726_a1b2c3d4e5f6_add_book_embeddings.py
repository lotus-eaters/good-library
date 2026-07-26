"""add book embeddings

Revision ID: a1b2c3d4e5f6
Revises: 0ae35902714d
Create Date: 2026-07-26 10:00:00.000000
"""
from alembic import op

revision = 'a1b2c3d4e5f6'
down_revision = '0ae35902714d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extension created manually as superuser before running this migration
    op.execute("ALTER TABLE books ADD COLUMN IF NOT EXISTS embedding vector(1536)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS books_embedding_idx "
        "ON books USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS books_embedding_idx")
    op.execute("ALTER TABLE books DROP COLUMN IF EXISTS embedding")
