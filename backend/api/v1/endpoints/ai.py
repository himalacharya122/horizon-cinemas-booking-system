from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from backend.api.deps import require_role
from backend.core.database import get_db
from backend.core.exceptions import HCBSException
from backend.schemas.ai import AIQueryRequest
from backend.services import ai_service

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
