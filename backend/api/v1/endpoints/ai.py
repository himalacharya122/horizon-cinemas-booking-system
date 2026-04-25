from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from backend.api.deps import require_role
from backend.core.database import get_db
from backend.core.exceptions import HCBSException
from backend.schemas.ai import (
    AIChatMessageSchema,
    AIChatSessionSchema,
    AIQueryRequest,
    AISessionUpdate,
)
from backend.services import ai_service, ai_sessions_service, ai_suggestions_service

router = APIRouter(prefix="/ai", tags=["AI Analytics"])


class AIQueryResponse(BaseModel):
    answer: str
    sql: Optional[str] = None
    data_count: Optional[int] = None


@router.post("/query", response_model=AIQueryResponse)
async def ask_horizon_ai(
    body: AIQueryRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    """
    Ask the Horizon AI Assistant a question about cinema data.
    Restricted to Admin and Manager roles.
    """
    try:
        result = await ai_service.execute_ai_query(
            db=db, user_query=body.query, history=body.history, session_id=body.session_id
        )
        return result
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        import logging

        logging.error(f"AI Query Error: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An error occurred while processing your AI request."
        )


# Session Management


@router.get("/sessions", response_model=List[AIChatSessionSchema])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "manager")),
):
    """Lists all AI chat sessions for the current user."""
    return ai_sessions_service.get_user_sessions(db, int(current_user["sub"]))


@router.post("/sessions", response_model=AIChatSessionSchema)
def create_new_session(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "manager")),
):
    """Creates a new AI chat session."""
    return ai_sessions_service.create_session(db, int(current_user["sub"]), "New Chat")


@router.get("/sessions/{session_id}/messages", response_model=List[AIChatMessageSchema])
def get_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "manager")),
):
    """Retrieves all messages for a specific session."""
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


@router.patch("/sessions/{session_id}", response_model=AIChatSessionSchema)
def update_session(
    session_id: int,
    body: AISessionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "manager")),
):
    """Renames an AI chat session."""
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

    ai_sessions_service.update_session_title(db, session_id, body.title)
    return session


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "manager")),
):
    """Deletes an AI chat session."""
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

    ai_sessions_service.delete_session(db, session_id)
    return None


@router.get("/suggestions", response_model=List[str])
async def get_ai_suggestions(
    session_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "manager")),
):
    """Fetch 4 dynamic follow-up suggestions based on context."""
    history = []
    if session_id:
        messages = ai_sessions_service.get_session_messages(db, session_id)
        history = [{"role": msg.role, "content": msg.content} for msg in messages[-4:]]

    return await ai_suggestions_service.get_dynamic_suggestions(history)
