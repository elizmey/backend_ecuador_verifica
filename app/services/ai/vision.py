from typing import Any

from app.services.ai.provider_factory import get_provider


async def analyze_image(image_path: str) -> dict[str, Any]:
    """Análisis de Computer Vision de una imagen usando el proveedor configurado."""
    provider = get_provider()
    return await provider.analyze_image(image_path)
