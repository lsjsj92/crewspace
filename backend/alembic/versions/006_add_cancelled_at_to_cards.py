# alembic/versions/006_add_cancelled_at_to_cards.py
# cards 테이블에 cancelled_at 컬럼 추가 마이그레이션
"""add cancelled_at to cards

Revision ID: 006_add_cancelled_at
Revises: 005_partial_unique
Create Date: 2026-03-30
"""
import sqlalchemy as sa
from alembic import op

revision = "006_add_cancelled_at"
down_revision = "005_partial_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cards",
        sa.Column(
            "cancelled_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("cards", "cancelled_at")
