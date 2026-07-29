# alembic/versions/007_add_card_links.py
# 카드 다중 부모 지원을 위한 card_links 테이블 추가 마이그레이션
"""add card_links table for multi-parent support

Revision ID: 007_add_card_links
Revises: 006_add_cancelled_at
Create Date: 2026-07-21
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "007_add_card_links"
down_revision = "006_add_cancelled_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "card_links",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("card_id", UUID(as_uuid=True), sa.ForeignKey("cards.id"), nullable=False),
        sa.Column("parent_id", UUID(as_uuid=True), sa.ForeignKey("cards.id"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("card_id", "parent_id", name="uq_card_links_card_parent"),
    )
    op.create_index("ix_card_links_parent_id", "card_links", ["parent_id"])


def downgrade() -> None:
    op.drop_index("ix_card_links_parent_id", table_name="card_links")
    op.drop_table("card_links")
