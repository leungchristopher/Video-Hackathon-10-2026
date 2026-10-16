"""VAST/VSS adapter for video search and clip retrieval.

The event API format is not known. The request and response shapes below are this
repository's own adapter contract; edit `*Request`/`*Response` and the mapping in this
file once the real API is documented. Convert any timestamps to source-video seconds here.
"""

from pydantic import BaseModel

from ..config import Settings
from ..models import Clip, Interval, SearchHit
from .http import bearer, parse, post_json

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
        data = await post_json(
            SEARCH,
            self._s.vss_base_url.rstrip("/") + self._s.vss_search_path,
            {"video_id": video_id, "query": query, "top_k": top_k},
            bearer(self._s.vss_api_key),
            self._s.service_timeout_s,
        )
        response = parse(SEARCH, SearchResponse, data, __file__)
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
        data = await post_json(
            CLIPS,
            self._s.vss_base_url.rstrip("/") + self._s.vss_clip_path,
            interval.model_dump(),
            bearer(self._s.vss_api_key),
            self._s.service_timeout_s,
        )
        response = parse(CLIPS, ClipResponse, data, __file__)
        return Clip(**interval.model_dump(), url=response.url, source="live")
