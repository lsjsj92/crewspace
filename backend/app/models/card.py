import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, SoftDeleteMixin


class CardType(enum.Enum):
    epic = "epic"
    story = "story"
    task = "task"
    sub_task = "sub_task"


class CardPriority(enum.Enum):
    lowest = "lowest"
    low = "low"
    medium = "medium"
    high = "high"
    highest = "highest"


class Card(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "cards"
    __table_args__ = (
        UniqueConstraint("project_id", "card_number", name="uq_cards_project_card_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    column_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("board_columns.id"), nullable=False
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cards.id"), nullable=True, default=None
    )
    card_type: Mapped[CardType] = mapped_column(
        Enum(CardType, name="card_type", create_constraint=True, native_enum=True),
        nullable=False,
    )
    card_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[CardPriority] = mapped_column(
        Enum(CardPriority, name="card_priority", create_constraint=True, native_enum=True),
        nullable=False,
        server_default="medium",
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Relationships
    project = relationship("Project", back_populates="cards", lazy="selectin")
    column = relationship("BoardColumn", back_populates="cards", lazy="selectin")
    parent = relationship("Card", remote_side="Card.id", back_populates="children", lazy="selectin")
    children = relationship("Card", back_populates="parent", lazy="selectin")
    creator = relationship("User", lazy="selectin")
    assignees = relationship("CardAssignee", back_populates="card", lazy="selectin")
    labels = relationship("CardLabel", back_populates="card", lazy="selectin")
    comments = relationship("CardComment", back_populates="card", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Card(id={self.id}, card_number={self.card_number}, title={self.title})>"


class CardAssignee(Base):
    __tablename__ = "card_assignees"
    __table_args__ = (
        UniqueConstraint("card_id", "user_id", name="uq_card_assignees_card_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cards.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    card = relationship("Card", back_populates="assignees", lazy="selectin")
    user = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<CardAssignee(card_id={self.card_id}, user_id={self.user_id})>"
