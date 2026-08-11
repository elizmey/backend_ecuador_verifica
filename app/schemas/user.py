from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=255)
    email: EmailStr | None = None
    password: str | None = Field(None, min_length=8, max_length=128)
    role: UserRole | None = None
    is_active: bool | None = None
