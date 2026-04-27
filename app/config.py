from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://treaties:treaties@localhost:5432/treaties"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b-instruct-q4_K_M"
    ollama_timeout_seconds: int = 180

    app_host: str = "127.0.0.1"
    app_port: int = 8000
    snapshot_dir: Path = Path("./snapshots")


settings = Settings()
settings.snapshot_dir.mkdir(parents=True, exist_ok=True)
