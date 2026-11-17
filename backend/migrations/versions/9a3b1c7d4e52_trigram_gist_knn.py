"""GiST trigram index for KNN similarity ordering

Revision ID: 9a3b1c7d4e52
Revises: 8d2e0f5a3c21
"""
from alembic import op

revision = "9a3b1c7d4e52"
down_revision = "8d2e0f5a3c21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    op.execute("CREATE INDEX IF NOT EXISTS ix_entities_name_gist "
               "ON entities USING gist (name gist_trgm_ops)")


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    op.execute("DROP INDEX IF EXISTS ix_entities_name_gist")
