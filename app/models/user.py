from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import UserRole


class UserPublic(BaseModel):
    user_id: str
    username: str
    join_time: str
    role: UserRole
    submit_count: int
    resolve_count: int


class UserLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str
    password: str


class UserLoginResponse(BaseModel):
    user_id: str
    username: str
    role: UserRole


class UserRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=6)


class UserRoleUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: UserRole


class UserCreateAdminResponse(BaseModel):
    user_id: str
    username: str


class UserRoleUpdateResponse(BaseModel):
    user_id: str
    role: UserRole


class UserListResponse(BaseModel):
    total: int
    users: list[UserPublic]
