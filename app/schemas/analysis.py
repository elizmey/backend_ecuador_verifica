from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.analysis import AnalysisStage


class AnalysisResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    stage: AnalysisStage
    provider: str
    success: bool
    payload: dict[str, Any]
    latency_ms: float | None
    error: str | None
    created_at: datetime


class NLPRequest(BaseModel):
    text: str


class ExplainRequest(BaseModel):
    payload: dict[str, Any]
    context: str | None = None
