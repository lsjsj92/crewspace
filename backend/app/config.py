from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"


def load_yaml_config() -> dict[str, Any]:
    yaml_path = CONFIG_DIR / "settings.yaml"
    if yaml_path.exists():
        with open(yaml_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


_yaml_config = load_yaml_config()


class Settings(BaseSettings):
    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "crewspace"
    POSTGRES_USER: str = "crewspace"
    POSTGRES_PASSWORD: str = "changeme_strong_password"

    # JWT
    SECRET_KEY: str = "changeme_jwt_secret_key_at_least_32_chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = _yaml_config.get("auth", {}).get(
        "access_token_expire_minutes", 15
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = _yaml_config.get("auth", {}).get(
        "refresh_token_expire_days", 7
    )

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # 이메일 도메인
    EMAIL_DOMAIN: str = "example.com"

    # Superadmin
    SUPERADMIN_EMAIL: str = "admin@crewspace.local"
    SUPERADMIN_USERNAME: str = "admin"
    SUPERADMIN_PASSWORD: str = "changeme_admin_password"

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


class AppConfig:
    """YAML-based application config (non-secret settings)."""

    def __init__(self) -> None:
        self._data = _yaml_config

    @property
    def board(self) -> dict[str, Any]:
        return self._data.get("board", {})

    @property
    def card(self) -> dict[str, Any]:
        return self._data.get("card", {})

    @property
    def scheduler(self) -> dict[str, Any]:
        return self._data.get("scheduler", {})

    @property
    def default_columns(self) -> list[dict[str, Any]]:
        return self.board.get("default_columns", [])

    @property
    def max_columns(self) -> int:
        return self.board.get("max_columns", 5)

    @property
    def min_columns(self) -> int:
        return self.board.get("min_columns", 2)

    @property
    def position_gap(self) -> int:
        return self.card.get("position_gap", 1000)

    @property
    def auto_archive_days(self) -> int:
        return self.card.get("auto_archive_days", 7)

    @property
    def completed_visible_days(self) -> int:
        return self.card.get("completed_visible_days", 3)

    @property
    def card_types(self) -> dict[str, dict]:
        return self.card.get("types", {})

    @property
    def allowed_parents(self) -> dict[str, set[str]]:
        return {
            ct: set(info.get("allowed_parents", []))
            for ct, info in self.card_types.items()
        }

    @property
    def independent_types(self) -> set[str]:
        return {
            ct for ct, info in self.card_types.items()
            if info.get("can_be_independent", True)
        }

    @property
    def card_type_display_order(self) -> dict[str, int]:
        return {
            ct: info.get("display_order", 99)
            for ct, info in self.card_types.items()
        }

    @property
    def archive_interval_hours(self) -> int:
        return self.scheduler.get("archive_interval_hours", 1)

    @property
    def hr(self) -> dict[str, Any]:
        return self._data.get("hr", {})

    @property
    def hr_excel_path(self) -> str:
        return self.hr.get("excel_path", "data/auth_member/hr_info.xlsx")

    @property
    def hr_default_password(self) -> str:
        return self.hr.get("default_password", "1234!")

    @property
    def sidebar(self) -> dict[str, Any]:
        return self._data.get("sidebar", {})

    @property
    def recent_projects_count(self) -> int:
        return self.sidebar.get("recent_projects_count", 5)


@lru_cache()
def get_settings() -> Settings:
    return Settings()


@lru_cache()
def get_app_config() -> AppConfig:
    return AppConfig()
