import asyncio
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.analysis import AnalysisResult, AnalysisStage
from app.models.request import RequestStatus, Verdict, VerificationRequest
from app.services.ai.base import AIProviderError
from app.services.ai.provider_factory import get_provider

settings = get_settings()

VALID_VERDICTS = {v.value for v in Verdict}


def _save_analysis(
    db: Session,
    request_id: int,
    stage: AnalysisStage,
    provider: str,
    success: bool,
    payload: dict[str, Any] | None = None,
    latency_ms: float | None = None,
    error: str | None = None,
) -> AnalysisResult:
    result = AnalysisResult(
        request_id=request_id,
        stage=stage,
        provider=provider,
        success=success,
        payload=payload or {},
        latency_ms=latency_ms,
        error=error,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


async def _async_pipeline(db: Session, request: VerificationRequest) -> None:
    from app.services.source_verification import verify_sources_for_text

    provider = get_provider()
    nlp_payload: dict[str, Any] | None = None
    vision_payloads: list[dict[str, Any]] = []
    matched_sources: list[dict[str, Any]] = []

    if request.claim.strip():
        t0 = time.perf_counter()
        nlp_payload = await provider.analyze_text(request.claim)
        nlp_analysis = _save_analysis(
            db,
            request.id,
            AnalysisStage.nlp,
            provider.name,
            True,
            nlp_payload,
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
        )
        refs = verify_sources_for_text(db, nlp_analysis.id, request.claim)
        matched_sources = [
            {
                "name": ref.source.name,
                "domain": ref.source.domain,
                "category": ref.source.category,
                "match_type": ref.match_type,
                "similarity": ref.similarity,
            }
            for ref in refs
        ]

    for image in request.images or []:
        t0 = time.perf_counter()
        vision_payload = await provider.analyze_image(image)
        vision_payloads.append(vision_payload)
        _save_analysis(
            db,
            request.id,
            AnalysisStage.vision,
            provider.name,
            True,
            vision_payload,
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
        )

    t0 = time.perf_counter()
    llm_payload = await provider.explain(
        {"nlp": nlp_payload, "vision": vision_payloads, "sources": matched_sources},
        context=request.claim,
    )
    _save_analysis(
        db,
        request.id,
        AnalysisStage.llm,
        provider.name,
        True,
        llm_payload,
        latency_ms=round((time.perf_counter() - t0) * 1000, 2),
    )

    recommended = llm_payload.get("recommended_verdict", "unverified")
    request.verdict = Verdict(recommended) if recommended in VALID_VERDICTS else Verdict.unverified
    request.confidence = llm_payload.get("confidence")
    request.summary = llm_payload.get("summary")


def run_request_pipeline(db: Session, request_id: int) -> None:
    """Procesa una solicitud: NLP → Vision → LLM. Síncrona, apta para worker/inline."""
    if not settings.AI_ENABLED:
        raise AIProviderError("La capa de IA está deshabilitada (AI_ENABLED=false)")

    request = db.get(VerificationRequest, request_id)
    if request is None:
        raise AIProviderError(f"Solicitud {request_id} no encontrada")

    request.status = RequestStatus.processing
    request.error_message = None
    db.commit()

    try:
        asyncio.run(_async_pipeline(db, request))
        request.status = RequestStatus.completed
    except Exception as e:  # noqa: BLE001 - cualquier fallo del proveedor
        db.rollback()
        request = db.get(VerificationRequest, request_id)
        request.status = RequestStatus.failed
        request.error_message = str(e)[:2000]

    request.processed_at = datetime.now(timezone.utc)
    db.commit()
