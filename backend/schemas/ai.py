from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class AIChatMessageSchema(BaseModel):
    message_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class AIChatSessionSchema(BaseModel):
    session_id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AIQueryRequest(BaseModel):
    query: str
    session_id: Optional[int] = None
    history: Optional[List[dict]] = None


class AISessionUpdate(BaseModel):
    title: str
