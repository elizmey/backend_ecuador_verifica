"""Chat del VeriIA Bot: Gemini si hay API key, si no respuestas básicas locales."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.data.knowledge import INITIATIVES, TRUSTED_SOURCES
from app.services.ai.base import AIProviderError
from app.services.ai.generate import post_with_retry
from app.services.verifier import verify_claim

_INITIATIVES_LINE = "; ".join(
    f"{i['title']} ({i['slug']}): {i['short']}" for i in INITIATIVES
)

SYSTEM_PROMPT = (
    "Eres VeriIA Bot, asistente de verificación de desinformación de VeriIA Ecuador. "
    "Responde siempre en español, de forma clara, breve y útil (máx. 180 palabras). "
    "Usa texto plano: nada de asteriscos de markdown ni viñetas con **; usa "
    "números o guiones simples para listas.\n\n"
    "Qué es VeriIA Ecuador: plataforma ecuatoriana que combate la desinformación "
    "con verificación asistida por IA, monitoreo de narrativas y herramientas "
    "gratuitas para medios, periodistas y ciudadanía.\n"
    "Sus 10 iniciativas: "
    f"{_INITIATIVES_LINE}\n\n"
    "Si te preguntan por la plataforma o sus iniciativas, responde con esa "
    "información y sugiere ver la sección Soluciones (/soluciones). "
    "Ayudas a ciudadanos a verificar noticias, enlaces e imágenes. "
    "Si te pasan una afirmación dudosa, indícales que la verifiquen en /analizar "
    "y sugiere contrastar con fuentes oficiales de Ecuador (CNE, MSP, Ecuador Chequea). "
    "No inventes hechos. Si no estás seguro, dilo. "
    "No digas que eres Gemini salvo que te pregunten el motor."
)

_INITIATIVES_BY_SLUG = {i["slug"]: i for i in INITIATIVES}

_TOPIC_RULES: list[tuple[tuple[str, ...], str]] = [
    (("redaccion", "redacciones", "resumir documento", "documentos oficiales", "borrador periodistico"), "redacciones"),
    (("deepfake", "contenido sintetico", "sintetico", "video falso", "audio falso", "imagen manipulada", "manipulada"), "verificacion"),
    (("monitoreo", "narrativa", "narrativas", "campaña coordinada", "campaña coordinada", "viral", "virales"), "monitoreo-de-narrativas"),
    (("alerta", "alertas", "colaborativ"), "alertas-colaborativas"),
    (("propuesta", "propuestas", "plan de gobierno", "candidato", "candidatos", "promesa", "promesas"), "analisis-de-propuestas"),
    (("kichwa", "shuar", "lenguas indigenas", "radio", "radios", "lectura facil", "accesible", "whatsapp", "cadenas"), "adaptacion-para-medios-locales"),
    (("alfabetizacion", "pensamiento critico", "juego", "simulador", "taller", "talleres"), "alfabetizacion-mediatica"),
    (("visualizacion", "visualizaciones", "grafico", "graficos", "datos electorales", "dashboards"), "visualizacion-de-datos"),
    (("agente conversacional", "agentes conversacionales", "asistente conversacional", "respuestas con fuente"), "agentes-conversacionales"),
    (("medios locales", "medios regionales", "medios comunitarios", "redaccion pequena", "recursos limitados", "radio comunitaria"), "fortalecimiento-de-medios-locales"),
]


def _is_url(text: str) -> bool:
    return bool(re.match(r"^https?://\S+$", text.strip(), re.I))


async def _chat_gemini(message: str, history: list[dict[str, str]]) -> str:
    settings = get_settings()
    if not settings.GOOGLE_AI_API_KEY.strip():
        raise AIProviderError("GOOGLE_AI_API_KEY no configurada")

    contents: list[dict[str, Any]] = []
    for item in history[-10:]:
        role = item.get("role", "user")
        gemini_role = "model" if role in ("assistant", "model", "bot") else "user"
        content = (item.get("content") or "").strip()
        if content:
            contents.append({"role": gemini_role, "parts": [{"text": content}]})
    contents.append({"role": "user", "parts": [{"text": message.strip()}]})

    url = (
        f"{settings.GOOGLE_AI_BASE_URL.rstrip('/')}"
        f"/v1beta/models/{settings.GOOGLE_AI_TEXT_MODEL}:generateContent"
    )
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.6,
            "maxOutputTokens": 512,
        },
    }

    try:
        resp = await post_with_retry(
            url,
            params={"key": settings.GOOGLE_AI_API_KEY},
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


async def _maybe_verify_snippet(message: str) -> str | None:
    """Si el mensaje parece una afirmación o URL, corre el verificador local."""
    text = message.strip()
    if len(text) < 8:
        return None
    # Evitar saludos cortos
    if text.lower() in {"hola", "hey", "buenas", "buenos días", "buenas tardes"}:
        return None

    looks_like_claim = _is_url(text) or (
        len(text.split()) >= 6
        and not text.rstrip().endswith("?")
        and any(
            k in text.lower()
            for k in (
                "causan",
                "provoca",
                "es falso",
                "es verdad",
                "dicen que",
                "según",
                "anunció",
                "vacun",
                "http",
            )
        )
    )
    if not looks_like_claim:
        return None

    try:
        result = await verify_claim(text)
    except Exception:
        return None
    label = result["verdict_label"]
    conf = int(round(float(result["confidence"]) * 100))
    expl = result["explanation"]
    sources = result.get("source_matches") or []
    src_txt = ""
    if sources:
        src_txt = " Fuentes detectadas: " + ", ".join(s["name"] for s in sources[:3]) + "."
    return (
        f"Veredicto automático: **{label}** (confianza {conf}%).\n\n"
        f"{expl}{src_txt}\n\n"
        "Puedes ver el detalle completo en Analizar → Resultados."
    )


def _about_reply(lower: str) -> str | None:
    if any(
        k in lower
        for k in (
            "qué es veriia",
            "que es veriia",
            "qué hace veriia",
            "que hace veriia",
            "quien eres",
            "quién eres",
            "qué eres",
            "que eres",
            "qué es esto",
            "que es esto",
            "qué hace la plataforma",
            "que hace la plataforma",
            "qué es la plataforma",
            "que es la plataforma",
        )
    ):
        return (
            "VeriIA Ecuador es una plataforma que combate la desinformación con "
            "verificación asistida por IA y herramientas gratuitas para medios, "
            "periodistas y ciudadanía. Tiene 10 iniciativas: redacciones, verificación "
            "de contenido sintético, monitoreo de narrativas, alertas colaborativas, "
            "análisis de propuestas, adaptación para medios locales, alfabetización "
            "mediática, visualización de datos, agentes conversacionales y "
            "fortalecimiento de medios locales. Puedes explorarlas todas en Soluciones "
            "(/soluciones)."
        )

    if any(
        k in lower
        for k in (
            "solucione",
            "iniciativa",
            "qué hacen",
            "que hacen",
            "qué herramientas",
            "que herramientas",
            "de qué se trata",
            "en qué consiste",
            "proyecto",
        )
    ):
        lista = "\n".join(f"- {i['title']}: {i['short']}" for i in INITIATIVES)
        return (
            "VeriIA Ecuador tiene 10 iniciativas:\n\n"
            f"{lista}\n\n"
            "Cada una incluye una herramienta funcional: entra a Soluciones "
            "(/soluciones) y abre la que te interese."
        )

    for keywords, slug in _TOPIC_RULES:
        if any(k in lower for k in keywords):
            s = _INITIATIVES_BY_SLUG[slug]
            return (
                f"Eso corresponde a la iniciativa «{s['title']}»: {s['short']} "
                f"Está en /soluciones/{slug} con una herramienta que puedes usar "
                "directamente desde la página."
            )
    return None


def _knowledge_reply(message: str) -> str | None:
    lower = message.lower().strip()

    if any(g in lower for g in ("hola", "buenas", "hey", "qué tal", "que tal")):
        return (
            "¡Hola! Soy VeriIA Bot. Puedo ayudarte a verificar noticias, enlaces e "
            "imágenes sospechosas, o contarte sobre las soluciones de VeriIA Ecuador. "
            "Pega una afirmación, un enlace o pregunta «¿cómo identifico noticias falsas?»."
        )

    if "fuente" in lower or "confiable" in lower:
        names = ", ".join(s["name"] for s in TRUSTED_SOURCES[:8])
        return (
            "Algunas fuentes de referencia que usamos: "
            f"{names}. "
            "También puedes contrastar con organismos oficiales (.gob.ec) y "
            "verificadores como Ecuador Chequea."
        )

    if any(
        k in lower
        for k in (
            "noticia falsa",
            "noticias falsas",
            "desinform",
            "identific",
            "detect",
        )
    ):
        return (
            "Seis señales para detectar desinformación:\n"
            "1) Fuente: revisa quién publica y si es un medio o entidad reconocida.\n"
            "2) Fecha: las noticias viejas suelen recircularse como si fueran nuevas.\n"
            "3) Tono: desconfía del alarmismo, los insultos o el «comparte urgente».\n"
            "4) Evidencia: exige datos, citas y enlaces verificables.\n"
            "5) Contraste: compara con medios y fuentes oficiales (.gob.ec).\n"
            "6) Verifica con VeriIA: pega el texto, enlace o imagen aquí (o en "
            "Analizar) y obtén un veredicto con su nivel de confianza."
        )

    if "imagen" in lower:
        return (
            "Para revisar una imagen, ve a Analizar → pestaña «Analizar imagen», "
            "súbela y opcionalmente añade contexto. Te devolveremos un nivel de "
            "riesgo y señales de manipulación."
        )

    if _is_url(lower) or "http" in lower:
        host = ""
        try:
            host = urlparse(message.strip().split()[0]).netloc
        except Exception:
            pass
        return (
            f"Recibí un enlace{f' ({host})' if host else ''}. "
            "Puedo revisar el dominio del medio; para verificar el contenido de la "
            "noticia pega el titular o el texto en Analizar, o escríbemelo aquí."
        )

    about = _about_reply(lower)
    if about:
        return about

    if len(lower.split()) <= 2:
        return (
            "Cuéntame un poco más: ¿quieres verificar una noticia, un enlace, "
            "saber cómo detectar desinformación o conocer las soluciones de VeriIA?"
        )

    return None


def _fallback_reply(message: str) -> str:
    return (
        "Entendido. Para un veredicto concreto, pega la afirmación o el enlace "
        "completo. Si quieres conocer la plataforma, escribe «soluciones». "
        "También puedes usar la página Analizar."
    )


async def chat(message: str, history: list[dict[str, str]] | None = None) -> dict[str, Any]:
    settings = get_settings()
    history = history or []
    msg = message.strip()
    if not msg:
        raise ValueError("El mensaje no puede estar vacío")

    # 1) Preguntas de conocimiento local (plataforma, soluciones, guías)
    local = _knowledge_reply(msg)
    if local:
        return {"reply": local, "provider": "mock", "mode": "knowledge"}

    # 2) Intentar Gemini si hay clave
    if settings.GOOGLE_AI_API_KEY.strip():
        try:
            reply = await _chat_gemini(msg, history)
            return {"reply": reply, "provider": "google", "mode": "gemini"}
        except AIProviderError:
            # cae a verificador local + respuestas básicas
            pass

    # 3) Si parece claim/URL, usar verificador local
    verified = await _maybe_verify_snippet(msg)
    if verified:
        return {"reply": verified, "provider": "mock", "mode": "basic"}

    # 4) Respuesta genérica (solo si no hay Gemini)
    return {"reply": _fallback_reply(msg), "provider": "mock", "mode": "basic"}
