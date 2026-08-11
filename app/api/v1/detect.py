from fastapi import APIRouter, File, Form, UploadFile

from app.schemas.detect import DetectionHealth, DetectionVerdict, ImageDetectionResponse
from app.services.ai.vision import provider_health
from app.services.detection_service import DETECTION_VERDICTS, detect_image

router = APIRouter()


@router.post(
    "/image",
    response_model=ImageDetectionResponse,
    summary="Detectar manipulación o contenido sintético en una imagen",
    description=(
        "Sube una imagen (.jpg, .jpeg, .png, .webp) y devuelve scores de "
        "manipulación y deepfake, OCR, objetos detectados, señales y un veredicto "
        "(auténtica / sospechosa / manipulada) con explicación. "
        "El archivo se procesa en memoria y se elimina al terminar."
    ),
)
async def detect_image_upload(
    file: UploadFile = File(..., description="Imagen a analizar"),
    claim: str | None = Form(
        default=None,
        description="Afirmación asociada a la imagen (opcional, para contexto).",
    ),
) -> ImageDetectionResponse:
    return await detect_image(file, claim)


@router.get(
    "/verdicts",
    response_model=list[DetectionVerdict],
    summary="Listar clasificaciones posibles de una imagen",
)
def list_verdicts() -> list[DetectionVerdict]:
    return [
        DetectionVerdict(code=code, label=info["label"], description=info["description"])
        for code, info in DETECTION_VERDICTS.items()
    ]


@router.get(
    "/health",
    response_model=DetectionHealth,
    summary="Estado del proveedor de visión",
)
async def health() -> DetectionHealth:
    data = await provider_health()
    return DetectionHealth(
        provider=data.get("provider", "mock"),
        reachable=data.get("reachable", True),
        error=data.get("error"),
    )
