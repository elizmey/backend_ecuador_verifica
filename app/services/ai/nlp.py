from typing import Any

from app.services.ai.base import AIProviderError
from app.services.ai.provider_factory import get_provider


async def analyze_text(text: str) -> dict[str, Any]:
    """Análisis NLP de un texto usando el proveedor configurado."""
    if not text.strip():
        raise AIProviderError("El texto está vacío")
    provider = get_provider()
    return await provider.analyze_text(text)
