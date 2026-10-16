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
