from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from .base import ServiceError

T = TypeVar("T", bound=BaseModel)


async def post_json(
    service: str, url: str, payload: dict[str, Any], headers: dict[str, str], timeout_s: float
) -> Any:
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            response = await client.post(url, json=payload, headers=headers)
    except httpx.TimeoutException:
        raise ServiceError(
            service, "timeout", f"no response from {url} within {timeout_s}s"
        ) from None
    except httpx.HTTPError as exc:
        raise ServiceError(service, "unavailable", f"cannot reach {url}: {exc}") from exc
    if response.status_code >= 400:
        raise ServiceError(
            service, "http_error", f"HTTP {response.status_code} from {url}: {response.text[:300]}"
        )
    try:
        return response.json()
    except ValueError as exc:
        raise ServiceError(service, "bad_response", f"non-JSON response from {url}") from exc


def parse(service: str, model: type[T], data: Any, adapter_file: str) -> T:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise ServiceError(
            service,
            "bad_response",
            f"response does not match the adapter contract in {adapter_file}: "
            f"{exc.errors()[0]['msg']} at {exc.errors()[0]['loc']}",
        ) from exc


def bearer(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}
