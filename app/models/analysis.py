import enum
from typing import Any

from sqlalchemy import Boolean, Enum, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class AnalysisStage(str, enum.Enum):
    nlp = "nlp"
    vision = "vision"
    llm = "llm"


class AnalysisResult(Base, TimestampMixin):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("verification_requests.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    stage: Mapped[AnalysisStage] = mapped_column(
        Enum(
            AnalysisStage,
            name="analysis_stage",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Float, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    request: Mapped["VerificationRequest"] = relationship(back_populates="analyses")  # noqa: F821
    source_references: Mapped[list["SourceReference"]] = relationship(  # noqa: F821
        back_populates="analysis_result", cascade="all, delete-orphan"
    )
