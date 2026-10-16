"""YOLO API is unknown; edit this placeholder contract when it is documented."""

from pydantic import BaseModel

from ..config import Settings
from ..models import Clip, ClipDetections, Detection, Interval
from .http import post

NAME = "YOLO object detection"


class DetectResponse(BaseModel):
    detections: list[Detection]


class YoloObjectDetector:
    name = NAME
    source = "live"

    def __init__(self, settings: Settings) -> None:
        self._s = settings
        self.model = settings.yolo_model

    async def detect(self, clip: Clip, config_version: str) -> ClipDetections:
        response = await post(
            NAME,
            self._s.yolo_url,
            self._s.yolo_api_key,
            {
                "model": self.model,
                "video_id": clip.video_id,
                "clip_url": clip.url,
                "start_s": clip.start_s,
                "end_s": clip.end_s,
            },
            DetectResponse,
            self._s.service_timeout_s,
        )
        return ClipDetections(
            **Interval.model_validate(clip.model_dump()).model_dump(),
            detections=response.detections,
            model=self.model,
            prompt_version=config_version,
            source="live",
        )
