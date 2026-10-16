from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from the environment or `.env` in the repository root."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    video_id: str = "demo"
    video_url: str = (
        "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4"
    )
    vss_search_url: str = ""
    vss_clip_url: str = ""
    vss_api_key: str = ""
    yolo_url: str = ""
    yolo_api_key: str = ""
    yolo_model: str = "yolo"
    cosmos_url: str = ""
    cosmos_api_key: str = ""
    cosmos_model: str = "cosmos-reason"
    wandb_api_key: str = ""
    wandb_base_url: str = "https://api.inference.wandb.ai/v1"
    wandb_project: str = ""
    wandb_model: str = "meta-llama/Llama-3.1-8B-Instruct"
    max_concurrent_jobs: int = 2
    job_timeout_s: float = 120.0
    service_timeout_s: float = 30.0
    cache_path: str = "data/cache.sqlite3"
