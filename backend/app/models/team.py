import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, SoftDeleteMixin


class TeamRole(enum.Enum):
    """팀 역할: owner(소유자) > manager(관리자) > member(멤버) > viewer(뷰어)"""
    owner = "owner"
    manager = "manager"
    member = "member"
    viewer = "viewer"


class Team(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Relationships
    creator = relationship("User", back_populates="created_teams", lazy="selectin")
    members = relationship("TeamMember", back_populates="team", lazy="selectin")
    projects = relationship("Project", back_populates="team", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name={self.name})>"


class TeamMember(Base, TimestampMixin):
    __tablename__ = "team_members"
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_members_team_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    role: Mapped[TeamRole] = mapped_column(
        Enum(TeamRole, name="team_role", create_constraint=True, native_enum=True),
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    team = relationship("Team", back_populates="members", lazy="selectin")
    user = relationship("User", back_populates="team_memberships", lazy="selectin")

    def __repr__(self) -> str:
        return f"<TeamMember(team_id={self.team_id}, user_id={self.user_id}, role={self.role})>"
