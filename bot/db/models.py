"""Database models for the prediction bot."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class PredictionStatus(str, enum.Enum):
    """Prediction status enum."""

    SCHEDULED = "scheduled"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class MediaType(str, enum.Enum):
    """Supported media types."""

    PHOTO = "photo"
    GIF = "gif"
    VIDEO = "video"
    ANIMATION = "animation"


class User(Base):
    """User model for storing Telegram users."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    predictions_created: Mapped[list["Prediction"]] = relationship(
        "Prediction", back_populates="created_by_admin"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_user_id={self.telegram_user_id})>"


class Prediction(Base):
    """Prediction model for storing monthly predictions."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[PredictionStatus] = mapped_column(
        Enum(PredictionStatus), default=PredictionStatus.SCHEDULED, nullable=False
    )

    # Media
    media_type: Mapped[MediaType] = mapped_column(Enum(MediaType), nullable=False)
    media_file_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Content
    post_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Buttons - initial
    button_1_initial: Mapped[str] = mapped_column(String(64), nullable=False)
    button_2_initial: Mapped[str] = mapped_column(String(64), nullable=False)
    button_3_initial: Mapped[str] = mapped_column(String(64), nullable=False)

    # Buttons - final (after selection)
    button_1_final: Mapped[str] = mapped_column(String(64), nullable=False)
    button_2_final: Mapped[str] = mapped_column(String(64), nullable=False)
    button_3_final: Mapped[str] = mapped_column(String(64), nullable=False)

    # Scheduling
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Broadcast tracking
    broadcast_started: Mapped[bool] = mapped_column(Boolean, default=False)
    broadcast_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Admin reference
    created_by_admin_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    created_by_admin: Mapped[Optional["User"]] = relationship("User", back_populates="predictions_created")
    choices: Mapped[list["UserPredictionChoice"]] = relationship(
        "UserPredictionChoice", back_populates="prediction"
    )

    __table_args__ = (
        # Ensure only one active prediction at a time
        Index(
            "ix_predictions_unique_active",
            "status",
            unique=True,
            postgresql_where=(status == PredictionStatus.ACTIVE),
        ),
        # Ensure only one scheduled prediction at a time
        Index(
            "ix_predictions_unique_scheduled",
            "status",
            unique=True,
            postgresql_where=(status == PredictionStatus.SCHEDULED),
        ),
    )

    def __repr__(self) -> str:
        return f"<Prediction(id={self.id}, status={self.status})>"

    def get_initial_buttons(self) -> list[str]:
        """Return list of initial button texts."""
        return [self.button_1_initial, self.button_2_initial, self.button_3_initial]

    def get_final_button(self, button_number: int) -> str:
        """Return final button text for given button number."""
        mapping = {
            1: self.button_1_final,
            2: self.button_2_final,
            3: self.button_3_final,
        }
        return mapping.get(button_number, "")


class UserPredictionChoice(Base):
    """Model for storing user choices on predictions."""

    __tablename__ = "user_prediction_choices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    prediction_id: Mapped[int] = mapped_column(Integer, ForeignKey("predictions.id"), nullable=False)
    selected_button: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, or 3
    selected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # For enforcing one choice per user per month
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)

    # Track if this is a test choice (admin test, not counted in stats)
    is_test: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    prediction: Mapped["Prediction"] = relationship("Prediction", back_populates="choices")

    __table_args__ = (
        # Ensure one choice per user per month (excluding test choices)
        UniqueConstraint(
            "telegram_user_id",
            "year",
            "month",
            name="uq_user_prediction_choice_per_month",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<UserPredictionChoice(id={self.id}, user={self.telegram_user_id}, "
            f"button={self.selected_button})>"
        )
