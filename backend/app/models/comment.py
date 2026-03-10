import uuid

from sqlalchemy import ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, SoftDeleteMixin


class CardComment(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "card_comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cards.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    card = relationship("Card", back_populates="comments", lazy="selectin")
    user = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<CardComment(id={self.id}, card_id={self.card_id})>"
