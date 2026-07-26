"""resize embedding to 384 dimensions (HuggingFace MiniLM)

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-07-26 11:00:00.000000
"""
from alembic import op

revision = 'b2c3d4e5f6a1'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS books_embedding_idx")
    op.execute("ALTER TABLE books DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE books ADD COLUMN embedding vector(384)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS books_embedding_idx "
        "ON books USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS books_embedding_idx")
    op.execute("ALTER TABLE books DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE books ADD COLUMN embedding vector(1536)")
