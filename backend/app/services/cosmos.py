"""Cosmos adapter for clip analysis.

The event API format is not known. The request and response shapes below are this
repository's own adapter contract; edit `AnalyzeResponse` and the payload in this file
once the real API is documented.
"""

from pydantic import BaseModel

from ..config import Settings
from ..models import Clip, ClipAnalysis
from .http import bearer, parse, post_json

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
        data = await post_json(
            NAME,
            self._s.cosmos_base_url.rstrip("/") + self._s.cosmos_analyze_path,
            {
                "model": self.model,
                "prompt": prompt,
                "video_id": clip.video_id,
                "clip_url": clip.url,
                "start_s": clip.start_s,
                "end_s": clip.end_s,
            },
            bearer(self._s.cosmos_api_key),
            self._s.service_timeout_s,
        )
        response = parse(NAME, AnalyzeResponse, data, __file__)
        return ClipAnalysis(
            video_id=clip.video_id,
            start_s=clip.start_s,
            end_s=clip.end_s,
            text=response.text,
            model=self.model,
            prompt_version=prompt_version,
            source="live",
        )
