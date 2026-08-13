from typing import Any

from app.services.ai.provider_factory import get_provider


async def analyze_image(
    image_path: str,
    *,
    filename: str | None = None,
    claim: str | None = None,
) -> dict[str, Any]:
    """Análisis de Computer Vision de una imagen usando el proveedor configurado."""
    provider = get_provider()
    return await provider.analyze_image(
        image_path,
        filename=filename,
        claim=claim,
    )


async def provider_health() -> dict[str, Any]:
    """Estado del proveedor de visión configurado."""
    provider = get_provider()
    health = getattr(provider, "health", None)
    if health is None:
        return {"provider": provider.name, "reachable": True}
    return await health()
