"""Servicio de detección de contenido sintético (imágenes).

100% efímero: el archivo se guarda en un archivo temporal, se analiza y se
elimina al terminar. No persiste nada.
"""

import os
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings
from app.services.ai.base import AIProviderError
from app.services.ai.vision import analyze_image

DETECTION_VERDICTS = {
    "autentica": {
        "label": "Auténtica / baja sospecha",
        "description": "No se detectaron indicadores significativos de manipulación o contenido generado por IA.",
        "max_risk": 0.3,
    },
    "sospechosa": {
        "label": "Sospechosa",
        "description": "Existen indicadores moderados de manipulación; se recomienda revisión humana.",
        "max_risk": 0.6,
    },
    "manipulada": {
        "label": "Manipulada / generada con IA",
        "description": "Se detectaron indicadores fuertes de manipulación o contenido sintético.",
        "max_risk": 1.01,
    },
}

SIGNAL_LABELS = {
    "artefactos_de_compresion": "Artefactos de compresión típicos de re-edición digital.",
    "inconsistencias_faciales": "Inconsistencias faciales asociadas a rostros generados o intercambiados.",
    "bordes_inconsistentes": "Bordes irregulares que sugieren recorte o composición.",
    "metadatos_ausentes": "Ausencia de metadatos EXIF, común en imágenes descargadas o editadas.",
}


def classify_image(manipulation_score: float, deepfake_score: float) -> tuple[str, float]:
    """Clasifica la imagen según el riesgo máximo entre manipulación y deepfake."""
    risk = round(max(float(manipulation_score or 0), float(deepfake_score or 0)), 2)
    for verdict, info in DETECTION_VERDICTS.items():
        if risk < info["max_risk"]:
            return verdict, risk
    return "manipulada", risk


def _save_temp_upload(file: UploadFile, max_size_mb: int, ext: str) -> str:
    fd, path = tempfile.mkstemp(suffix=ext, prefix="veriia_detect_")
    os.close(fd)
    dest = Path(path)
    max_bytes = max_size_mb * 1024 * 1024
    size = 0
    try:
        with dest.open("wb") as out:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"El archivo excede {max_size_mb} MB",
                    )
                out.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    return str(dest)


def _build_explanation(
    verdict: str, analysis: dict[str, Any], risk: float
) -> str:
    info = DETECTION_VERDICTS[verdict]
    signals = analysis.get("signals") or []
    parts = [info["description"]]
    if signals:
        labelled = [SIGNAL_LABELS.get(s, s) for s in signals]
        parts.append("Señales detectadas: " + " ".join(labelled))
    else:
        parts.append("No se detectaron señales específicas de manipulación.")
    if analysis.get("ocr_text"):
        parts.append(f"Texto detectado en la imagen: {analysis['ocr_text']}")
    parts.append(f"Riesgo estimado: {risk * 100:.0f}%.")
    return " ".join(parts)


async def detect_image(file: UploadFile, claim: str | None = None) -> dict[str, Any]:
    """Analiza una imagen subida y devuelve el diagnóstico (sin persistir nada)."""
    settings = get_settings()
    original_name = file.filename or "imagen"
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in settings.allowed_image_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Extensión no permitida: {ext or '(sin extensión)'}. "
                f"Permitidas: {', '.join(settings.allowed_image_extensions_list)}"
            ),
        )

    t0 = time.perf_counter()
    path = _save_temp_upload(file, settings.MAX_UPLOAD_SIZE_MB, ext)
    try:
        analysis = await analyze_image(path)
    except AIProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Proveedor de IA no disponible: {exc}",
        )
    finally:
        os.remove(path)

    manipulation = float(analysis.get("manipulation_score") or 0)
    deepfake = float(analysis.get("deepfake_score") or 0)
    verdict, risk = classify_image(manipulation, deepfake)
    info = DETECTION_VERDICTS[verdict]

    return {
        "filename": original_name,
        "verdict": verdict,
        "verdict_label": info["label"],
        "verdict_description": info["description"],
        "risk_score": risk,
        "manipulation_score": manipulation,
        "deepfake_score": deepfake,
        "ocr_text": analysis.get("ocr_text", ""),
        "objects": analysis.get("objects", []),
        "signals": analysis.get("signals", []),
        "explanation": _build_explanation(verdict, analysis, risk),
        "provider": analysis.get("provider", "mock"),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "processing_ms": round((time.perf_counter() - t0) * 1000, 2),
        "metadata": analysis.get("metadata", {}),
        "claim": claim,
    }
