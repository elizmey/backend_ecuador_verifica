from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.request import RequestMediaType, RequestStatus, Verdict
from app.schemas.analysis import AnalysisResultRead


class VerificationRequestCreate(BaseModel):
    claim: str = Field(..., min_length=3, max_length=10000)
    media_type: RequestMediaType = RequestMediaType.text


class VerificationRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    claim: str
    media_type: RequestMediaType
    images: list[str]
    status: RequestStatus
    verdict: Verdict | None
    confidence: float | None
    summary: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None


class VerificationRequestDetail(VerificationRequestRead):
    analyses: list[AnalysisResultRead] = []


class VerdictUpdate(BaseModel):
    verdict: Verdict
    summary: str | None = Field(None, max_length=10000)
    confidence: float | None = Field(None, ge=0.0, le=1.0)
