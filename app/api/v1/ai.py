from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.deps import CurrentUser
from app.schemas.analysis import ExplainRequest, NLPRequest
from app.services.ai.base import AIProviderError
from app.services.ai.llm import explain_results, provider_health
from app.services.ai.nlp import analyze_text
from app.services.ai.vision import analyze_image
from app.services.storage import save_upload

router = APIRouter(prefix="/ai", tags=["Inteligencia Artificial"])


@router.post("/nlp", summary="Análisis NLP de texto")
async def nlp_analysis(payload: NLPRequest, _: CurrentUser = None):
    try:
        return await analyze_text(payload.text)
    except AIProviderError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.post("/vision", summary="Análisis de Computer Vision de una imagen")
async def vision_analysis(image: UploadFile = File(...), _: CurrentUser = None):
    path = await save_upload(image)
    try:
        return await analyze_image(path)
    except AIProviderError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.post("/explain", summary="Explicación LLM de resultados")
async def llm_explain(payload: ExplainRequest, _: CurrentUser = None):
    try:
        return await explain_results(payload.payload, context=payload.context)
    except AIProviderError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.get("/health", summary="Estado del proveedor de IA configurado")
async def ai_health(_: CurrentUser = None):
    return await provider_health()
