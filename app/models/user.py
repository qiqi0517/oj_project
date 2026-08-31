from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import UserRole


class UserPublic(BaseModel):
    id: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8)


class UserLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str
    password: str