SHELL := /bin/bash
PYTHON ?= python3
VENV := backend/.venv
BIN := $(VENV)/bin

.PHONY: setup dev check

setup:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --quiet -r backend/requirements.txt -r backend/requirements-dev.txt
	cd frontend && npm ci
	@[ -f .env ] || (cp .env.example .env && echo "Created .env from .env.example")
	@$(MAKE) --no-print-directory data/demo.mp4

# Optional demo video: a test pattern with a seconds clock, to check timestamp seeking.
data/demo.mp4:
	@mkdir -p data
	@if command -v ffmpeg >/dev/null; then \
		ffmpeg -loglevel error -f lavfi -i testsrc=duration=360:size=640x360:rate=10 \
			-c:v libx264 -pix_fmt yuv420p -movflags +faststart $@ && echo "Created $@"; \
	else echo "ffmpeg not found: skipped $@. Set VIDEO_URL in .env to a video URL or file."; fi

dev:
	@trap 'kill 0' EXIT; \
	$(BIN)/uvicorn app.main:app --app-dir backend --reload --reload-dir backend/app \
		--host 127.0.0.1 --port 8000 & \
	(cd frontend && npm run dev -- --host 127.0.0.1) & \
	wait

check:
	$(BIN)/ruff check backend
	$(BIN)/ruff format --check backend
	cd backend && .venv/bin/pytest -q
	cd frontend && npm run build
