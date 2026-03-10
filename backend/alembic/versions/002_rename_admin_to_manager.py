# alembic/versions/002_rename_admin_to_manager.py
# 팀 역할 enum에서 'admin'을 'manager'로 변경하는 마이그레이션
"""rename team_role admin to manager

Revision ID: 002_rename_admin
Revises: 001_initial
Create Date: 2026-03-08
"""
from alembic import op

revision = "002_rename_admin"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL enum에 'manager' 값을 추가한 뒤 기존 'admin'을 'manager'로 변환
    op.execute("ALTER TYPE team_role ADD VALUE IF NOT EXISTS 'manager'")
    # 트랜잭션 커밋 후 새 enum 값 사용이 가능하므로 별도 실행
    op.execute("COMMIT")
    op.execute(
        "UPDATE team_members SET role = 'manager' WHERE role = 'admin'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE team_members SET role = 'admin' WHERE role = 'manager'"
    )
