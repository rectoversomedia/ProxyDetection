"""Configuration management using Pydantic Settings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Lazy import to avoid circular dependency
logger = None


def _get_logger():
    global logger
    if logger is None:
        from .logger import get_logger
        logger = get_logger(__name__)
    return logger


class Settings(BaseSettings):
    """Application settings loaded from environment variables and config files."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="allow",
    )

    # Proxy Providers
    dat_impulse_api_key: Optional[str] = Field(None, alias="DAT_IMPULSE_API_KEY")
    decodo_api_key: Optional[str] = Field(None, alias="DECODO_API_KEY")
    proxy_file_path: Optional[str] = Field(None, alias="PROXY_FILE_PATH")

    # Browser Settings
    browser_type: str = Field("camoufox", alias="BROWSER_TYPE")
    camoufox_path: Optional[str] = Field(None, alias="CAMOUFOX_PATH")
    playwright_browsers_path: Optional[str] = Field(None, alias="PLAYWRIGHT_BROWSERS_PATH")
    browser_headless: bool = Field(False, alias="BROWSER_HEADLESS")

    # Submission Settings
    default_delay: int = Field(5, alias="DEFAULT_DELAY")
    max_parallel: int = Field(3, alias="MAX_PARALLEL")
    max_retries: int = Field(3, alias="MAX_RETRIES")

    # Database
    database_path: str = Field("data/proxy_detection.db", alias="DATABASE_PATH")

    # Logging
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_file: str = Field("logs/app.log", alias="LOG_FILE")

    # Session
    session_timeout: int = Field(300, alias="SESSION_TIMEOUT")
    profile_dir: str = Field("configs/profiles", alias="PROFILE_DIR")

    # Screenshot
    save_error_screenshots: bool = Field(True, alias="SAVE_ERROR_SCREENSHOTS")
    screenshot_dir: str = Field("logs/screenshots", alias="SCREENSHOT_DIR")

    @field_validator("database_path", mode="before")
    @classmethod
    def resolve_database_path(cls, v: str) -> str:
        """Resolve relative database path to absolute path."""
        if v and not Path(v).is_absolute():
            # Make relative to project root
            return str(Path.cwd() / v)
        return v

    @field_validator("profile_dir", mode="before")
    @classmethod
    def resolve_profile_dir(cls, v: str) -> str:
        """Resolve relative profile directory to absolute path."""
        if v and not Path(v).is_absolute():
            return str(Path.cwd() / v)
        return v

    @field_validator("screenshot_dir", mode="before")
    @classmethod
    def resolve_screenshot_dir(cls, v: str) -> str:
        """Resolve relative screenshot directory to absolute path."""
        if v and not Path(v).is_absolute():
            return str(Path.cwd() / v)
        return v

    def get_proxy_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific proxy provider."""
        configs_dir = Path("configs")
        provider_config_path = configs_dir / "providers" / f"{provider}.json"

        if provider_config_path.exists():
            with open(provider_config_path) as f:
                return json.load(f)
        return {}

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            Path(self.database_path).parent,
            Path(self.log_file).parent,
            Path(self.screenshot_dir),
            Path(self.profile_dir),
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get cached settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_directories()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings()
    _settings.ensure_directories()
    return _settings
