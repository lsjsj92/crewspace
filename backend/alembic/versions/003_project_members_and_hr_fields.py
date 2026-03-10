# alembic/versions/003_project_members_and_hr_fields.py
"""add project_members table and HR fields

Revision ID: 003_project_members
Revises: 002_rename_admin
Create Date: 2026-03-08
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "003_project_members"
down_revision = "002_rename_admin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add HR fields to users table
    op.add_column("users", sa.Column("employee_id", sa.String(50), unique=True, nullable=True))
    op.add_column("users", sa.Column("organization", sa.String(200), nullable=True))
    op.add_column("users", sa.Column("gw_id", sa.String(100), unique=True, nullable=True))

    # 2. Create project_role enum
    project_role = postgresql.ENUM("manager", "member", "viewer", name="project_role", create_type=False)
    project_role.create(op.get_bind(), checkfirst=True)

    # 3. Create project_members table
    op.create_table(
        "project_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", postgresql.ENUM("manager", "member", "viewer", name="project_role", create_type=False), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_members_project_user"),
    )

    # 4. Make projects.team_id nullable
    op.alter_column("projects", "team_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)

    # 5. Drop old unique constraint and add global prefix unique
    op.drop_constraint("uq_projects_team_prefix", "projects", type_="unique")
    op.create_unique_constraint("uq_projects_prefix", "projects", ["prefix"])

    # 6. Migrate existing data: team_members -> project_members
    # For each project, find the team_members of that project's team and add them as project_members
    op.execute("""
        INSERT INTO project_members (project_id, user_id, role, joined_at)
        SELECT p.id, tm.user_id,
            CASE WHEN tm.role = 'owner' THEN 'manager'::project_role
                 WHEN tm.role = 'manager' THEN 'manager'::project_role
                 WHEN tm.role = 'member' THEN 'member'::project_role
                 WHEN tm.role = 'viewer' THEN 'viewer'::project_role
            END,
            tm.joined_at
        FROM projects p
        JOIN team_members tm ON tm.team_id = p.team_id
        WHERE p.deleted_at IS NULL
        ON CONFLICT (project_id, user_id) DO NOTHING
    """)

    # 7. Create indexes
    op.create_index("ix_project_members_project_id", "project_members", ["project_id"])
    op.create_index("ix_project_members_user_id", "project_members", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_project_members_user_id", table_name="project_members")
    op.drop_index("ix_project_members_project_id", table_name="project_members")
    op.drop_constraint("uq_projects_prefix", "projects", type_="unique")
    op.create_unique_constraint("uq_projects_team_prefix", "projects", ["team_id", "prefix"])
    op.alter_column("projects", "team_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
    op.drop_table("project_members")
    sa.Enum(name="project_role").drop(op.get_bind(), checkfirst=True)
    op.drop_column("users", "gw_id")
    op.drop_column("users", "organization")
    op.drop_column("users", "employee_id")
