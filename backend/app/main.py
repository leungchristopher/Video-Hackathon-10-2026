from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from .cache import ResultCache
from .config import Settings
from .jobs import JobManager
from .models import Health, Job, JobRequest, Video
from .pipeline import Pipeline
from .services import build_services


def _is_remote(url: str) -> bool:
    return url.startswith(("http://", "https://"))


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    remote = _is_remote(settings.video_url)
    media_url = settings.video_url if remote else f"/api/videos/{settings.video_id}/media"
    video = Video(id=settings.video_id, title=settings.video_title, media_url=media_url)
    services = build_services(settings, media_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        pipeline = Pipeline(services, ResultCache(settings.cache_path))
        app.state.jobs = JobManager(
            pipeline.run, settings.max_concurrent_jobs, settings.job_timeout_s
        )
        yield

    app = FastAPI(title="Video analysis", lifespan=lifespan)

    @app.get("/api/health")
    def health() -> Health:
        return Health(services=services.info())

    @app.get("/api/videos")
    def videos() -> list[Video]:
        return [video]

    @app.get("/api/videos/{video_id}/media")
    def media(video_id: str) -> FileResponse:
        path = Path(settings.video_url)
        if remote or video_id != video.id or not path.is_file():
            raise HTTPException(404, "no local media for this video")
        return FileResponse(path)

    @app.post("/api/jobs", status_code=202)
    async def create_job(request: JobRequest) -> Job:
        if request.video_id != video.id:
            raise HTTPException(404, f"unknown video_id {request.video_id!r}")
        return app.state.jobs.submit(request)

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str) -> Job:
        job = app.state.jobs.get(job_id)
        if job is None:
            raise HTTPException(404, f"unknown job {job_id!r}")
        return job

    return app


app = create_app()
