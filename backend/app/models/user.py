import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SoftDeleteMixin, TimestampMixin


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    employee_id: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    organization: Mapped[str | None] = mapped_column(String(200), nullable=True)
    gw_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)

    # Relationships
    team_memberships = relationship("TeamMember", back_populates="user", lazy="selectin")
    project_memberships = relationship("ProjectMember", back_populates="user", lazy="selectin")
    created_teams = relationship("Team", back_populates="creator", lazy="selectin")
    refresh_tokens = relationship("RefreshToken", back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"
