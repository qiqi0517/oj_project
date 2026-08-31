from datetime import datetime
from pydantic import BaseModel
from app.models.enums import UserRole


class UserPublic(BaseModel):
    id: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserRegisterRequest(BaseModel):
    username: str
    password: str


class UserLoginRequest(BaseModel):
    username: str
    password: str