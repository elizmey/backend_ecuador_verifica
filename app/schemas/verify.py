from typing import Any

from pydantic import BaseModel, Field


class VerifyRequest(BaseModel):
    claim: str = Field(
        ...,
        min_length=3,
        max_length=5000,
        description="Afirmación o texto a verificar en tiempo real.",
        examples=["Las vacunas causan autismo"],
    )
    language: str | None = Field(
        default=None,
        description="Código de idioma esperado (p. ej. 'es'). Si se omite se detecta automáticamente.",
    )


class SourceMatch(BaseModel):
    name: str
    domain: str
    url: str
    category: str
    match_type: str
    similarity: float


class RecommendedSource(BaseModel):
    name: str
    url: str
    category: str


class Evidence(BaseModel):
    fact_used: str | None = None
    fact_category: str | None = None
    negation_detected: bool = False
    recommended_sources: list[RecommendedSource] = Field(default_factory=list)


class VerifyResponse(BaseModel):
    claim: str
    verdict: str
    verdict_label: str
    verdict_description: str
    confidence: float
    explanation: str
    provider: str
    language: str
    checked_at: str
    processing_ms: float
    nlp: dict[str, Any]
    source_matches: list[SourceMatch] = Field(default_factory=list)
    evidence: Evidence


class VerdictInfo(BaseModel):
    code: str
    label: str
    description: str


class SourceInfo(BaseModel):
    name: str
    domain: str
    url: str
    category: str


class KnownClaimInfo(BaseModel):
    id: str
    category: str
    verdict: str
    keywords: list[str]
    explanation: str
    sources: list[str]
