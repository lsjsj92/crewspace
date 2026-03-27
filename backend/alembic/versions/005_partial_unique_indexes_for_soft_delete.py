# alembic/versions/005_partial_unique_indexes_for_soft_delete.py
# soft-delete 모델의 UniqueConstraint를 partial unique index로 교체
# deleted_at IS NULL 조건으로 활성 행에만 unique 적용
"""replace unique constraints with partial unique indexes for soft-delete

Revision ID: 005_partial_unique
Revises: 004_add_sub_task
Create Date: 2026-03-27
"""
import sqlalchemy as sa
from alembic import op

revision = "005_partial_unique"
down_revision = "004_add_sub_task"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── board_columns: (project_id, position) ──
    op.drop_constraint(
        "uq_board_columns_project_position", "board_columns", type_="unique"
    )
    op.create_index(
        "uq_board_columns_project_position_active",
        "board_columns",
        ["project_id", "position"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── users: email ──
    # column-level unique=True → 자동 생성된 constraint 이름: users_email_key
    op.drop_index("ix_users_email", table_name="users")
    op.drop_constraint("users_email_key", "users", type_="unique")
    op.create_index(
        "uq_users_email_active",
        "users",
        ["email"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── users: username ──
    op.drop_index("ix_users_username", table_name="users")
    op.drop_constraint("users_username_key", "users", type_="unique")
    op.create_index(
        "uq_users_username_active",
        "users",
        ["username"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── users: employee_id ──
    op.drop_constraint("users_employee_id_key", "users", type_="unique")
    op.create_index(
        "uq_users_employee_id_active",
        "users",
        ["employee_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── users: gw_id ──
    op.drop_constraint("users_gw_id_key", "users", type_="unique")
    op.create_index(
        "uq_users_gw_id_active",
        "users",
        ["gw_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── projects: prefix ──
    op.drop_constraint("uq_projects_prefix", "projects", type_="unique")
    op.create_index(
        "uq_projects_prefix_active",
        "projects",
        ["prefix"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── cards: (project_id, card_number) ──
    op.drop_constraint(
        "uq_cards_project_card_number", "cards", type_="unique"
    )
    op.create_index(
        "uq_cards_project_card_number_active",
        "cards",
        ["project_id", "card_number"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── labels: (project_id, name) ──
    op.drop_constraint("uq_labels_project_name", "labels", type_="unique")
    op.create_index(
        "uq_labels_project_name_active",
        "labels",
        ["project_id", "name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    # soft-deleted 행 중 중복 값이 있으면 원래 constraint 복원 시 실패할 수 있으므로
    # 먼저 soft-deleted 행의 중복 값을 정리한다

    # ── users: soft-deleted 중복 정리 ──
    op.execute(
        """
        UPDATE users
        SET email = email || '_deleted_' || LEFT(id::text, 8)
        WHERE deleted_at IS NOT NULL
          AND email IN (
              SELECT email FROM users GROUP BY email HAVING COUNT(*) > 1
          )
        """
    )
    op.execute(
        """
        UPDATE users
        SET username = username || '_deleted_' || LEFT(id::text, 8)
        WHERE deleted_at IS NOT NULL
          AND username IN (
              SELECT username FROM users GROUP BY username HAVING COUNT(*) > 1
          )
        """
    )
    op.execute(
        """
        UPDATE users
        SET employee_id = employee_id || '_d' || LEFT(id::text, 8)
        WHERE deleted_at IS NOT NULL
          AND employee_id IN (
              SELECT employee_id FROM users GROUP BY employee_id HAVING COUNT(*) > 1
          )
        """
    )
    op.execute(
        """
        UPDATE users
        SET gw_id = gw_id || '_d' || LEFT(id::text, 8)
        WHERE deleted_at IS NOT NULL
          AND gw_id IN (
              SELECT gw_id FROM users GROUP BY gw_id HAVING COUNT(*) > 1
          )
        """
    )

    # ── projects: soft-deleted prefix 중복 정리 (prefix는 10자 제한이므로 절삭) ──
    op.execute(
        """
        UPDATE projects
        SET prefix = LEFT(prefix || '_d' || LEFT(id::text, 4), 10)
        WHERE deleted_at IS NOT NULL
          AND prefix IN (
              SELECT prefix FROM projects GROUP BY prefix HAVING COUNT(*) > 1
          )
        """
    )

    # ── board_columns: soft-deleted position 중복 정리 ──
    op.execute(
        """
        UPDATE board_columns
        SET position = position + 10000 + (
            ROW_NUMBER() OVER (PARTITION BY project_id ORDER BY id)
        )::int
        FROM (
            SELECT project_id, position
            FROM board_columns
            GROUP BY project_id, position
            HAVING COUNT(*) > 1
        ) dup
        WHERE board_columns.project_id = dup.project_id
          AND board_columns.position = dup.position
          AND board_columns.deleted_at IS NOT NULL
        """
    )

    # ── cards: soft-deleted card_number 중복 정리 ──
    op.execute(
        """
        UPDATE cards
        SET card_number = card_number + 100000 + (
            ROW_NUMBER() OVER (PARTITION BY project_id ORDER BY id)
        )::int
        FROM (
            SELECT project_id, card_number
            FROM cards
            GROUP BY project_id, card_number
            HAVING COUNT(*) > 1
        ) dup
        WHERE cards.project_id = dup.project_id
          AND cards.card_number = dup.card_number
          AND cards.deleted_at IS NOT NULL
        """
    )

    # ── labels: soft-deleted name 중복 정리 ──
    op.execute(
        """
        UPDATE labels
        SET name = LEFT(name || '_d' || LEFT(id::text, 8), 100)
        WHERE deleted_at IS NOT NULL
          AND (project_id, name) IN (
              SELECT project_id, name
              FROM labels
              GROUP BY project_id, name
              HAVING COUNT(*) > 1
          )
        """
    )

    # ── labels: partial index 삭제 후 원래 constraint 복원 ──
    op.drop_index(
        "uq_labels_project_name_active", table_name="labels"
    )
    op.create_unique_constraint(
        "uq_labels_project_name", "labels", ["project_id", "name"]
    )

    # ── cards ──
    op.drop_index(
        "uq_cards_project_card_number_active", table_name="cards"
    )
    op.create_unique_constraint(
        "uq_cards_project_card_number", "cards", ["project_id", "card_number"]
    )

    # ── projects ──
    op.drop_index("uq_projects_prefix_active", table_name="projects")
    op.create_unique_constraint(
        "uq_projects_prefix", "projects", ["prefix"]
    )

    # ── users: gw_id ──
    op.drop_index("uq_users_gw_id_active", table_name="users")
    op.create_unique_constraint(
        "users_gw_id_key", "users", ["gw_id"]
    )

    # ── users: employee_id ──
    op.drop_index("uq_users_employee_id_active", table_name="users")
    op.create_unique_constraint(
        "users_employee_id_key", "users", ["employee_id"]
    )

    # ── users: username ──
    op.drop_index("uq_users_username_active", table_name="users")
    op.create_unique_constraint(
        "users_username_key", "users", ["username"]
    )
    op.create_index("ix_users_username", "users", ["username"])

    # ── users: email ──
    op.drop_index("uq_users_email_active", table_name="users")
    op.create_unique_constraint(
        "users_email_key", "users", ["email"]
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ── board_columns ──
    op.drop_index(
        "uq_board_columns_project_position_active", table_name="board_columns"
    )
    op.create_unique_constraint(
        "uq_board_columns_project_position",
        "board_columns",
        ["project_id", "position"],
    )
