"""Cosmos API is unknown; edit this placeholder contract when it is documented."""

from pydantic import BaseModel

from ..config import Settings
from ..models import Clip, ClipAnalysis
from .http import post

NAME = "Cosmos clip analysis"


class AnalyzeResponse(BaseModel):
    text: str


class CosmosClipAnalyzer:
    name = NAME
    source = "live"

    def __init__(self, settings: Settings) -> None:
        self._s = settings
        self.model = settings.cosmos_model

    async def analyze(self, clip: Clip, prompt: str, prompt_version: str) -> ClipAnalysis:
        response = await post(
            NAME,
            self._s.cosmos_url,
            self._s.cosmos_api_key,
            {
                "model": self.model,
                "prompt": prompt,
                "video_id": clip.video_id,
                "clip_url": clip.url,
                "start_s": clip.start_s,
                "end_s": clip.end_s,
            },
            AnalyzeResponse,
            self._s.service_timeout_s,
        )
        return ClipAnalysis(
            video_id=clip.video_id,
            start_s=clip.start_s,
            end_s=clip.end_s,
            text=response.text,
            model=self.model,
            prompt_version=prompt_version,
            source="live",
        )
