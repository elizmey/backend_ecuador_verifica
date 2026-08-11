import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings

settings = get_settings()


def _safe_ext(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


async def save_upload(file: UploadFile) -> str:
    ext = _safe_ext(file.filename or "")
    if ext not in settings.allowed_image_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Extensión no permitida: {ext or '(sin extensión)'}. "
                f"Permitidas: {', '.join(settings.allowed_image_extensions_list)}"
            ),
        )

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    dest = upload_dir / filename

    size = 0
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    with open(dest, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > max_bytes:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Archivo excede {settings.MAX_UPLOAD_SIZE_MB} MB",
                )
            out.write(chunk)

    return str(dest)
