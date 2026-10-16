"""W&B Inference adapter for language model calls (OpenAI-compatible chat completions)."""

from pydantic import BaseModel

from ..config import Settings
from ..models import LlmReply
from .base import ServiceError
from .http import bearer, parse, post_json

NAME = "W&B Inference language model"


class Message(BaseModel):
    content: str


class Choice(BaseModel):
    message: Message


class ChatResponse(BaseModel):
    choices: list[Choice]


class WandbLanguageModel:
    name = NAME
    source = "live"

    def __init__(self, settings: Settings) -> None:
        self._s = settings
        self.model = settings.wandb_model

    async def complete(self, system: str, user: str) -> LlmReply:
        headers = bearer(self._s.wandb_api_key)
        if self._s.wandb_project:
            headers["OpenAI-Project"] = self._s.wandb_project
        data = await post_json(
            NAME,
            self._s.wandb_base_url.rstrip("/") + "/chat/completions",
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.2,
            },
            headers,
            self._s.service_timeout_s,
        )
        response = parse(NAME, ChatResponse, data, __file__)
        if not response.choices:
            raise ServiceError(NAME, "bad_response", "response contained no choices")
        return LlmReply(text=response.choices[0].message.content, model=self.model, source="live")
