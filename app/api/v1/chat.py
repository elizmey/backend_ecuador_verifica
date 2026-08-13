from fastapi import APIRouter, HTTPException, status

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat

router = APIRouter()


@router.post(
    "",
    response_model=ChatResponse,
    summary="Chat con VeriIA Bot",
    description=(
        "Conversación con el asistente. Usa **Gemini** si `GOOGLE_AI_API_KEY` está "
        "configurada; si no, responde en modo básico local (y puede llamar al "
        "verificador cuando el mensaje parece una afirmación o enlace)."
    ),
)
async def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    try:
        history = [{"role": m.role, "content": m.content} for m in payload.history]
        result = await chat(payload.message, history)
        return ChatResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
