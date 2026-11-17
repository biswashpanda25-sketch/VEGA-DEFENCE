"""spatial GiST index on the geography expression used by /geo/nearby

Revision ID: 7c1d9a4e2b10
Revises: 5facbe099d8e
"""
from alembic import op

revision = "7c1d9a4e2b10"
down_revision = "5facbe099d8e"
branch_labels = None
depends_on = None

EXPR = "(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography)"


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(f"CREATE INDEX IF NOT EXISTS ix_entities_geog ON entities USING gist ({EXPR})")
    op.execute("CREATE INDEX IF NOT EXISTS ix_entities_name_trgm "
               "ON entities USING gin (name gin_trgm_ops)")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("DROP INDEX IF EXISTS ix_entities_geog")
    op.execute("DROP INDEX IF EXISTS ix_entities_name_trgm")
