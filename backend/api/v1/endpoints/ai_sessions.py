from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.deps import require_role
from backend.core.database import get_db
from backend.schemas.ai import AIChatMessageSchema, AIChatSessionSchema
from backend.services import ai_sessions_service

router = APIRouter(prefix="/ai/sessions", tags=["AI History"])


@router.get("", response_model=List[AIChatSessionSchema])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "manager")),
):
    """Lists all AI chat sessions for the current user."""
    return ai_sessions_service.get_user_sessions(db, int(current_user["sub"]))


@router.post("", response_model=AIChatSessionSchema)
def create_new_session(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "manager")),
):
    """Creates a new AI chat session."""
    return ai_sessions_service.create_session(db, int(current_user["sub"]), "New Chat")


@router.get("/{session_id}/messages", response_model=List[AIChatMessageSchema])
def get_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "manager")),
):
    """Retrieves all messages for a specific session."""
    # Ensure session belongs to user
    session = (
        db.query(ai_sessions_service.AIChatSession)
        .filter(
            ai_sessions_service.AIChatSession.session_id == session_id,
            ai_sessions_service.AIChatSession.user_id == int(current_user["sub"]),
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    return ai_sessions_service.get_session_messages(db, session_id)
