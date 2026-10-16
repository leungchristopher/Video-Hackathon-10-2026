from dataclasses import dataclass

from ..config import Settings
from ..models import ServiceInfo
from .base import ClipAnalyzer, ClipRetriever, LanguageModel, VideoSearch
from .cosmos import CosmosClipAnalyzer
from .test_responses import TestClipAnalyzer, TestClipRetriever, TestLanguageModel, TestVideoSearch
from .vss import VssClipRetriever, VssVideoSearch
from .wandb import WandbLanguageModel


@dataclass
class Services:
    search: VideoSearch
    clips: ClipRetriever
    analyzer: ClipAnalyzer
    llm: LanguageModel

    def info(self) -> list[ServiceInfo]:
        return [
            ServiceInfo(
                interface="video_search", provider=self.search.name, mode=self.search.source
            ),
            ServiceInfo(
                interface="clip_retrieval", provider=self.clips.name, mode=self.clips.source
            ),
            ServiceInfo(
                interface="clip_analysis", provider=self.analyzer.name, mode=self.analyzer.source
            ),
            ServiceInfo(interface="language_model", provider=self.llm.name, mode=self.llm.source),
        ]


def build_services(settings: Settings, media_url: str) -> Services:
    """Use a live adapter when its service is configured, otherwise the test response."""
    delay = settings.test_response_delay_s
    vss = bool(settings.vss_base_url)
    return Services(
        search=VssVideoSearch(settings) if vss else TestVideoSearch(delay),
        clips=VssClipRetriever(settings) if vss else TestClipRetriever(media_url, delay),
        analyzer=(
            CosmosClipAnalyzer(settings) if settings.cosmos_base_url else TestClipAnalyzer(delay)
        ),
        llm=WandbLanguageModel(settings) if settings.wandb_api_key else TestLanguageModel(delay),
    )
