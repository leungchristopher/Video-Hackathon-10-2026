import asyncio
import time

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.models import SearchHit
from app.services.test_responses import TestVideoSearch


def make_client(tmp_path, **overrides) -> TestClient:
    settings = Settings(
        _env_file=None,
        cache_path=str(tmp_path / "cache.sqlite3"),
        **overrides,
    )
    return TestClient(create_app(settings))


def run_job(client: TestClient) -> dict:
    response = client.post("/api/jobs", json={"video_id": "demo", "question": "What happens?"})
    assert response.status_code == 202
    job = response.json()
    deadline = time.monotonic() + 10
    while job["status"] in ("queued", "running"):
        assert time.monotonic() < deadline
        time.sleep(0.02)
        job = client.get(f"/api/jobs/{job['id']}").json()
    return job


def test_complete_flow_with_test_responses(tmp_path):
    with make_client(tmp_path) as client:
        config = client.get("/api/config").json()
        modes = {service["interface"]: service["mode"] for service in config["services"]}
        assert set(modes) == {
            "video_search",
            "clip_retrieval",
            "object_detection",
            "clip_analysis",
            "language_model",
        }
        assert set(modes.values()) == {"test"}

        job = run_job(client)
        assert job["status"] == "succeeded", job["error"]
        result = job["result"]
        assert result["answer"]["source"] == "test"
        assert result["answer"]["text"].startswith("[TEST RESPONSE]")
        evidence = result["evidence"]
        assert len(evidence) == 3
        assert evidence[0]["start_s"] == 1.0 and evidence[0]["end_s"] == 3.0
        assert all(
            card["start_s"] <= detection["time_s"] <= card["end_s"]
            for card in evidence
            for detection in card["detections"]["detections"]
        )

        again = run_job(client)
        assert all(card["analysis"]["cached"] for card in again["result"]["evidence"])
        assert all(card["detections"]["cached"] for card in again["result"]["evidence"])


@pytest.mark.parametrize(
    ("setting", "service"),
    [
        ("yolo_url", "YOLO object detection"),
        ("cosmos_url", "Cosmos clip analysis"),
    ],
)
def test_unreachable_service_fails_job(tmp_path, setting, service):
    with make_client(tmp_path, **{setting: "http://127.0.0.1:9"}) as client:
        job = run_job(client)
        assert job["status"] == "failed"
        assert job["error"]["service"] == service
        assert job["error"]["kind"] == "unavailable"
        assert "127.0.0.1:9" in job["error"]["message"]


def test_job_timeout(tmp_path, monkeypatch):
    async def slow_search(
        self: TestVideoSearch, video_id: str, query: str, top_k: int
    ) -> list[SearchHit]:
        await asyncio.sleep(1)
        return []

    monkeypatch.setattr(TestVideoSearch, "search", slow_search)
    with make_client(tmp_path, job_timeout_s=0.1) as client:
        job = run_job(client)
        assert job["status"] == "failed"
        assert job["error"]["kind"] == "timeout"
        assert "searching video" in job["error"]["message"]
