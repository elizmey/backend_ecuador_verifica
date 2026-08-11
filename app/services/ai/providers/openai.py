import base64
import json
from typing import Any

import httpx

from app.core.config import get_settings
from app.services.ai.base import AIProviderError, BaseAIProvider

settings = get_settings()


class OpenAICompatibleProvider(BaseAIProvider):
    """Proveedor OpenAI o compatible (OpenRouter, Azure, localhost, etc.).

    Se usa cuando OPENAI_API_KEY está definida y AI_PROVIDER=openai.
    """

    name = "openai"

    def __init__(self) -> None:
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL.rstrip("/")
        self.text_model = settings.OPENAI_TEXT_MODEL
        self.vision_model = settings.OPENAI_VISION_MODEL
        self.timeout = settings.AI_TIMEOUT_SECONDS
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
        return self._client

    async def _chat(
        self, messages: list[dict], model: str | None = None, json_mode: bool = True
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": model or self.text_model,
            "messages": messages,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        try:
            resp = await self._get_client().post("/chat/completions", json=body)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            raise AIProviderError(f"Error de comunicación con {self.name}: {e}") from e

        content = data["choices"][0]["message"]["content"]
        if json_mode:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                raise AIProviderError(f"{self.name} no devolvió JSON válido")
        return {"text": content}

    def _system_prompt(self, task: str) -> str:
        return (
            "Eres el motor de verificación de datos 'Ecuador Verifica'. "
            f"Tarea: {task}. Responde SIEMPRE en español con JSON válido."
        )

    async def analyze_text(self, text: str) -> dict[str, Any]:
        prompt = (
            "Analiza la siguiente afirmación y devuelve JSON con: "
            "language, sentiment {label, score}, claims [{text, confidence}], "
            "entities [{text, label}], topics [], suspicious_signals []. "
            f"Texto: {text}"
        )
        return await self._chat(
            [
                {"role": "system", "content": self._system_prompt("análisis NLP")},
                {"role": "user", "content": prompt},
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
        return await self._chat(
            [
                {"role": "system", "content": self._system_prompt("análisis de imagen")},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{encoded}"},
                        },
                    ],
                },
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
        return await self._chat(
            [
                {"role": "system", "content": self._system_prompt("explicación de resultados")},
                {"role": "user", "content": prompt},
            ]
        )

    async def health(self) -> dict[str, Any]:
        try:
            resp = await self._get_client().get("/models")
            resp.raise_for_status()
            return {"provider": self.name, "reachable": True}
        except httpx.HTTPError as e:
            return {"provider": self.name, "reachable": False, "error": str(e)}
