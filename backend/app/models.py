from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Source = Literal["live", "test"]
JobState = Literal["queued", "running", "succeeded", "failed"]
ErrorKind = Literal["timeout", "unavailable", "http_error", "bad_response", "internal"]


class Interval(BaseModel):
    """A span of the source video. Seconds from the start of the source video."""

    video_id: str
    start_s: float = Field(ge=0)
    end_s: float = Field(ge=0)

    @model_validator(mode="after")
    def _ordered(self) -> "Interval":
        if self.end_s <= self.start_s:
            raise ValueError("end_s must be greater than start_s")
        return self


class SearchHit(Interval):
    score: float
    text: str
    source: Source


class Clip(Interval):
    url: str | None
    source: Source


class ClipAnalysis(Interval):
    text: str
    model: str
    prompt_version: str
    source: Source
    cached: bool = False


class Detection(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    time_s: float = Field(ge=0)
    box: tuple[float, float, float, float]

    @field_validator("box")
    @classmethod
    def _normalized_box(
        cls, box: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        if any(not 0 <= coordinate <= 1 for coordinate in box):
            raise ValueError("box coordinates must be normalized between 0 and 1")
        return box


class ClipDetections(Interval):
    detections: list[Detection]
    model: str
    prompt_version: str
    source: Source
    cached: bool = False


class LlmReply(BaseModel):
    text: str
    model: str
    source: Source


class EvidenceCard(Interval):
    score: float
    search_text: str
    search_source: Source
    clip_url: str | None
    clip_source: Source
    analysis: ClipAnalysis
    detections: ClipDetections


class JobRequest(BaseModel):
    video_id: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=10)


class JobError(BaseModel):
    service: str | None
    kind: ErrorKind
    message: str


class JobResult(BaseModel):
    answer: LlmReply
    evidence: list[EvidenceCard]


class Job(BaseModel):
    id: str
    status: JobState
    stage: str
    request: JobRequest
    created_at: datetime
    updated_at: datetime
    result: JobResult | None = None
    error: JobError | None = None


class ServiceInfo(BaseModel):
    interface: str
    provider: str
    mode: Source


class Health(BaseModel):
    services: list[ServiceInfo]


class Video(BaseModel):
    id: str
    title: str
    media_url: str
