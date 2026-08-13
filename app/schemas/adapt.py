from typing import Literal

from pydantic import BaseModel, Field

AdaptTask = Literal[
    "radio",
    "whatsapp",
    "kichwa",
    "shuar",
    "accesible",
    "resumen",
    "redaccion",
    "comparativa",
    "agenda",
]


class AdaptRequest(BaseModel):
    content: str = Field(
        ..., min_length=1, max_length=8000, description="Contenido a adaptar"
    )
    task: AdaptTask = Field(
        "radio",
        description=(
            "Formato destino: radio | whatsapp | kichwa | shuar | accesible | "
            "resumen | redaccion | comparativa | agenda"
        ),
    )
    title: str = Field(
        default="", max_length=200, description="Título o contexto del contenido"
    )
    extra: str = Field(
        default="", max_length=1000, description="Indicación adicional opcional"
    )


class AdaptResponse(BaseModel):
    output: str
    task: str
    task_label: str
    provider: str = Field(description="google | local")
    model: str
    processing_ms: int
