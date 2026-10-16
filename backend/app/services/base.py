from typing import Protocol

from ..models import Clip, ClipAnalysis, Interval, LlmReply, SearchHit, Source


class ServiceError(Exception):
    """A failure in an external service, reported to the user as-is."""

    def __init__(self, service: str, kind: str, message: str) -> None:
        super().__init__(f"{service}: {message}")
        self.service = service
        self.kind = kind
        self.message = message


class VideoSearch(Protocol):
    name: str
    source: Source

    async def search(self, video_id: str, query: str, top_k: int) -> list[SearchHit]: ...


class ClipRetriever(Protocol):
    name: str
    source: Source

    async def get_clip(self, interval: Interval) -> Clip: ...


class ClipAnalyzer(Protocol):
    name: str
    source: Source
    model: str

    async def analyze(self, clip: Clip, prompt: str, prompt_version: str) -> ClipAnalysis: ...


class LanguageModel(Protocol):
    name: str
    source: Source
    model: str

    async def complete(self, system: str, user: str) -> LlmReply: ...
