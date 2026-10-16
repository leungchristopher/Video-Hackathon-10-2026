import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from .cache import ResultCache
from .models import (
    Clip,
    ClipAnalysis,
    ClipDetections,
    EvidenceCard,
    Interval,
    JobRequest,
    JobResult,
    LlmReply,
    SearchHit,
)
from .prompts import (
    ANSWER_SYSTEM,
    CLIP_PROMPT,
    CLIP_PROMPT_VERSION,
    DETECTION_CONFIG_VERSION,
    answer_prompt,
)
from .services import Services

T = TypeVar("T", ClipAnalysis, ClipDetections)


class Pipeline:
    """Question -> VSS search -> VSS clip retrieval ->
    YOLO detection + Cosmos analysis (cached) -> W&B answer."""

    def __init__(self, services: Services, cache: ResultCache) -> None:
        self.services = services
        self.cache = cache

    async def run(self, request: JobRequest, set_stage: Callable[[str], None]) -> JobResult:
        set_stage("searching video")
        hits = await self.services.search.search(request.video_id, request.question, request.top_k)
        if not hits:
            reply = LlmReply(
                text="No matching moments were found.",
                model="none",
                source=self.services.search.source,
            )
            return JobResult(answer=reply, evidence=[])

        set_stage(f"retrieving {len(hits)} clips; detecting objects and analysing clips")
        evidence = list(await asyncio.gather(*(self._evidence(hit) for hit in hits)))

        set_stage("answering")
        answer = await self.services.llm.complete(
            ANSWER_SYSTEM, answer_prompt(request.question, evidence)
        )
        return JobResult(answer=answer, evidence=evidence)

    async def _evidence(self, hit: SearchHit) -> EvidenceCard:
        interval = Interval(video_id=hit.video_id, start_s=hit.start_s, end_s=hit.end_s)
        clip = await self.services.clips.get_clip(interval)
        detections, analysis = await asyncio.gather(
            self._cached(
                "detections",
                ClipDetections,
                clip,
                self.services.detector.model,
                DETECTION_CONFIG_VERSION,
                lambda: self.services.detector.detect(clip, DETECTION_CONFIG_VERSION),
            ),
            self._cached(
                "clip_analysis",
                ClipAnalysis,
                clip,
                self.services.analyzer.model,
                CLIP_PROMPT_VERSION,
                lambda: self.services.analyzer.analyze(clip, CLIP_PROMPT, CLIP_PROMPT_VERSION),
            ),
        )
        return EvidenceCard(
            **interval.model_dump(),
            score=hit.score,
            search_text=hit.text,
            search_source=hit.source,
            clip_url=clip.url,
            clip_source=clip.source,
            analysis=analysis,
            detections=detections,
        )

    async def _cached(
        self,
        kind: str,
        result_type: type[T],
        clip: Clip,
        model: str,
        prompt_version: str,
        fetch: Callable[[], Awaitable[T]],
    ) -> T:
        item = self.cache.get(kind, result_type, clip, model, prompt_version)
        if item is None:
            item = await fetch()
            self.cache.put(kind, item)
        return item
