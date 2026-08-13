"""Adaptación de contenidos para medios locales (Gemini + fallback local).

Convierte un texto (verificación, noticia, comunicado…) en formatos aptos para
radio, WhatsApp, lenguas indígenas, lectura fácil, notas editoriales,
comparativas de propuestas y boletines para medios regionales.
"""

from __future__ import annotations

import time
from typing import Any

from app.services.ai.base import AIProviderError
from app.services.ai.generate import generate_text

BASE_SYSTEM = (
    "Eres la herramienta de adaptación de contenidos de VeriIA Ecuador. "
    "Ayudas a medios locales, radios comunitarias y organizaciones a adaptar "
    "información verificada para distintas audiencias y formatos. "
    "Responde siempre en español (salvo que la tarea pida otro idioma), "
    "con lenguaje claro, neutro y sin inventar datos ni fuentes. "
    "No añadas información que no esté en el texto original. "
    "Si el texto menciona una verificación, presérvala tal cual."
)

TASKS: dict[str, dict[str, str]] = {
    "radio": {
        "label": "Cápsula de radio (90s)",
        "system": (
            BASE_SYSTEM
            + " Convierte el texto en un guion de cápsula de radio de 90 segundos "
            "(aprox. 180 palabras). Estructura: CORTINA/ENTRADA, cuerpo con datos "
            "clave, y CIERRE con recomendación. Usa lenguaje hablado, natural, con "
            "frases cortas y pausas (indicadas con …). Incluye sugerencias de "
            "entonación entre corchetes."
        ),
    },
    "whatsapp": {
        "label": "Texto para WhatsApp",
        "system": (
            BASE_SYSTEM
            + " Adapta el contenido a un mensaje de WhatsApp reenviable: texto breve, "
            "claro y directo (máx. 200 palabras), con emojis mínimos y un encabezado "
            "que llame la atención sin sensacionalismo. Termina con una línea "
            "«Comparte para que llegue a más personas» y la fuente de la verificación."
        ),
    },
    "kichwa": {
        "label": "Traducción a kichwa",
        "system": (
            BASE_SYSTEM
            + " Traduce el texto al kichwa ecuatoriano (kichwa unificado). Mantén "
            "nombres propios e instituciones en su forma original. Si un término no "
            "tiene equivalente claro, déjalo en español con su significado entre "
            "paréntesis. Al final añade una línea en español con una nota breve de "
            "qué es el texto."
        ),
    },
    "shuar": {
        "label": "Traducción a shuar",
        "system": (
            BASE_SYSTEM
            + " Traduce el texto al shuar (shuar chicham). Mantén nombres propios e "
            "instituciones en su forma original. Si un término no tiene equivalente "
            "claro, déjalo en español con su significado entre paréntesis. Al final "
            "añade una línea en español con una nota breve de qué es el texto."
        ),
    },
    "accesible": {
        "label": "Lectura fácil / accesible",
        "system": (
            BASE_SYSTEM
            + " Reescribe el texto en lectura fácil (norma IFLA/UNE 153101): frases "
            "cortas de una idea, palabras comunes, sin tecnicismos, voz activa, "
            "evitando metáforas. Organízalo con subtítulos cortos y viñetas. Debe "
            "ser comprensible para personas con discapacidad cognitiva o baja "
            "alfabetización digital."
        ),
    },
    "resumen": {
        "label": "Resumen ejecutivo",
        "system": (
            BASE_SYSTEM
            + " Resume el texto en un resumen ejecutivo (máx. 180 palabras) con: "
            "qué se dice, datos clave, y qué se debe verificar. Usa viñetas y "
            "lenguaje directo, útil para sala de redacción."
        ),
    },
    "redaccion": {
        "label": "Nota periodística / contexto",
        "system": (
            BASE_SYSTEM
            + " Convierte el contenido en una nota periodística breve (máx. 350 "
            "palabras) con titular, entradilla, datos clave y cierre con contexto. "
            "Usa estructura de pirámide invertida, citas solo si están en el texto, "
            "y sugiere 2-3 fuentes de contraste genéricas sin inventarlas."
        ),
    },
    "comparativa": {
        "label": "Comparativa de propuestas",
        "system": (
            BASE_SYSTEM
            + " El usuario te dará dos o más propuestas, planes o discursos separados "
            "por «///» o identificados. Compáralos en una tabla o listado por ejes "
            "temáticos (economía, salud, seguridad, educación, ambiente…). Señala "
            "diferencias, coincidencias y contradicciones de forma neutral. Si un "
            "tema no aparece, indícalo como «No abordado»."
        ),
    },
    "agenda": {
        "label": "Boletín / agenda editorial",
        "system": (
            BASE_SYSTEM
            + " Convierte el contenido en un boletín editorial diario para una "
            "redacción pequeña: 3-5 puntos de agenda con titular de trabajo, qué "
            "verificar, fuentes sugeridas y tiempo estimado. Formato breve, práctico "
            "y accionable."
        ),
    },
}


