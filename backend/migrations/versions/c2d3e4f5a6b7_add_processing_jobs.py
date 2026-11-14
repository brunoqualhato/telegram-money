"""add_processing_jobs

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
"""

from alembic import op
import sqlalchemy as sa


revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("category", sa.String(length=32), nullable=False, server_default="ai"),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("target_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.String(length=500), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_processing_jobs_category", "processing_jobs", ["category"])
    op.create_index("ix_processing_jobs_job_type", "processing_jobs", ["job_type"])
    op.create_index("ix_processing_jobs_status", "processing_jobs", ["status"])
    op.create_index("ix_processing_jobs_target_id", "processing_jobs", ["target_id"])
    op.create_index("ix_processing_jobs_priority", "processing_jobs", ["priority"])
    op.create_index("ix_processing_jobs_created_at", "processing_jobs", ["created_at"])


def downgrade():
    op.drop_table("processing_jobs")
