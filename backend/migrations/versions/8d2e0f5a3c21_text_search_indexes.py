"""trigram indexes for entity text search (/entities?q=, /search)

Revision ID: 8d2e0f5a3c21
Revises: 7c1d9a4e2b10
"""
from alembic import op

revision = "8d2e0f5a3c21"
down_revision = "7c1d9a4e2b10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    op.execute("CREATE INDEX IF NOT EXISTS ix_entities_description_trgm "
               "ON entities USING gin (description gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_entities_name_trgm "
               "ON entities USING gin (name gin_trgm_ops)")


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    op.execute("DROP INDEX IF EXISTS ix_entities_description_trgm")