def _fallback(task: str, title: str, content: str) -> str:
    """Transformación local determinista cuando Gemini no está disponible."""
    body = content.strip()
    lines = [
        "[Modo local · Gemini no disponible — resultado generado con plantillas]"
    ]
    if title.strip():
        lines.append(f"\n📌 {title.strip()}")
    lines.append(body)
    if task in ("kichwa", "shuar"):
        lang = "kichwa" if task == "kichwa" else "shuar"
        lines.append(
            f"\n\n[Traducción a {lang} requiere la clave de Gemini en el backend. "
            "Este texto se muestra en su idioma original.]"
        )
    elif task == "radio":
        lines.append(
            "\n\n🎙️ SUGERENCIA: leer en ~90 segundos con pausas tras cada idea clave."
        )
    elif task == "whatsapp":
        lines.append("\n\n✅ Comparte para que llegue a más personas.")
    elif task == "redaccion":
        lines.append("\n\n#️⃣ Titular sugerido: usa la idea principal del texto.")
    elif task == "comparativa":
        parts = [p.strip() for p in body.split("///") if p.strip()]
        if len(parts) >= 2:
            header = ["\n\n| Eje | Propuesta 1 | Propuesta 2 |", "| --- | --- | --- |"]
            return "\n".join([lines[0], *header, "| (ejes) | (texto) | (texto) |", *parts])
    return "\n".join(lines)


async def adapt(payload: dict[str, Any]) -> dict[str, Any]:
    task = payload.get("task", "radio")
    title = (payload.get("title") or "").strip()
    content = (payload.get("content") or "").strip()
    extra = (payload.get("extra") or "").strip()

    if task not in TASKS:
        raise ValueError(f"Tarea de adaptación no soportada: {task}")
    if not content:
        raise ValueError("El contenido no puede estar vacío")

    spec = TASKS[task]
    started = time.perf_counter()

    prompt_parts = [f"Título/contexto: {title}"] if title else []
    prompt_parts.append(f"Contenido:\n{content}")
    if extra:
        prompt_parts.append(f"Indicación adicional:\n{extra}")
    user_prompt = "\n\n".join(prompt_parts)

    from app.core.config import get_settings

    provider = "local"
    model = "plantilla"
    output = ""

    settings = get_settings()
    if settings.GOOGLE_AI_API_KEY.strip():
        try:
            output = await generate_text(
                spec["system"],
                user_prompt,
                temperature=0.7,
                max_tokens=1024,
            )
            provider = "google"
            model = settings.GOOGLE_AI_TEXT_MODEL
        except AIProviderError:
            output = ""

    if not output:
        output = _fallback(task, title, content)

    processing_ms = int((time.perf_counter() - started) * 1000)
    return {
        "output": output,
        "task": task,
        "task_label": spec["label"],
        "provider": provider,
        "model": model,
        "processing_ms": processing_ms,
    }
