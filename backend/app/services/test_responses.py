"""Test responses used when a service is not configured. Every result has source="test"."""

import re

from ..models import Clip, ClipAnalysis, ClipDetections, Detection, Interval, LlmReply, SearchHit

LABEL = "[TEST RESPONSE]"

MOMENTS = [
    (1.0, 3.0, "a figure walks into the frame from the left"),
    (4.0, 6.5, "a character interacts with an object on the ground"),
    (7.0, 9.5, "something moves from the foreground to the background"),
]


class TestVideoSearch:
    name = "Test video search"
    source = "test"

    async def search(self, video_id: str, query: str, top_k: int) -> list[SearchHit]:
        hits = [
            SearchHit(
                video_id=video_id,
                start_s=start,
                end_s=end,
                score=round(0.9 - 0.1 * i, 1),
                text=f"{LABEL} {text}",
                source="test",
            )
            for i, (start, end, text) in enumerate(MOMENTS)
        ]
        return hits[:top_k]


class TestClipRetriever:
    name = "Test clip retrieval"
    source = "test"

    def __init__(self, video_url: str) -> None:
        self._video_url = video_url

    async def get_clip(self, interval: Interval) -> Clip:
        url = f"{self._video_url}#t={interval.start_s},{interval.end_s}"
        return Clip(**interval.model_dump(), url=url, source="test")


class TestClipAnalyzer:
    name = "Test clip analysis"
    source = "test"
    model = "test-clip-analyzer"

    async def analyze(self, clip: Clip, prompt: str, prompt_version: str) -> ClipAnalysis:
        text = (
            f"{LABEL} Canned analysis of {clip.start_s:.1f}s-{clip.end_s:.1f}s "
            f"({clip.end_s - clip.start_s:.1f}s long). No model was called."
        )
        return ClipAnalysis(
            **Interval.model_validate(clip.model_dump()).model_dump(),
            text=text,
            model=self.model,
            prompt_version=prompt_version,
            source="test",
        )


class TestObjectDetector:
    name = "Test object detection"
    source = "test"
    model = "test-object-detector"

    async def detect(self, clip: Clip, config_version: str) -> ClipDetections:
        midpoint = (clip.start_s + clip.end_s) / 2
        detections = [
            Detection(
                label="person",
                confidence=0.91,
                time_s=clip.start_s + 0.5,
                box=(0.1, 0.2, 0.4, 0.8),
            ),
            Detection(
                label="car",
                confidence=0.78,
                time_s=midpoint,
                box=(0.55, 0.1, 0.9, 0.95),
            ),
        ]
        return ClipDetections(
            **Interval.model_validate(clip.model_dump()).model_dump(),
            detections=detections,
            model=self.model,
            prompt_version=config_version,
            source="test",
        )


class TestLanguageModel:
    name = "Test language model"
    source = "test"
    model = "test-language-model"

    async def complete(self, system: str, user: str) -> LlmReply:
        stamps = re.findall(r"^\[(\d+(?:\.\d+)?)s-", user, flags=re.MULTILINE)
        cited = ", ".join(f"[{s}s]" for s in stamps) or "no evidence"
        text = f"{LABEL} Canned answer. No language model was called. Relevant moments: {cited}."
        return LlmReply(text=text, model=self.model, source="test")
