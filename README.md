# Video-Hackathon-10-2026

Minimal video question-answering app. Ask a question about a video; a background job
searches the video, retrieves and analyses matching clips, and asks a language model for an
answer. Evidence cards show each moment; click a timestamp to move playback there.

- Frontend: React, Vite, TypeScript (`frontend/`)
- Backend: Python, FastAPI, Pydantic (`backend/`)
- External services (called over HTTP, nothing is installed locally):
  VAST/VSS (video search, clip retrieval), Cosmos (clip analysis), W&B Inference (language model)

The app runs without credentials. Any unconfigured service returns canned **test responses**,
marked `source: "test"` in the API and with a yellow `TEST RESPONSE` badge and banner in the UI.

## Setup

Requires Python 3.10+, Node 22+ (see `.nvmrc`) and `make`.

```sh
make setup   # backend venv, npm ci, .env from .env.example, demo video (needs ffmpeg)
make dev     # backend on :8000, frontend on http://127.0.0.1:5173 (proxies /api)
make check   # ruff, pytest (full flow + service failure + timeout), tsc + vite build
```

## How it works

```
POST /api/jobs {video_id, question}
  -> video search (VAST/VSS)          hits with start_s/end_s
  -> clip retrieval (VAST/VSS)        per hit
  -> clip analysis (Cosmos)           per clip, cached in SQLite
  -> language model (W&B Inference)   answer citing [12.0s]-style timestamps
GET /api/jobs/{id}                    status: queued | running | succeeded | failed
```

- All timestamps are seconds from the start of the source video (`start_s`, `end_s`).
- Jobs run in-process with at most `MAX_CONCURRENT_JOBS` at once; extra jobs stay `queued`.
  Each job is limited to `JOB_TIMEOUT_S`, each service call to `SERVICE_TIMEOUT_S`.
- A failed job reports `error: {service, kind, message}` where `kind` is one of
  `timeout`, `unavailable`, `http_error`, `bad_response`, `internal`.
- Clip analyses are cached in SQLite (`CACHE_PATH`) by video, interval, model and prompt
  version. Change `CLIP_PROMPT_VERSION` in `backend/app/prompts.py` when editing the prompt.
- Other endpoints: `GET /api/health` (which services are live or test), `GET /api/videos`.

Interfaces are in `backend/app/services/base.py`; test responses in
`backend/app/services/test_responses.py`.

## Connecting services

Credentials stay in `.env` on the backend (ignored by Git) and are never sent to the browser.
Restart `make dev` after editing `.env`; `GET /api/health` shows which services are live.

The event API formats are not known, so the VAST/VSS and Cosmos adapters use a placeholder
contract defined in one file each. When the real API is documented, edit the request payload and
the `*Response` models in that file and convert any timestamps to source-video seconds there.
A response that does not match fails the job with a `bad_response` error naming the file.

| Service | Enable with | Adapter | Placeholder contract |
|---|---|---|---|
| VAST/VSS search | `VSS_BASE_URL`, `VSS_API_KEY` | `backend/app/services/vss.py` | `POST {VSS_SEARCH_PATH}` `{video_id, query, top_k}` → `{results: [{start_s, end_s, score, text}]}` |
| VAST/VSS clips | same | same | `POST {VSS_CLIP_PATH}` `{video_id, start_s, end_s}` → `{url}` |
| Cosmos | `COSMOS_BASE_URL`, `COSMOS_API_KEY`, `COSMOS_MODEL` | `backend/app/services/cosmos.py` | `POST {COSMOS_ANALYZE_PATH}` `{model, prompt, video_id, clip_url, start_s, end_s}` → `{text}` |
| W&B Inference | `WANDB_API_KEY`, `WANDB_PROJECT`, `WANDB_MODEL` | `backend/app/services/wandb.py` | OpenAI-compatible `POST {WANDB_BASE_URL}/chat/completions` |

API keys are sent as `Authorization: Bearer <key>`. For W&B, `WANDB_PROJECT` is your
`entity/project`, sent as the `OpenAI-Project` header.

The demo video `data/demo.mp4` is an ffmpeg test pattern whose on-screen counter shows the
source-video time, so you can check that clicking a timestamp seeks correctly. Without ffmpeg,
`make setup` skips it.

To use your own video, set `VIDEO_URL` to an http(s) URL or a local file path (served by the
backend) and `VIDEO_ID` to the identifier the search service uses for it.
