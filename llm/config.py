from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Loads configuration from environment variables and .env file.
    Precedence: real env vars > .env file > field defaults.
    """

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    port: int = 8001

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"

    # Caching
    cache_llm_calls: bool = True
    cache_dir: str = str(_PROJECT_ROOT / "data" / "cache")


settings = Settings()
