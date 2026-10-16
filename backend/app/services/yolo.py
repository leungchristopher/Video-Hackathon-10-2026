"""YOLO adapter for object detection.

The event API format is not known. The request and response shapes below are this
repository's own adapter contract; edit `DetectResponse` and the payload in this file
once the real API is documented.
"""

from pydantic import BaseModel

from ..config import Settings
from ..models import Clip, ClipDetections, Detection, Interval
from .http import bearer, parse, post_json

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
        data = await post_json(
            NAME,
            self._s.yolo_base_url.rstrip("/") + self._s.yolo_detect_path,
            {
                "model": self.model,
                "video_id": clip.video_id,
                "clip_url": clip.url,
                "start_s": clip.start_s,
                "end_s": clip.end_s,
            },
            bearer(self._s.yolo_api_key),
            self._s.service_timeout_s,
        )
        response = parse(NAME, DetectResponse, data, __file__)
        return ClipDetections(
            **Interval.model_validate(clip.model_dump()).model_dump(),
            detections=response.detections,
            model=self.model,
            prompt_version=config_version,
            source="live",
        )
