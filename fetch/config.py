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
    port: int = 8002

    # Playwright
    fetch_timeout_ms: int = 60_000

    # PDF rendering
    pdf_templates_dir: str = str(_PROJECT_ROOT / "pdf" / "templates")


settings = Settings()
