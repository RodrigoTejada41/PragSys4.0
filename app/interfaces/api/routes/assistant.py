from fastapi import APIRouter, Depends

from app.application.assistant_service import build_assistant_reply
from app.application.schemas import AssistantChatRequest, AssistantChatResponse
from app.infrastructure.models import User
from app.interfaces.api.deps import require_access

router = APIRouter(prefix="/assistente", tags=["assistente"])


@router.post("/chat", response_model=AssistantChatResponse)
def assistant_chat(
    payload: AssistantChatRequest,
    current_user: User = Depends(require_access(["master", "admin", "operador", "gestor_estoque"])),
) -> AssistantChatResponse:
    return build_assistant_reply(
        current_user=current_user,
        message=payload.message,
        current_view=payload.current_view,
        current_title=payload.current_title,
    )
