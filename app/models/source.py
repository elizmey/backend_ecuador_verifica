from sqlalchemy import Boolean, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Source(Base, TimestampMixin):
    """Fuente confiable registrada para la verificación de contenidos."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reliability_score: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    references: Mapped[list["SourceReference"]] = relationship(  # noqa: F821
        back_populates="source", cascade="all, delete-orphan"
    )


class SourceReference(Base, TimestampMixin):
    """Referencia de una fuente encontrada durante un análisis (verificación de fuentes)."""

    __tablename__ = "source_references"
    __table_args__ = (
        UniqueConstraint(
            "analysis_result_id", "source_id", name="uq_reference_analysis_source"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_result_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_results.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), index=True, nullable=False
    )
    match_type: Mapped[str] = mapped_column(String(50), nullable=False)  # domain|url|keyword
    similarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)

    analysis_result: Mapped["AnalysisResult"] = relationship(  # noqa: F821
        back_populates="source_references"
    )
    source: Mapped[Source] = relationship(back_populates="references")
