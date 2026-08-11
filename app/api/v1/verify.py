from fastapi import APIRouter, HTTPException, status

from app.data.knowledge import KNOWN_CLAIMS, TRUSTED_SOURCES, VERDICTS
from app.schemas.verify import (
    KnownClaimInfo,
    SourceInfo,
    VerifyRequest,
    VerifyResponse,
    VerdictInfo,
)
from app.services.ai.base import AIProviderError
from app.services.verifier import verify_claim

router = APIRouter()


@router.post(
    "/check",
    response_model=VerifyResponse,
    summary="Verificar una afirmación en tiempo real",
    description=(
        "Analiza el texto con NLP, lo cruza contra la base de conocimiento y las "
        "fuentes confiables, y devuelve un veredicto (verdadero / falso / engañoso / "
        "sin evidencia) con explicación. No guarda nada."
    ),
)
async def check(payload: VerifyRequest) -> VerifyResponse:
    try:
        return await verify_claim(payload.claim)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except AIProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Proveedor de IA no disponible: {exc}",
        )


@router.get(
    "/verdicts",
    response_model=list[VerdictInfo],
    summary="Listar veredictos posibles",
)
def list_verdicts() -> list[VerdictInfo]:
    return [
        VerdictInfo(code=code, label=info["label"], description=info["description"])
        for code, info in VERDICTS.items()
    ]


@router.get(
    "/sources",
    response_model=list[SourceInfo],
    summary="Listar fuentes confiables de referencia",
)
def list_sources() -> list[SourceInfo]:
    return [SourceInfo(**source) for source in TRUSTED_SOURCES]


@router.get(
    "/known-claims",
    response_model=list[KnownClaimInfo],
    summary="Listar desinformaciones documentadas en memoria",
)
def list_known_claims() -> list[KnownClaimInfo]:
    return [
        KnownClaimInfo(
            id=f["id"],
            category=f["category"],
            verdict=f["verdict"],
            keywords=f["keywords"],
            explanation=f["explanation"],
            sources=f["sources"],
        )
        for f in KNOWN_CLAIMS
    ]
