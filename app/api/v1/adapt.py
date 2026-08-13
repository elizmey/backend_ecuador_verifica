from fastapi import APIRouter, HTTPException, status

from app.schemas.adapt import AdaptRequest, AdaptResponse
from app.services.adaptation_service import adapt

router = APIRouter()


@router.post(
    "",
    response_model=AdaptResponse,
    summary="Adaptar contenidos para medios locales",
    description=(
        "Convierte un texto en formatos para radios, WhatsApp, lenguas indígenas "
        "(kichwa/shua), lectura fácil, notas editoriales, comparativas de propuestas "
        "y boletines. Usa **Gemini** si `GOOGLE_AI_API_KEY` está configurada; si no, "
        "devuelve una versión local con plantillas."
    ),
)
async def adapt_endpoint(payload: AdaptRequest) -> AdaptResponse:
    try:
        return await adapt(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
