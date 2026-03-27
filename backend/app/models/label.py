import uuid

from sqlalchemy import ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, SoftDeleteMixin


class Label(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "labels"
    __table_args__ = (
        Index(
            "uq_labels_project_name_active",
            "project_id",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="labels", lazy="selectin")
    cards = relationship("CardLabel", back_populates="label", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Label(id={self.id}, name={self.name}, color={self.color})>"


class CardLabel(Base):
    __tablename__ = "card_labels"

    card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cards.id"), primary_key=True
    )
    label_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("labels.id"), primary_key=True
    )

    # Relationships
    card = relationship("Card", back_populates="labels", lazy="selectin")
    label = relationship("Label", back_populates="cards", lazy="selectin")

    def __repr__(self) -> str:
        return f"<CardLabel(card_id={self.card_id}, label_id={self.label_id})>"
