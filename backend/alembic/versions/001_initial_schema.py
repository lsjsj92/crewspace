# alembic/versions/001_initial_schema.py
# 초기 데이터베이스 스키마 마이그레이션 - 모든 테이블 생성
"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-03-08
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Enum 타입 생성 ---
    team_role = postgresql.ENUM("owner", "admin", "member", "viewer", name="team_role", create_type=False)
    team_role.create(op.get_bind(), checkfirst=True)

    project_status = postgresql.ENUM("active", "completed", "archived", name="project_status", create_type=False)
    project_status.create(op.get_bind(), checkfirst=True)

    card_type = postgresql.ENUM("epic", "story", "task", name="card_type", create_type=False)
    card_type.create(op.get_bind(), checkfirst=True)

    card_priority = postgresql.ENUM("lowest", "low", "medium", "high", "highest", name="card_priority", create_type=False)
    card_priority.create(op.get_bind(), checkfirst=True)

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("username", sa.String(100), unique=True, nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_superadmin", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- teams ---
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- team_members ---
    op.create_table(
        "team_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", postgresql.ENUM("owner", "admin", "member", "viewer", name="team_role", create_type=False), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("team_id", "user_id", name="uq_team_members_team_user"),
    )

    # --- projects ---
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("prefix", sa.String(10), nullable=False),
        sa.Column("status", postgresql.ENUM("active", "completed", "archived", name="project_status", create_type=False), nullable=False, server_default="active"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("team_id", "prefix", name="uq_projects_team_prefix"),
    )

    # --- board_columns ---
    op.create_table(
        "board_columns",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.Column("is_end", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("wip_limit", sa.SmallInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("project_id", "position", name="uq_board_columns_project_position"),
    )

    # --- cards ---
    op.create_table(
        "cards",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("column_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("board_columns.id"), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cards.id"), nullable=True),
        sa.Column("card_type", postgresql.ENUM("epic", "story", "task", name="card_type", create_type=False), nullable=False),
        sa.Column("card_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", postgresql.ENUM("lowest", "low", "medium", "high", "highest", name="card_priority", create_type=False), nullable=False, server_default="medium"),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("project_id", "card_number", name="uq_cards_project_card_number"),
    )

    # --- card_assignees ---
    op.create_table(
        "card_assignees",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cards.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("card_id", "user_id", name="uq_card_assignees_card_user"),
    )

    # --- labels ---
    op.create_table(
        "labels",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("color", sa.String(7), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("project_id", "name", name="uq_labels_project_name"),
    )

    # --- card_labels ---
    op.create_table(
        "card_labels",
        sa.Column("card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cards.id"), primary_key=True),
        sa.Column("label_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("labels.id"), primary_key=True),
    )

    # --- card_comments ---
    op.create_table(
        "card_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cards.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- project_outcomes ---
    op.create_table(
        "project_outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("achieved_at", sa.Date(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- audit_logs ---
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cards.id"), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- refresh_tokens ---
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(255), unique=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- 성능을 위한 인덱스 생성 ---
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_cards_project_id", "cards", ["project_id"])
    op.create_index("ix_cards_column_id", "cards", ["column_id"])
    op.create_index("ix_cards_created_by", "cards", ["created_by"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_project_id", "audit_logs", ["project_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])


def downgrade() -> None:
    # 역순으로 테이블 삭제
    op.drop_table("refresh_tokens")
    op.drop_table("audit_logs")
    op.drop_table("project_outcomes")
    op.drop_table("card_comments")
    op.drop_table("card_labels")
    op.drop_table("labels")
    op.drop_table("card_assignees")
    op.drop_table("cards")
    op.drop_table("board_columns")
    op.drop_table("projects")
    op.drop_table("team_members")
    op.drop_table("teams")
    op.drop_table("users")

    # Enum 타입 삭제
    sa.Enum(name="card_priority").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="card_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="project_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="team_role").drop(op.get_bind(), checkfirst=True)
