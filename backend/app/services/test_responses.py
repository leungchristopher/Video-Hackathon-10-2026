"""Test responses used when a service is not configured. Every result has source="test"."""

import asyncio
import re

from ..models import Clip, ClipAnalysis, ClipDetections, Detection, Interval, LlmReply, SearchHit

LABEL = "[TEST RESPONSE]"

# Source-video intervals in seconds with canned descriptions. Not derived from the video.
MOMENTS = [
    (12.0, 18.5, "a figure walks into the frame from the left"),
    (47.0, 55.0, "a close-up shot with little camera movement"),
    (95.0, 104.0, "several objects move quickly across the scene"),
    (181.0, 192.5, "a character interacts with an object on the ground"),
    (322.0, 331.0, "a chase moves from the foreground to the background"),
]


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower()))


class TestVideoSearch:
    name = "Test video search"
    source = "test"

    def __init__(self, delay_s: float) -> None:
        self._delay = delay_s

    async def search(self, video_id: str, query: str, top_k: int) -> list[SearchHit]:
        await asyncio.sleep(self._delay)
        q = _words(query)
        hits = [
            SearchHit(
                video_id=video_id,
                start_s=start,
                end_s=end,
                score=round(0.5 + 0.1 * len(q & _words(text)) - 0.01 * i, 3),
                text=f"{LABEL} {text}",
                source="test",
            )
            for i, (start, end, text) in enumerate(MOMENTS)
        ]
        return sorted(hits, key=lambda h: h.score, reverse=True)[:top_k]


class TestClipRetriever:
    name = "Test clip retrieval"
    source = "test"

    def __init__(self, media_url: str, delay_s: float) -> None:
        self._media_url = media_url
        self._delay = delay_s

    async def get_clip(self, interval: Interval) -> Clip:
        await asyncio.sleep(self._delay)
        url = f"{self._media_url}#t={interval.start_s},{interval.end_s}"
        return Clip(**interval.model_dump(), url=url, source="test")


class TestClipAnalyzer:
    name = "Test clip analysis"
    source = "test"
    model = "test-clip-analyzer"

    def __init__(self, delay_s: float) -> None:
        self._delay = delay_s

    async def analyze(self, clip: Clip, prompt: str, prompt_version: str) -> ClipAnalysis:
        await asyncio.sleep(self._delay)
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
    labels = ("person", "car", "dog", "bicycle")

    def __init__(self, delay_s: float) -> None:
        self._delay = delay_s

    async def detect(self, clip: Clip, config_version: str) -> ClipDetections:
        await asyncio.sleep(self._delay)
        index = int(clip.start_s) % len(self.labels)
        midpoint = (clip.start_s + clip.end_s) / 2
        detections = [
            Detection(
                label=self.labels[index],
                confidence=0.91,
                time_s=clip.start_s + 1.0,
                box=(0.1, 0.2, 0.4, 0.8),
            ),
            Detection(
                label=self.labels[(index + 1) % len(self.labels)],
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

    def __init__(self, delay_s: float) -> None:
        self._delay = delay_s

    async def complete(self, system: str, user: str) -> LlmReply:
        await asyncio.sleep(self._delay)
        stamps = re.findall(r"^\[(\d+(?:\.\d+)?)s-", user, flags=re.MULTILINE)
        cited = ", ".join(f"[{s}s]" for s in stamps) or "no evidence"
        text = f"{LABEL} Canned answer. No language model was called. Relevant moments: {cited}."
        return LlmReply(text=text, model=self.model, source="test")
