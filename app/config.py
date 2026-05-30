from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST_DIR = ROOT_DIR / "frontend" / "dist"
EXPORTS_DIR = ROOT_DIR / "exports"
ENV_FILE = ROOT_DIR / ".env"
DB_PATH = ROOT_DIR / "api_translate.db"


class Settings(BaseSettings):
    app_name: str = "AI-Translator"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_reload: bool = False
    app_secret: str = "change-me-in-production"
    cors_origins: str = "*"
    session_cookie_name: str = "api_translate_session"
    csrf_cookie_name: str = "api_translate_csrf"
    session_ttl_hours: int = 12
    database_url: str = f"sqlite:///{DB_PATH.as_posix()}"
    request_timeout_seconds: int = 90
    rate_limit_per_minute: int = 120
    docs_enabled: bool = True

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> List[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
