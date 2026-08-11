import hashlib
import os
from typing import Any

from app.services.ai.base import BaseAIProvider


class MockAIProvider(BaseAIProvider):
    """Proveedor determinista para desarrollo y tests (sin modelos reales)."""

    name = "mock"

    def _seed(self, value: str) -> int:
        return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:8], 16)

    def _confidence(self, value: str) -> float:
        return round(0.5 + (self._seed(value) % 40) / 100, 2)

    async def analyze_text(self, text: str) -> dict[str, Any]:
        words = len(text.split())
        sentences = text.count(".") + text.count("!") + text.count("?") or 1
        seed = self._seed(text)

        claims = []
        for i in range(min(3, sentences)):
            chunk = text.split(".")[i].strip() if "." in text else text[:80]
            if chunk:
                claims.append(
                    {"text": chunk[:200], "confidence": self._confidence(chunk)}
                )

        topics = ["política", "salud", "seguridad"]
        entities = [
            {"text": "Ecuador", "label": "GPE"},
            {"text": "Quito", "label": "GPE"},
        ]

        suspicious = []
        if words < 10:
            suspicious.append("texto_muy_corto")
        if seed % 2 == 0:
            suspicious.append("lenguaje_emocional")

        return {
            "provider": self.name,
            "language": "es",
            "word_count": words,
            "sentiment": {
                "label": "negative" if seed % 3 == 0 else "neutral",
                "score": self._confidence(text),
            },
            "claims": claims,
            "entities": entities,
            "topics": topics,
            "suspicious_signals": suspicious,
        }

    async def analyze_image(self, image_path: str) -> dict[str, Any]:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"No se encontró la imagen: {image_path}")

        size = os.path.getsize(image_path)
        seed = self._seed(image_path)

        return {
            "provider": self.name,
            "manipulation_score": round((seed % 30) / 100, 2),
            "deepfake_score": round((seed % 15) / 100, 2),
            "ocr_text": "Texto de ejemplo extraído de la imagen",
            "objects": [
                {"label": "person", "confidence": 0.93},
                {"label": "background", "confidence": 0.88},
            ],
            "metadata": {"file_size_bytes": size},
        }

    async def explain(
        self, payload: dict[str, Any], context: str | None = None
    ) -> dict[str, Any]:
        nlp = payload.get("nlp", {})
        vision = payload.get("vision", [])
        manipulation = max((v.get("manipulation_score", 0) for v in vision), default=0)

        if manipulation > 0.5:
            verdict = "mixed"
        else:
            verdict = "false" if nlp.get("suspicious_signals") else "unverified"

        reasoning = [
            "El análisis NLP detectó señales de contenido manipulativo o emocional.",
            "La imagen no presenta evidencias significativas de manipulación." if manipulation <= 0.5
            else "La imagen presenta indicadores de manipulación que requieren revisión humana.",
        ]

        return {
            "provider": self.name,
            "summary": (
                "El contenido presenta elementos que sugieren verificación adicional. "
                "Se recomienda contrastar con fuentes oficiales."
            ),
            "recommended_verdict": verdict,
            "confidence": round(0.5 + manipulation / 2, 2),
            "reasoning": reasoning,
        }
