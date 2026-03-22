# alembic/versions/004_add_sub_task_card_type.py
"""add sub_task to card_type enum

Revision ID: 004_add_sub_task
Revises: 003_project_members
Create Date: 2026-03-10
"""
from alembic import op

revision = "004_add_sub_task"
down_revision = "003_project_members"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("COMMIT")
    op.execute("ALTER TYPE card_type ADD VALUE IF NOT EXISTS 'sub_task'")
    op.execute("BEGIN")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values
    # A full migration would need to recreate the type
    pass
