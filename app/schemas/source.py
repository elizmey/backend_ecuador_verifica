from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SourceCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    domain: str = Field(..., min_length=3, max_length=255)
    url: str | None = Field(None, max_length=500)
    category: str | None = Field(None, max_length=100)
    reliability_score: float = Field(0.8, ge=0.0, le=1.0)
    is_verified: bool = True
    notes: str | None = None


class SourceUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    domain: str | None = Field(None, min_length=3, max_length=255)
    url: str | None = Field(None, max_length=500)
    category: str | None = Field(None, max_length=100)
    reliability_score: float | None = Field(None, ge=0.0, le=1.0)
    is_verified: bool | None = None
    notes: str | None = None


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    domain: str
    url: str | None
    category: str | None
    reliability_score: float
    is_verified: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class SourceReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    analysis_result_id: int
    source: SourceRead
    match_type: str
    similarity: float | None
    snippet: str | None
