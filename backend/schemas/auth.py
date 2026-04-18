"""
backend/schemas/auth.py
Pydantic models for authentication requests and responses.
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, examples=["himal"])
    password: str = Field(..., min_length=1, max_length=128, examples=["Password123#"])


class UserInfo(BaseModel):
    user_id: int
    username: str
    full_name: str
    role: str
    cinema_id: int
    cinema_name: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo
