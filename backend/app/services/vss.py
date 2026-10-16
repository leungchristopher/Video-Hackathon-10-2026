"""VAST/VSS API is unknown; edit this placeholder contract when it is documented."""

from pydantic import BaseModel

from ..config import Settings
from ..models import Clip, Interval, SearchHit
from .http import post

SEARCH = "VAST/VSS video search"
CLIPS = "VAST/VSS clip retrieval"


class SearchResult(BaseModel):
    start_s: float
    end_s: float
    score: float
    text: str


class SearchResponse(BaseModel):
    results: list[SearchResult]


class ClipResponse(BaseModel):
    url: str | None


class VssVideoSearch:
    name = SEARCH
    source = "live"

    def __init__(self, settings: Settings) -> None:
        self._s = settings

    async def search(self, video_id: str, query: str, top_k: int) -> list[SearchHit]:
        response = await post(
            SEARCH,
            self._s.vss_search_url,
            self._s.vss_api_key,
            {"video_id": video_id, "query": query, "top_k": top_k},
            SearchResponse,
            self._s.service_timeout_s,
        )
        return [
            SearchHit(video_id=video_id, source="live", **r.model_dump())
            for r in response.results[:top_k]
        ]


class VssClipRetriever:
    name = CLIPS
    source = "live"

    def __init__(self, settings: Settings) -> None:
        self._s = settings

    async def get_clip(self, interval: Interval) -> Clip:
        response = await post(
            CLIPS,
            self._s.vss_clip_url,
            self._s.vss_api_key,
            interval.model_dump(),
            ClipResponse,
            self._s.service_timeout_s,
        )
        return Clip(**interval.model_dump(), url=response.url, source="live")
