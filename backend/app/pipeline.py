import asyncio
from collections.abc import Callable

from .cache import AnalysisCache
from .models import EvidenceCard, Interval, JobRequest, JobResult, LlmReply, SearchHit
from .prompts import ANSWER_SYSTEM, CLIP_PROMPT, CLIP_PROMPT_VERSION, answer_prompt
from .services import Services


class Pipeline:
    """Question -> video search -> clip retrieval -> clip analysis (cached) -> answer."""

    def __init__(self, services: Services, cache: AnalysisCache) -> None:
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

        set_stage(f"retrieving and analysing {len(hits)} clips")
        evidence = list(await asyncio.gather(*(self._evidence(hit) for hit in hits)))

        set_stage("answering")
        prompt = answer_prompt(
            request.question, [(e.start_s, e.end_s, e.analysis.text) for e in evidence]
        )
        answer = await self.services.llm.complete(ANSWER_SYSTEM, prompt)
        return JobResult(answer=answer, evidence=evidence)

    async def _evidence(self, hit: SearchHit) -> EvidenceCard:
        interval = Interval(video_id=hit.video_id, start_s=hit.start_s, end_s=hit.end_s)
        clip = await self.services.clips.get_clip(interval)
        analyzer = self.services.analyzer
        key = (hit.video_id, hit.start_s, hit.end_s, analyzer.model, CLIP_PROMPT_VERSION)
        analysis = self.cache.get(*key)
        if analysis is None:
            analysis = await analyzer.analyze(clip, CLIP_PROMPT, CLIP_PROMPT_VERSION)
            self.cache.put(analysis)
        return EvidenceCard(
            **interval.model_dump(),
            score=hit.score,
            search_text=hit.text,
            search_source=hit.source,
            clip_url=clip.url,
            clip_source=clip.source,
            analysis=analysis,
        )
