"""Generación de texto con Google Gemini (shared helper)."""

from __future__ import annotations

import asyncio

import httpx

from app.core.config import get_settings
from app.services.ai.base import AIProviderError

_RETRY_STATUS = (429, 500, 502, 503, 504)


async def post_with_retry(
    url: str,
    *,
    params: dict[str, str],
    json: dict,
    timeout: int,
    retries: int = 3,
) -> httpx.Response:
    """POST a Gemini con reintentos ante 429/timeouts (backoff exponencial)."""
    delay = 1.0
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(retries):
            try:
                resp = await client.post(url, params=params, json=json)
            except httpx.HTTPError as exc:
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                raise AIProviderError(f"Error al llamar a Gemini: {exc}") from exc

            if resp.status_code in _RETRY_STATUS and attempt < retries - 1:
                wait = delay
                retry_after = resp.headers.get("retry-after")
                if retry_after and retry_after.isdigit():
                    wait = float(retry_after)
                await asyncio.sleep(min(wait, 10))
                delay *= 2
                continue

            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise AIProviderError(f"Error al llamar a Gemini: {exc}") from exc
            return resp

    raise AIProviderError("Error al llamar a Gemini: reintentos agotados")


async def generate_text(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """Llama a Gemini y devuelve el texto generado.

    Lanza AIProviderError si no hay clave configurada o la API falla.
    """
    settings = get_settings()
    key = settings.GOOGLE_AI_API_KEY.strip()
    if not key:
        raise AIProviderError("GOOGLE_AI_API_KEY no configurada")

    url = (
        f"{settings.GOOGLE_AI_BASE_URL.rstrip('/')}"
        f"/v1beta/models/{settings.GOOGLE_AI_TEXT_MODEL}:generateContent"
    )
    body = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }

    try:
        resp = await post_with_retry(
            url,
            params={"key": key},
            json=body,
            timeout=settings.AI_TIMEOUT_SECONDS,
        )
        data = resp.json()
    except httpx.HTTPError as exc:
        raise AIProviderError(f"Error al llamar a Gemini: {exc}") from exc

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise AIProviderError(
            f"Gemini no devolvió texto: {data.get('error') or exc}"
        ) from exc
