# Video analysis harness

A minimal React/Vite/TypeScript and FastAPI/Pydantic app that links VSS search and clip
retrieval, YOLO object detection, Cosmos clip analysis, and W&B Inference. No models are
installed locally. Unconfigured services return clearly labelled test responses.

## Run

Requires Python 3.10+, Node 22+ and `make`.

```sh
make setup   # install pinned backend/frontend dependencies; create .env
make dev     # backend on :8000, frontend on http://127.0.0.1:5173
make check   # ruff, pytest, TypeScript and Vite build
```

## Flow

```text
POST /api/jobs {video_id, question}
  -> VSS search -> VSS clip retrieval
  -> YOLO detection + Cosmos analysis (cached)
  -> W&B answer with clickable citations
GET /api/jobs/{id}
GET /api/config
```

- Every timestamp is seconds from the start of the source video.
- Jobs run in-process with `MAX_CONCURRENT_JOBS`; job and service calls have separate timeouts.
- Errors are `{service, kind, message}` with kinds `timeout`, `unavailable`, `http_error`,
  `bad_response`, or `internal`.
- Analyses and detections are cached in SQLite (`CACHE_PATH`) by kind, video, interval, model,
  and prompt/config version.
- `VIDEO_ID` and `VIDEO_URL` select the video and its source URL.

## Services

Set service URLs and credentials in the backend `.env`; never send credentials to the browser.
Each adapter owns a placeholder contract to edit when the real API is known. Empty service
URLs or keys use test responses (`source: "test"`, `[TEST RESPONSE]` text, TEST badge).

| Service | Enable with | Placeholder contract |
|---|---|---|
| VSS search | `VSS_SEARCH_URL`, `VSS_API_KEY` | `POST VSS_SEARCH_URL {video_id, query, top_k}` → `{results: [{start_s, end_s, score, text}]}` |
| VSS clip retrieval | `VSS_CLIP_URL`, `VSS_API_KEY` | `POST VSS_CLIP_URL {video_id, start_s, end_s}` → `{url}` |
| YOLO | `YOLO_URL`, `YOLO_API_KEY`, `YOLO_MODEL` | `POST YOLO_URL {model, video_id, clip_url, start_s, end_s}` → `{detections: [{label, confidence, time_s, box}]}` |
| Cosmos | `COSMOS_URL`, `COSMOS_API_KEY`, `COSMOS_MODEL` | `POST COSMOS_URL {model, prompt, video_id, clip_url, start_s, end_s}` → `{text}` |
| W&B Inference | `WANDB_API_KEY`, `WANDB_PROJECT`, `WANDB_MODEL` | OpenAI-compatible chat completions |

YOLO `box` values are normalized `x1, y1, x2, y2` coordinates from 0 to 1. W&B uses
`WANDB_BASE_URL` and sends `WANDB_PROJECT` as the `OpenAI-Project` header.
