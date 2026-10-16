from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .cache import ResultCache
from .config import Settings
from .jobs import JobManager
from .models import AppConfig, Job, JobRequest
from .pipeline import Pipeline
from .services import build_services


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    services = build_services(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        pipeline = Pipeline(services, ResultCache(settings.cache_path))
        app.state.jobs = JobManager(
            pipeline.run, settings.max_concurrent_jobs, settings.job_timeout_s
        )
        yield

    app = FastAPI(title="Video analysis", lifespan=lifespan)

    @app.get("/api/config")
    def config() -> AppConfig:
        return AppConfig(
            video_id=settings.video_id,
            video_url=settings.video_url,
            services=services.info(),
        )

    @app.post("/api/jobs", status_code=202)
    async def create_job(request: JobRequest) -> Job:
        return app.state.jobs.submit(request)

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str) -> Job:
        job = app.state.jobs.get(job_id)
        if job is None:
            raise HTTPException(404, f"unknown job {job_id!r}")
        return job

    return app


app = create_app()
