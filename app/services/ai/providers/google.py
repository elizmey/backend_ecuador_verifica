import base64
import json
from typing import Any

import httpx

from app.core.config import get_settings
from app.services.ai.base import AIProviderError, BaseAIProvider

settings = get_settings()


class GoogleAIProvider(BaseAIProvider):
    """Proveedor Google AI (Gemini) vía REST API.

    Listo para conexión: define GOOGLE_AI_API_KEY y usa AI_PROVIDER=google.
    """

    name = "google"

    def __init__(self) -> None:
        self.api_key = settings.GOOGLE_AI_API_KEY
        self.base_url = settings.GOOGLE_AI_BASE_URL.rstrip("/")
        self.text_model = settings.GOOGLE_AI_TEXT_MODEL
        self.vision_model = settings.GOOGLE_AI_VISION_MODEL
        self.timeout = settings.AI_TIMEOUT_SECONDS
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )
        return self._client

    async def _generate(self, parts: list[dict], model: str | None = None) -> dict[str, Any]:
        url = f"/v1beta/models/{model or self.text_model}:generateContent"
        body: dict[str, Any] = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"responseMimeType": "application/json"},
        }
        try:
            resp = await self._get_client().post(url, params={"key": self.api_key}, json=body)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            raise AIProviderError(f"Error de comunicación con Google AI: {e}") from e

        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as e:
            raise AIProviderError(
                f"Google AI no devolvió contenido: {data.get('error') or str(e)}"
            ) from e

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise AIProviderError("Google AI no devolvió JSON válido")

    def _system_prompt(self, task: str) -> str:
        return (
            "Eres el motor de verificación de datos 'VeriIA Ecuador'. "
            f"Tarea: {task}. Responde SIEMPRE en español con JSON válido."
        )

    async def analyze_text(self, text: str) -> dict[str, Any]:
        prompt = (
            "Analiza la siguiente afirmación y devuelve JSON con: "
            "language, sentiment {label, score}, claims [{text, confidence}], "
            "entities [{text, label}], topics [], suspicious_signals []. "
            f"Texto: {text}"
        )
        return await self._generate(
            [
                {"text": self._system_prompt("análisis NLP")},
                {"text": prompt},
            ]
        )

    async def analyze_image(self, image_path: str) -> dict[str, Any]:
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        prompt = (
            "Analiza esta imagen para verificación de contenido y devuelve JSON con: "
            "manipulation_score (0-1), deepfake_score (0-1), ocr_text, "
            "objects [{label, confidence}], metadata."
        )
        return await self._generate(
            [
                {"text": self._system_prompt("análisis de imagen")},
                {
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": encoded,
                    }
                },
                {"text": prompt},
            ],
            model=self.vision_model,
        )

    async def explain(self, payload: dict[str, Any], context: str | None = None) -> dict[str, Any]:
        prompt = (
            "Con base en el siguiente análisis previo, genera una explicación en español "
            "para un ciudadano. Devuelve JSON con: summary, recommended_verdict "
            "(true|false|mixed|unverified), confidence (0-1), reasoning [], fuentes_sugeridas []. "
            f"Análisis: {json.dumps(payload, ensure_ascii=False)}"
        )
        if context:
            prompt += f"\nAfirmación original: {context}"
        return await self._generate(
            [
                {"text": self._system_prompt("explicación de resultados")},
                {"text": prompt},
            ]
        )

    async def health(self) -> dict[str, Any]:
        try:
            resp = await self._get_client().get(
                "/v1beta/models", params={"key": self.api_key}, timeout=10
            )
            resp.raise_for_status()
            models = [m.get("name") for m in resp.json().get("models", [])]
            return {
                "provider": self.name,
                "reachable": True,
                "models_available": len(models),
            }
        except httpx.HTTPError as e:
            return {"provider": self.name, "reachable": False, "error": str(e)}
