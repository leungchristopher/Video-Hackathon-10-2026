from dataclasses import dataclass

from ..config import Settings
from ..models import ServiceInfo
from .base import ClipAnalyzer, ClipRetriever, LanguageModel, ObjectDetector, VideoSearch
from .cosmos import CosmosClipAnalyzer
from .test_responses import (
    TestClipAnalyzer,
    TestClipRetriever,
    TestLanguageModel,
    TestObjectDetector,
    TestVideoSearch,
)
from .vss import VssClipRetriever, VssVideoSearch
from .wandb import WandbLanguageModel
from .yolo import YoloObjectDetector


@dataclass
class Services:
    search: VideoSearch
    clips: ClipRetriever
    detector: ObjectDetector
    analyzer: ClipAnalyzer
    llm: LanguageModel

    def info(self) -> list[ServiceInfo]:
        pairs = [
            ("video_search", self.search),
            ("clip_retrieval", self.clips),
            ("object_detection", self.detector),
            ("clip_analysis", self.analyzer),
            ("language_model", self.llm),
        ]
        return [
            ServiceInfo(interface=interface, provider=service.name, mode=service.source)
            for interface, service in pairs
        ]


def build_services(settings: Settings) -> Services:
    return Services(
        search=VssVideoSearch(settings) if settings.vss_search_url else TestVideoSearch(),
        clips=(
            VssClipRetriever(settings)
            if settings.vss_clip_url
            else TestClipRetriever(settings.video_url)
        ),
        detector=YoloObjectDetector(settings) if settings.yolo_url else TestObjectDetector(),
        analyzer=CosmosClipAnalyzer(settings) if settings.cosmos_url else TestClipAnalyzer(),
        llm=WandbLanguageModel(settings) if settings.wandb_api_key else TestLanguageModel(),
    )
