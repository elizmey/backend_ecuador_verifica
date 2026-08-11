"""Servicio de verificación de desinformación en tiempo real.

100% en memoria: no persiste nada, no usa base de datos. Cada llamada
analiza la afirmación, la cruza con la base de conocimiento y devuelve
un veredicto con explicación.
"""

import re
import time
import unicodedata
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from app.data.knowledge import KNOWN_CLAIMS, TRUSTED_SOURCES, VERDICTS
from app.services.ai.nlp import analyze_text

NEGATION_PATTERNS = (
    " no caus",
    " no transmite",
    " no provoca",
    " no produce",
    " no existe",
    " no es verdad",
    " no es cierto",
    " es mentira",
    " es falso",
    " falso que",
    " desmient",
    " no contrae",
    " no cura",
)


def _norm(text: str) -> str:
    """Minúsculas y sin tildes, para comparar de forma robusta."""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text))


_STOPWORDS = {"de", "la", "el", "del", "y", "a", "en", "los", "las", "un", "una", "es"}


def _match_known_claim(claim: str) -> dict[str, Any] | None:
    text = _norm(claim)
    best: dict[str, Any] | None = None
    best_score = 0.0
    for fact in KNOWN_CLAIMS:
        present = sum(1 for kw in fact["keywords"] if kw in text)
        ratio = present / len(fact["keywords"])
        if ratio >= 0.6 and ratio > best_score:
            best = fact
            best_score = ratio
    return best


def _has_negation(claim: str) -> bool:
    text = _norm(claim)
    return any(pattern in text for pattern in NEGATION_PATTERNS)


def _match_sources(claim: str) -> list[dict[str, Any]]:
    text = _norm(claim)
    tokens = _tokens(text)
    matches: list[dict[str, Any]] = []

    for source in TRUSTED_SOURCES:
        name_norm = _norm(source["name"])
        match_type: str | None = None
        similarity = 0.0

        if source["domain"] in text:
            match_type, similarity = "domain", 1.0
        elif name_norm in text:
            match_type, similarity = "name", 1.0
        else:
            name_tokens = {t for t in _tokens(name_norm) if t not in _STOPWORDS}
            if name_tokens:
                overlap = len(name_tokens & tokens) / len(name_tokens)
                if overlap >= 0.5:
                    match_type, similarity = "keyword", round(overlap, 2)

        if match_type:
            matches.append(
                {
                    "name": source["name"],
                    "domain": source["domain"],
                    "url": source["url"],
                    "category": source["category"],
                    "match_type": match_type,
                    "similarity": similarity,
                }
            )

    return sorted(matches, key=lambda m: m["similarity"], reverse=True)


def _build_explanation(
    claim: str,
    fact: dict[str, Any] | None,
    negated: bool,
    nlp: dict[str, Any],
    source_matches: list[dict[str, Any]],
) -> str:
    if fact is not None:
        if negated:
            return (
                f"Correcto: la afirmación contradice una desinformación ampliamente "
                f"documentada. {fact['explanation']}"
            )
        return fact["explanation"]

    parts: list[str] = []
    signals = nlp.get("suspicious_signals") or []
    if signals:
        parts.append(
            "El análisis automático detectó señales de lenguaje manipulativo o "
            "emocional, por lo que conviene leer esta información con cautela."
        )
    else:
        parts.append(
            "No se encontró coincidencia con los casos documentados en la base de "
            "conocimiento del verificador."
        )
    if source_matches:
        names = " / ".join(m["name"] for m in source_matches[:3])
        parts.append(f"El texto coincide con fuentes de referencia: {names}.")
    parts.append("Se recomienda contrastar la información con fuentes oficiales.")
    return " ".join(parts)


def _resolve_verdict(
    claim: str, fact: dict[str, Any] | None, negated: bool, nlp: dict[str, Any]
) -> tuple[str, float]:
    if fact is not None:
        verdict: str = fact["verdict"]
        confidence: float = fact["confidence"]
        if negated:
            if verdict == "falso":
                verdict, confidence = "verdadero", min(0.99, confidence + 0.02)
            elif verdict == "verdadero":
                verdict, confidence = "falso", min(0.99, confidence + 0.02)
        return verdict, confidence

    signals = nlp.get("suspicious_signals") or []
    if signals:
        return "enganyoso", round(0.55 + 0.1 * min(len(signals), 3), 2)
    return "sin_evidencia", 0.5


async def verify_claim(claim: str) -> dict[str, Any]:
    """Analiza una afirmación y devuelve el veredicto completo (sin persistir)."""
    if not claim or not claim.strip():
        raise ValueError("La afirmación no puede estar vacía")

    claim = claim.strip()
    t0 = time.perf_counter()

    nlp = await analyze_text(claim)

    fact = _match_known_claim(claim)
    negated = _has_negation(claim) if fact else False
    verdict, confidence = _resolve_verdict(claim, fact, negated, nlp)
    source_matches = _match_sources(claim)
    explanation = _build_explanation(claim, fact, negated, nlp, source_matches)

    evidence_sources = []
    if fact:
        for name in fact["sources"]:
            norm_name = _norm(name)
            match = next(
                (
                    s
                    for s in TRUSTED_SOURCES
                    if norm_name == _norm(s["name"])
                    or norm_name in _norm(s["name"])
                    or _norm(s["name"]) in norm_name
                ),
                None,
            )
            if match:
                url, category = match["url"], match["category"]
            else:
                url = f"https://www.google.com/search?q={quote(name)}"
                category = "referencia"
            evidence_sources.append({"name": name, "url": url, "category": category})

    verdict_info = VERDICTS.get(verdict, VERDICTS["sin_evidencia"])

    return {
        "claim": claim,
        "verdict": verdict,
        "verdict_label": verdict_info["label"],
        "verdict_description": verdict_info["description"],
        "confidence": confidence,
        "explanation": explanation,
        "provider": nlp.get("provider", "mock"),
        "language": nlp.get("language", "es"),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "processing_ms": round((time.perf_counter() - t0) * 1000, 2),
        "nlp": nlp,
        "source_matches": source_matches,
        "evidence": {
            "fact_used": fact["id"] if fact else None,
            "fact_category": fact["category"] if fact else None,
            "negation_detected": negated,
            "recommended_sources": evidence_sources,
        },
    }
