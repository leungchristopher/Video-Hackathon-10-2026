import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone

from .models import Job, JobError, JobRequest, JobResult
from .services.base import ServiceError

log = logging.getLogger(__name__)

Runner = Callable[[JobRequest, Callable[[str], None]], Awaitable[JobResult]]


def _now() -> datetime:
    return datetime.now(timezone.utc)


class JobManager:
    """In-process background jobs with a concurrency limit and a per-job timeout."""

    def __init__(self, runner: Runner, max_concurrent: int, timeout_s: float) -> None:
        self._runner = runner
        self._slots = asyncio.Semaphore(max_concurrent)
        self._timeout_s = timeout_s
        self._jobs: dict[str, Job] = {}
        self._tasks: set[asyncio.Task[None]] = set()

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def submit(self, request: JobRequest) -> Job:
        now = _now()
        job = Job(
            id=uuid.uuid4().hex,
            status="queued",
            stage="waiting for a free worker",
            request=request,
            created_at=now,
            updated_at=now,
        )
        self._jobs[job.id] = job
        task = asyncio.create_task(self._run(job))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return job

    def _update(self, job: Job, **fields: object) -> None:
        for name, value in fields.items():
            setattr(job, name, value)
        job.updated_at = _now()

    async def _run(self, job: Job) -> None:
        async with self._slots:
            self._update(job, status="running", stage="starting")
            try:
                result = await asyncio.wait_for(
                    self._runner(job.request, lambda stage: self._update(job, stage=stage)),
                    self._timeout_s,
                )
            except ServiceError as exc:
                error = JobError(service=exc.service, kind=exc.kind, message=exc.message)
                self._update(job, status="failed", error=error)
            except asyncio.TimeoutError:
                message = f"job exceeded the {self._timeout_s}s limit while {job.stage}"
                error = JobError(service=None, kind="timeout", message=message)
                self._update(job, status="failed", error=error)
            except Exception as exc:
                log.exception("job %s failed", job.id)
                error = JobError(
                    service=None, kind="internal", message=f"{type(exc).__name__}: {exc}"
                )
                self._update(job, status="failed", error=error)
            else:
                self._update(job, status="succeeded", stage="done", result=result)
