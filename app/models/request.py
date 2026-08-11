import enum
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class RequestMediaType(str, enum.Enum):
    text = "text"
    image = "image"
    mixed = "mixed"


class RequestStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Verdict(str, enum.Enum):
    true = "true"
    false = "false"
    mixed = "mixed"
    unverified = "unverified"


class VerificationRequest(Base, TimestampMixin):
    __tablename__ = "verification_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    article_id: Mapped[int | None] = mapped_column(
        ForeignKey("news_articles.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    media_type: Mapped[RequestMediaType] = mapped_column(
        Enum(
            RequestMediaType,
            name="request_media_type",
            values_callable=lambda x: [e.value for e in x],
        ),
        default=RequestMediaType.text,
        nullable=False,
    )
    images: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)

    status: Mapped[RequestStatus] = mapped_column(
        Enum(
            RequestStatus,
            name="request_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        default=RequestStatus.pending,
        nullable=False,
    )
    verdict: Mapped[Verdict | None] = mapped_column(
        Enum(
            Verdict,
            name="verdict",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=True,
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    owner: Mapped["User"] = relationship(back_populates="requests")  # noqa: F821
    article: Mapped["NewsArticle | None"] = relationship(  # noqa: F821
        back_populates="verifications"
    )
    analyses: Mapped[list["AnalysisResult"]] = relationship(  # noqa: F821
        back_populates="request", cascade="all, delete-orphan"
    )

    @property
    def veracity_score(self) -> float | None:
        """Porcentaje de confiabilidad (0-100) derivado de la confianza del análisis."""
        if self.confidence is None:
            return None
        return round(self.confidence * 100, 1)
