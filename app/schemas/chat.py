from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="user | assistant")
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="Mensaje del usuario")
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Historial previo (opcional, máx. 12 mensajes)",
        max_length=12,
    )


class ChatResponse(BaseModel):
    reply: str
    provider: str
    mode: str = Field(description="gemini | basic")
