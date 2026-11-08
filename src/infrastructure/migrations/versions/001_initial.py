"""Create GUIDE v1.0.0 tables and the import audit trail."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.infrastructure.schema import SCHEMA, build_metadata, load_model

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute(f'CREATE SCHEMA "{SCHEMA}"')
    build_metadata(load_model()).create_all(op.get_bind())
    op.create_table(
        "import_audit_trail",
        sa.Column("import_id", UUID(as_uuid=False), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=False)),
        sa.Column("total_records", sa.BigInteger, nullable=False),
        sa.Column("failed_records", sa.BigInteger, nullable=False),
        sa.Column("validation_errors", JSONB, nullable=False),
        sa.Column("created_by", sa.Text, nullable=False),
        schema=SCHEMA,
    )


def downgrade():
    op.drop_table("import_audit_trail", schema=SCHEMA)
    build_metadata(load_model()).drop_all(op.get_bind())
    op.execute(f'DROP SCHEMA "{SCHEMA}"')
