import time

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def make_client(tmp_path, **overrides) -> TestClient:
    values = {"cache_path": str(tmp_path / "cache.sqlite3"), "test_response_delay_s": 0.01}
    settings = Settings(_env_file=None, **(values | overrides))
    return TestClient(create_app(settings))


def run_job(client: TestClient, question: str = "who walks into the frame?") -> dict:
    response = client.post("/api/jobs", json={"video_id": "demo", "question": question})
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
        modes = {s["interface"]: s["mode"] for s in client.get("/api/health").json()["services"]}
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
        assert evidence[0]["start_s"] == 12.0 and evidence[0]["end_s"] == 18.5
        assert all(card["analysis"]["source"] == "test" for card in evidence)
        assert not any(card["analysis"]["cached"] for card in evidence)
        assert all(card["detections"]["source"] == "test" for card in evidence)
        assert all(card["detections"]["detections"] for card in evidence)
        assert all(
            card["start_s"] <= detection["time_s"] <= card["end_s"]
            for card in evidence
            for detection in card["detections"]["detections"]
        )

        again = run_job(client)
        assert all(card["analysis"]["cached"] for card in again["result"]["evidence"])
        assert all(card["detections"]["cached"] for card in again["result"]["evidence"])


def test_unreachable_service_fails_job_with_clear_error(tmp_path):
    with make_client(tmp_path, cosmos_base_url="http://127.0.0.1:9") as client:
        job = run_job(client)
        assert job["status"] == "failed"
        assert job["error"]["service"] == "Cosmos clip analysis"
        assert job["error"]["kind"] == "unavailable"
        assert "127.0.0.1:9" in job["error"]["message"]


def test_yolo_failure(tmp_path):
    with make_client(tmp_path, yolo_base_url="http://127.0.0.1:9") as client:
        job = run_job(client)
        assert job["status"] == "failed"
        assert job["error"]["service"] == "YOLO object detection"
        assert job["error"]["kind"] == "unavailable"
        assert "127.0.0.1:9" in job["error"]["message"]


def test_job_timeout(tmp_path):
    with make_client(tmp_path, test_response_delay_s=1.0, job_timeout_s=0.1) as client:
        job = run_job(client)
        assert job["status"] == "failed"
        assert job["error"]["kind"] == "timeout"
        assert "searching video" in job["error"]["message"]


def test_rejects_unknown_video(tmp_path):
    with make_client(tmp_path) as client:
        response = client.post("/api/jobs", json={"video_id": "nope", "question": "x"})
        assert response.status_code == 404
