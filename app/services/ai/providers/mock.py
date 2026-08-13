import hashlib
import os
import re
import struct
from typing import Any

from app.services.ai.base import BaseAIProvider

# Nombres típicos de capturas de pantalla del SO → casi siempre UI real, no IA.
_SCREENSHOT_NAME = re.compile(
    r"(captura\s*de\s*pantalla|screenshot|screen[\s_-]?shot|captura|snipping|print\s*screen)",
    re.IGNORECASE,
)

# Señales de contenido sintético / manipulado en el nombre.
_AI_NAME = re.compile(
    r"(midjourney|dall[\s-]?e|stable[\s_-]?diffusion|deepfake|ai[\s_-]?generat|"
    r"generated|synth|fake[\s_-]?face|face[\s_-]?swap)",
    re.IGNORECASE,
)

# Texto típico de instaladores / Office / Windows (si aparece en bytes o claim).
_UI_HINTS = (
    "microsoft",
    "office",
    "windows",
    "hemos terminado",
    "cerrar",
    "instal",
    "aplicaciones",
    "configur",
    "aceptar",
    "siguiente",
    "finish",
    "setup",
)


class MockAIProvider(BaseAIProvider):
    """Proveedor determinista para desarrollo y tests (sin modelos reales).

    Para imágenes usa heurísticas del archivo/nombre (no CV real): capturas de
    pantalla y UIs normales salen con bajo riesgo; solo se eleva si hay indicios
    claros de contenido sintético o manipulación.
    """

    name = "mock"

    def _seed(self, value: str) -> int:
        return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:8], 16)

    def _seed_bytes(self, data: bytes) -> int:
        return int(hashlib.sha256(data).hexdigest()[:8], 16)

    def _confidence(self, value: str) -> float:
        return round(0.5 + (self._seed(value) % 40) / 100, 2)

    async def analyze_text(self, text: str) -> dict[str, Any]:
        import re
        from urllib.parse import urlparse

        raw = text.strip()
        url_re = re.compile(r"https?://[^\s]+", re.IGNORECASE)
        urls = url_re.findall(raw)
        is_url_only = bool(urls) and url_re.sub("", raw).strip() == ""

        # Palabras reales (sin query params de URL)
        content = url_re.sub(" ", raw)
        words = [w for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9]+", content) if len(w) > 1]
        word_count = len(words)
        sentences = raw.count(".") + raw.count("!") + raw.count("?") or 1
        seed = self._seed(raw)
        lower = raw.lower()

        claims = []
        if not is_url_only:
            for i in range(min(3, sentences)):
                chunk = raw.split(".")[i].strip() if "." in raw else raw[:80]
                if chunk and not chunk.lower().startswith("http"):
                    claims.append(
                        {"text": chunk[:200], "confidence": self._confidence(chunk)}
                    )

        topics: list[str] = []
        entities: list[dict[str, str]] = []
        if "ecuador" in lower:
            entities.append({"text": "Ecuador", "label": "GPE"})
            topics.append("ecuador")
        if any(k in lower for k in ("salud", "vacun", "covid", "oms")):
            topics.append("salud")
        if any(k in lower for k in ("voto", "eleccion", "politic", "gobierno")):
            topics.append("política")
        if is_url_only and urls:
            host = urlparse(urls[0]).netloc.lower().removeprefix("www.")
            entities.append({"text": host, "label": "ORG"})
            topics.append("enlace")

        # Señales reales, no aleatorias
        suspicious: list[str] = []
        if is_url_only:
            suspicious.append("solo_enlace")
        elif word_count < 4:
            suspicious.append("texto_muy_corto")

        emotional = (
            "urgente",
            "escandalo",
            "escándalo",
            "bomba",
            "ocult",
            "no te lo dicen",
            "compartir antes",
            "!!!!!!!",
            "alerta maxima",
            "alerta máxima",
        )
        if not is_url_only and any(e in lower for e in emotional):
            suspicious.append("lenguaje_emocional")

        return {
            "provider": self.name,
            "language": "es",
            "word_count": word_count,
            "is_url": is_url_only or bool(urls),
            "urls": urls[:5],
            "sentiment": {
                "label": "neutral" if is_url_only else ("negative" if "lenguaje_emocional" in suspicious else "neutral"),
                "score": self._confidence(raw),
            },
            "claims": claims,
            "entities": entities,
            "topics": topics or ["general"],
            "suspicious_signals": suspicious,
        }

    def _read_dimensions(self, data: bytes) -> tuple[int, int] | None:
        if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n":
            # IHDR: width/height big-endian after length+type
            try:
                w, h = struct.unpack(">II", data[16:24])
                if 0 < w < 20000 and 0 < h < 20000:
                    return w, h
            except struct.error:
                return None
        if len(data) > 3 and data[:2] == b"\xff\xd8":
            # JPEG: buscar SOF0/SOF2
            i = 2
            while i + 9 < len(data):
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                if marker in (0xC0, 0xC1, 0xC2):
                    try:
                        h, w = struct.unpack(">HH", data[i + 5 : i + 9])
                        if 0 < w < 20000 and 0 < h < 20000:
                            return w, h
                    except struct.error:
                        return None
                    break
                if marker == 0xD9:
                    break
                if marker in (0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0x01) or marker == 0xFF:
                    i += 1
                    continue
                if i + 4 > len(data):
                    break
                seg_len = struct.unpack(">H", data[i + 2 : i + 4])[0]
                i += 2 + seg_len
        return None

    def _extract_strings(self, data: bytes, limit: int = 40) -> list[str]:
        """Extrae cadenas legibles (título/UI a veces aparecen en metadatos)."""
        found: list[str] = []
        for match in re.finditer(rb"[\x20-\x7E\xC0-\xFF]{5,80}", data):
            try:
                text = match.group().decode("latin-1", errors="ignore").strip()
            except Exception:
                continue
            if text and text not in found:
                found.append(text)
            if len(found) >= limit:
                break
        return found

    def _detect_format(self, data: bytes, filename: str) -> str:
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        if data[:2] == b"\xff\xd8":
            return "image/jpeg"
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return "image/webp"
        ext = os.path.splitext(filename)[1].lower()
        return {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }.get(ext, "application/octet-stream")

    async def analyze_image(
        self,
        image_path: str,
        *,
        filename: str | None = None,
        claim: str | None = None,
    ) -> dict[str, Any]:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"No se encontró la imagen: {image_path}")

        size = os.path.getsize(image_path)
        with open(image_path, "rb") as f:
            data = f.read()

        name = filename or os.path.basename(image_path)
        claim_l = (claim or "").lower()
        name_l = name.lower()
        blob_text = " ".join(self._extract_strings(data)).lower()
        dims = self._read_dimensions(data)
        fmt = self._detect_format(data, name)
        seed = self._seed_bytes(data)

        is_screenshot = bool(_SCREENSHOT_NAME.search(name))
        is_ai_named = bool(_AI_NAME.search(name)) or bool(_AI_NAME.search(claim or ""))
        ui_hits = sum(1 for h in _UI_HINTS if h in blob_text or h in claim_l or h in name_l)
        looks_like_ui = ui_hits >= 1 or is_screenshot

        # Resolución típica de captura / monitor
        desktop_res = False
        if dims:
            w, h = dims
            desktop_res = (w >= 1024 and h >= 600) or (h >= 1024 and w >= 600)

        signals: list[str] = []
        objects: list[dict[str, Any]] = []

        if is_ai_named:
            # Solo elevamos fuerte con indicios explícitos de IA/deepfake
            manipulation = round(0.55 + (seed % 25) / 100, 2)
            deepfake = round(0.50 + (seed % 30) / 100, 2)
            signals.extend(["artefactos_de_compresion", "inconsistencias_faciales"])
            objects = [
                {"label": "person", "confidence": 0.72},
                {"label": "face", "confidence": 0.68},
            ]
            ocr = claim or "Posible contenido sintético ( indicios en el nombre/contexto )"
        elif looks_like_ui or (fmt == "image/png" and desktop_res and size > 40_000):
            # Capturas / instaladores / UI → riesgo bajo (auténtica)
            # Variación mínima determinista, siempre < 0.25
            manipulation = round(0.04 + (seed % 12) / 100, 2)  # 0.04–0.15
            deepfake = round(0.02 + (seed % 10) / 100, 2)  # 0.02–0.11
            objects = [
                {"label": "ui_window", "confidence": 0.91},
                {"label": "text", "confidence": 0.87},
                {"label": "button", "confidence": 0.74},
            ]
            if ui_hits or "microsoft" in blob_text or "microsoft" in claim_l:
                ocr = (
                    claim.strip()
                    if claim and claim.strip()
                    else "Interfaz de instalación / aplicación (p. ej. Microsoft 365 / Office)"
                )
            elif is_screenshot:
                ocr = claim.strip() if claim and claim.strip() else "Captura de pantalla del sistema"
            else:
                ocr = claim.strip() if claim and claim.strip() else "Interfaz o documento en pantalla"
            # Sin señales de deepfake/rostros inventados
        else:
            # Imagen genérica: sesgo a baja sospecha (demo honesta)
            manipulation = round(0.08 + (seed % 18) / 100, 2)  # 0.08–0.25
            deepfake = round(0.05 + (seed % 15) / 100, 2)  # 0.05–0.19
            if manipulation >= 0.22:
                signals.append("metadatos_ausentes")
            objects = [
                {"label": "photo", "confidence": round(0.7 + (seed % 20) / 100, 2)},
                {"label": "background", "confidence": 0.8},
            ]
            ocr = claim.strip() if claim and claim.strip() else ""

        risk = round(max(manipulation, deepfake), 2)

        meta: dict[str, Any] = {
            "file_size_bytes": size,
            "format": fmt,
            "heuristic": (
                "ai_named"
                if is_ai_named
                else "screenshot_or_ui"
                if looks_like_ui or (fmt == "image/png" and desktop_res)
                else "generic"
            ),
        }
        if dims:
            meta["resolution"] = f"{dims[0]}x{dims[1]}"
            meta["dimensions"] = [dims[0], dims[1]]

        return {
            "provider": self.name,
            "manipulation_score": manipulation,
            "deepfake_score": deepfake,
            "risk_score": risk,
            "ocr_text": ocr,
            "objects": objects,
            "signals": signals,
            "metadata": meta,
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
            "La imagen no presenta evidencias significativas de manipulación."
            if manipulation <= 0.5
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
