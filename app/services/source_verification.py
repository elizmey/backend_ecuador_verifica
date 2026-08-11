import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.source import Source, SourceReference


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9áéíóúñü]+", text.lower()))


@dataclass
class SourceMatch:
    source: Source
    match_type: str
    similarity: float


def match_sources_for_text(sources: list[Source], text: str) -> list[SourceMatch]:
    """Devuelve qué fuentes confiables coinciden con el texto dado (sin persistir)."""
    if not text or not text.strip():
        return []

    text_lower = text.lower()
    text_tokens = _tokenize(text)

    matches: list[SourceMatch] = []
    for source in sources:
        match_type: str | None = None
        similarity = 0.0

        if source.domain and source.domain.lower() in text_lower:
            match_type, similarity = "domain", 1.0
        elif source.url and source.url.lower() in text_lower:
            match_type, similarity = "url", 1.0
        else:
            name_tokens = _tokenize(source.name)
            if name_tokens:
                overlap = len(name_tokens & text_tokens) / len(name_tokens)
                if overlap >= 0.5:
                    match_type, similarity = "keyword", round(overlap, 2)

        if match_type:
            matches.append(
                SourceMatch(source=source, match_type=match_type, similarity=similarity)
            )
    return matches


def verify_sources_for_text(
    db: Session, analysis_result_id: int, text: str
) -> list[SourceReference]:
    """Cruza el texto contra las fuentes confiables y persiste las referencias."""
    sources = list(db.scalars(select(Source).where(Source.is_verified.is_(True))))
    matches = match_sources_for_text(sources, text)

    refs: list[SourceReference] = []
    for match in matches:
        refs.append(
            SourceReference(
                analysis_result_id=analysis_result_id,
                source_id=match.source.id,
                match_type=match.match_type,
                similarity=match.similarity,
                snippet=text[:500],
            )
        )

    if refs:
        db.add_all(refs)
        db.commit()
    return refs
