import uuid

from sqlalchemy import Boolean, ForeignKey, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, SoftDeleteMixin


class BoardColumn(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "board_columns"
    __table_args__ = (
        UniqueConstraint("project_id", "position", name="uq_board_columns_project_position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    is_end: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    wip_limit: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, default=None)

    # Relationships
    project = relationship("Project", back_populates="board_columns", lazy="selectin")
    cards = relationship("Card", back_populates="column", lazy="selectin")

    def __repr__(self) -> str:
        return f"<BoardColumn(id={self.id}, name={self.name}, position={self.position})>"
