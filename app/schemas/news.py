from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.request import VerificationRequestRead


class NewsArticleCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=500)
    content: str = Field(..., min_length=10, max_length=100000)
    author: str | None = Field(None, max_length=255)
    url: str | None = Field(None, max_length=500)
    medium: str | None = Field(None, max_length=255)
    published_at: datetime | None = None


class NewsArticleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    author: str | None
    url: str | None
    medium: str | None
    published_at: datetime | None
    user_id: int | None
    created_at: datetime
    updated_at: datetime


class NewsArticleDetail(NewsArticleRead):
    verifications: list[VerificationRequestRead] = []


class NewsArticleList(BaseModel):
    items: list[NewsArticleRead]
    total: int
