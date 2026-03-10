import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, SoftDeleteMixin


class ProjectStatus(enum.Enum):
    active = "active"
    completed = "completed"
    archived = "archived"


class ProjectRole(enum.Enum):
    """프로젝트 역할: manager(관리자) > member(멤버) > viewer(뷰어)"""
    manager = "manager"
    member = "member"
    viewer = "viewer"


class Project(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("prefix", name="uq_projects_prefix"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status", create_constraint=True, native_enum=True),
        nullable=False,
        server_default="active",
    )
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Relationships
    team = relationship("Team", back_populates="projects", lazy="selectin")
    creator = relationship("User", lazy="selectin")
    board_columns = relationship("BoardColumn", back_populates="project", lazy="selectin")
    cards = relationship("Card", back_populates="project", lazy="selectin")
    labels = relationship("Label", back_populates="project", lazy="selectin")
    outcomes = relationship("ProjectOutcome", back_populates="project", lazy="selectin")
    members = relationship("ProjectMember", back_populates="project", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, prefix={self.prefix})>"


class ProjectMember(Base, TimestampMixin):
    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_members_project_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    role: Mapped[ProjectRole] = mapped_column(
        Enum(ProjectRole, name="project_role", create_constraint=True, native_enum=True),
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    project = relationship("Project", back_populates="members", lazy="selectin")
    user = relationship("User", back_populates="project_memberships", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ProjectMember(project_id={self.project_id}, user_id={self.user_id}, role={self.role})>"
