"""Slots compartilhados entre API e workers.

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
"""
from alembic import op
import sqlalchemy as sa

revision = "d3e4f5a6b7c8"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        UPDATE processing_jobs SET status = 'cancelled', error = 'Tarefa ativa duplicada consolidada na migração'
        WHERE target_id IS NOT NULL AND status IN ('pending', 'running')
        AND id NOT IN (
            SELECT MIN(id) FROM processing_jobs
            WHERE target_id IS NOT NULL AND status IN ('pending', 'running') GROUP BY job_type, target_id
        )
    """)
    op.create_index(
        "uq_processing_jobs_active_target", "processing_jobs", ["job_type", "target_id"], unique=True,
        sqlite_where=sa.text("target_id IS NOT NULL AND status IN ('pending', 'running')"),
        postgresql_where=sa.text("target_id IS NOT NULL AND status IN ('pending', 'running')"),
    )
    op.create_table(
        "resource_leases",
        sa.Column("name", sa.String(64), primary_key=True),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.add_column("processing_jobs", sa.Column("execution_token", sa.String(64), nullable=True))


def downgrade():
    op.drop_index("uq_processing_jobs_active_target", table_name="processing_jobs")
    op.drop_column("processing_jobs", "execution_token")
    op.drop_table("resource_leases")
