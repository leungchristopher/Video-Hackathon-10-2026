import sqlite3
import threading
from pathlib import Path
from typing import TypeVar

from .models import ClipAnalysis, ClipDetections, Interval

SCHEMA = """
CREATE TABLE IF NOT EXISTS results (
    kind TEXT NOT NULL,
    video_id TEXT NOT NULL,
    start_s REAL NOT NULL,
    end_s REAL NOT NULL,
    model TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    result TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (kind, video_id, start_s, end_s, model, prompt_version)
)
"""

T = TypeVar("T", ClipAnalysis, ClipDetections)


class ResultCache:
    """Results keyed by video, interval, model and prompt/config version."""

    def __init__(self, path: str) -> None:
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock, self._db:
            self._db.execute(SCHEMA)

    @staticmethod
    def _key(interval: Interval, model: str, version: str) -> tuple[str, float, float, str, str]:
        return (
            interval.video_id,
            round(interval.start_s, 3),
            round(interval.end_s, 3),
            model,
            version,
        )

    def get(
        self,
        kind: str,
        cls: type[T],
        interval: Interval,
        model: str,
        version: str,
    ) -> T | None:
        with self._lock:
            row = self._db.execute(
                "SELECT result FROM results WHERE kind=? AND video_id=? AND start_s=? AND end_s=?"
                " AND model=? AND prompt_version=?",
                (kind, *self._key(interval, model, version)),
            ).fetchone()
        if row is None:
            return None
        return cls.model_validate_json(row[0]).model_copy(update={"cached": True})

    def put(self, kind: str, item: ClipAnalysis | ClipDetections) -> None:
        key = self._key(item, item.model, item.prompt_version)
        with self._lock, self._db:
            self._db.execute(
                "INSERT OR REPLACE INTO results"
                " (kind, video_id, start_s, end_s, model, prompt_version, result)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    kind,
                    *key,
                    item.model_copy(update={"cached": False}).model_dump_json(),
                ),
            )
