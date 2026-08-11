from typing import Any

from pydantic import BaseModel, Field


class DetectedObject(BaseModel):
    label: str
    confidence: float


class ImageDetectionResponse(BaseModel):
    filename: str
    verdict: str
    verdict_label: str
    verdict_description: str
    risk_score: float
    manipulation_score: float
    deepfake_score: float
    ocr_text: str
    objects: list[DetectedObject] = Field(default_factory=list)
    signals: list[str] = Field(default_factory=list)
    explanation: str
    provider: str
    checked_at: str
    processing_ms: float
    metadata: dict[str, Any] = Field(default_factory=dict)
    claim: str | None = None


class DetectionVerdict(BaseModel):
    code: str
    label: str
    description: str


class DetectionHealth(BaseModel):
    provider: str
    reachable: bool
    error: str | None = None
