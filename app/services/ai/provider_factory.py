from app.core.config import get_settings
from app.services.ai.providers.google import GoogleAIProvider
from app.services.ai.providers.mock import MockAIProvider
from app.services.ai.providers.ollama import OllamaAIProvider
from app.services.ai.providers.openai import OpenAICompatibleProvider

settings = get_settings()


def get_provider(name: str | None = None):
    provider_name = (name or settings.AI_PROVIDER).strip().lower()
    if provider_name == "ollama":
        return OllamaAIProvider()
    if provider_name == "openai":
        if not settings.OPENAI_API_KEY:
            from app.services.ai.base import AIProviderError

            raise AIProviderError(
                "AI_PROVIDER=openai requiere OPENAI_API_KEY en el entorno"
            )
        return OpenAICompatibleProvider()
    if provider_name == "google":
        if not settings.GOOGLE_AI_API_KEY:
            from app.services.ai.base import AIProviderError

            raise AIProviderError(
                "AI_PROVIDER=google requiere GOOGLE_AI_API_KEY en el entorno"
            )
        return GoogleAIProvider()
    return MockAIProvider()
