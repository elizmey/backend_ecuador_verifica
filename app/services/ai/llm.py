from typing import Any

from app.services.ai.provider_factory import get_provider


async def explain_results(
    payload: dict[str, Any], context: str | None = None
) -> dict[str, Any]:
    """Genera una explicación LLM legible a partir de un análisis previo."""
    provider = get_provider()
    return await provider.explain(payload, context)


async def provider_health() -> dict[str, Any]:
    provider = get_provider()
    health = getattr(provider, "health", None)
    if health is None:
        return {"provider": provider.name, "reachable": True}
    return await health()
