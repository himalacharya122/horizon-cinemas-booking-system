from typing import List

from sqlalchemy.orm import Session

from backend.models.ai_history import AIChatMessage, AIChatSession


def create_session(db: Session, user_id: int, title: str) -> AIChatSession:
    """Creates a new AI chat session."""
    session = AIChatSession(user_id=user_id, title=title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_user_sessions(db: Session, user_id: int) -> List[AIChatSession]:
    """Retrieves all chat sessions for a specific user."""
    return (
        db.query(AIChatSession)
        .filter(AIChatSession.user_id == user_id)
        .order_by(AIChatSession.updated_at.desc())
        .all()
    )


def get_session_messages(db: Session, session_id: int) -> List[AIChatMessage]:
    """Retrieves all messages for a specific session."""
    return (
        db.query(AIChatMessage)
        .filter(AIChatMessage.session_id == session_id)
        .order_by(AIChatMessage.created_at.asc())
        .all()
    )


def add_message(db: Session, session_id: int, role: str, content: str) -> AIChatMessage:
    """Adds a message to an existing session."""
    message = AIChatMessage(session_id=session_id, role=role, content=content)
    db.add(message)

    # Update session's updated_at timestamp
    session = db.query(AIChatSession).filter(AIChatSession.session_id == session_id).first()
    if session:
        session.updated_at = AIChatSession.updated_at  # Trigger onupdate

    db.commit()
    db.refresh(message)
    return message


def update_session_title(db: Session, session_id: int, title: str):
    """Updates the title of a chat session."""
    session = db.query(AIChatSession).filter(AIChatSession.session_id == session_id).first()
    if session:
        session.title = title
        db.commit()
