from abc import ABC, abstractmethod
from typing import Any


class AIProviderError(Exception):
    """Error genérico de comunicación con un proveedor de IA."""


class BaseAIProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def analyze_text(self, text: str) -> dict[str, Any]:
        """Análisis NLP de un texto (claims, sentimiento, temas, entidades)."""

    @abstractmethod
    async def analyze_image(self, image_path: str) -> dict[str, Any]:
        """Análisis de Computer Vision de una imagen (manipulación, OCR, objetos)."""

    @abstractmethod
    async def explain(self, payload: dict[str, Any], context: str | None = None) -> dict[str, Any]:
        """Genera una explicación LLM legible a partir de un análisis previo."""
