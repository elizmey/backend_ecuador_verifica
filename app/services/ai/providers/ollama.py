import base64
import json
from typing import Any

import httpx

from app.core.config import get_settings
from app.services.ai.base import AIProviderError, BaseAIProvider

settings = get_settings()


class OllamaAIProvider(BaseAIProvider):
    """Proveedor local vía Ollama (HTTP API en http://localhost:11434)."""

    name = "ollama"

    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.text_model = settings.OLLAMA_TEXT_MODEL
        self.vision_model = settings.OLLAMA_VISION_MODEL
        self.timeout = settings.AI_TIMEOUT_SECONDS
        self._client: httpx.AsyncClient | None = None

    async def _chat(self, messages: list[dict], model: str | None = None, json_mode: bool = True) -> dict[str, Any]:
        url = f"{self.base_url}/api/chat"
        body: dict[str, Any] = {
            "model": model or self.text_model,
            "messages": messages,
            "stream": False,
        }
        if json_mode:
            body["format"] = "json"
        try:
            resp = await self._get_client().post(url, json=body, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            raise AIProviderError(f"Error de comunicación con Ollama: {e}") from e

        content = data.get("message", {}).get("content", "")
        if json_mode:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                raise AIProviderError("Ollama no devolvió JSON válido")
        return {"text": content}

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url)
        return self._client

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
            [{"role": "system", "content": self._system_prompt("análisis NLP")},
             {"role": "user", "content": prompt}],
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
            [{"role": "system", "content": self._system_prompt("análisis de imagen")},
             {"role": "user", "content": prompt, "images": [encoded]}],
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
            [{"role": "system", "content": self._system_prompt("explicación de resultados")},
             {"role": "user", "content": prompt}],
        )

    async def health(self) -> dict[str, Any]:
        try:
            resp = await self._get_client().get("/api/tags", timeout=5)
            resp.raise_for_status()
            return {"provider": self.name, "reachable": True, "models": list(resp.json().get("models", []))}
        except httpx.HTTPError as e:
            return {"provider": self.name, "reachable": False, "error": str(e)}
