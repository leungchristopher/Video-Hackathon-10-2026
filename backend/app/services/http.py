from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from .base import ServiceError

T = TypeVar("T", bound=BaseModel)


async def post(
    service: str,
    url: str,
    api_key: str,
    payload: dict,
    response_model: type[T],
    timeout_s: float,
    headers: dict[str, str] | None = None,
) -> T:
    request_headers = dict(headers or {})
    if api_key:
        request_headers["Authorization"] = f"Bearer {api_key}"
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            response = await client.post(url, json=payload, headers=request_headers)
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
        data = response.json()
    except ValueError as exc:
        raise ServiceError(service, "bad_response", f"non-JSON response from {url}") from exc
    try:
        return response_model.model_validate(data)
    except ValidationError as exc:
        raise ServiceError(
            service,
            "bad_response",
            f"response does not match the {response_model.__name__} adapter contract: "
            f"{exc.errors()[0]['msg']} at {exc.errors()[0]['loc']}",
        ) from exc
