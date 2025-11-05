"""Application settings and configuration.

This module provides centralized configuration management using
pydantic-settings for environment variables and YAML configuration.
"""

from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file.

    Environment variables take precedence over .env file values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Steel.dev Configuration
    steel_api_key: str = Field(
        ...,
        description="Steel.dev API key for browser automation",
    )

    # Platform API Keys
    github_token: str | None = Field(
        None,
        description="GitHub personal access token",
    )
    twitter_bearer_token: str | None = Field(
        None,
        description="Twitter API v2 bearer token",
    )
    linkedin_access_token: str | None = Field(
        None,
        description="LinkedIn OAuth access token",
    )

    # Database Configuration
    database_url: str = Field(
        "sqlite+aiosqlite:///./fabo.db",
        description="Database connection URL",
    )

    # Application Settings
    log_level: str = Field(
        "INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    environment: str = Field(
        "development",
        description="Application environment (development, production)",
    )

    # Screenshot Storage
    screenshots_path: Path = Field(
        Path("./screenshots"),
        description="Directory to store screenshots",
    )

    # API Server Settings
    api_host: str = Field("0.0.0.0", description="API server host")
    api_port: int = Field(8000, description="API server port")
    api_secret_key: str = Field(
        "change-me-in-production",
        description="Secret key for API authentication",
    )

    # Scheduler Settings
    enable_scheduler: bool = Field(
        True,
        description="Enable automatic milestone checking",
    )
    default_check_interval: int = Field(
        3600,
        description="Default check interval in seconds",
    )

    # Configuration File
    config_file: Path = Field(
        Path("./config.yaml"),
        description="Path to YAML configuration file",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level value."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v_upper

    @field_validator("screenshots_path")
    @classmethod
    def ensure_screenshots_path(cls, v: Path) -> Path:
        """Ensure screenshots directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


class ConfigurationLoader:
    """Loader for YAML configuration files."""

    def __init__(self, config_path: Path):
        """Initialize configuration loader.

        Args:
            config_path: Path to YAML configuration file.
        """
        self.config_path = config_path
        self._config: dict[str, Any] | None = None

    def load(self) -> dict[str, Any]:
        """Load configuration from YAML file.

        Returns:
            Configuration dictionary.
        """
        if self._config is not None:
            return self._config

        if not self.config_path.exists():
            # Return empty config if file doesn't exist
            self._config = {}
            return self._config

        import yaml

        with open(self.config_path, "r") as f:
            self._config = yaml.safe_load(f) or {}

        return self._config

    def get_platform_config(self, platform: str) -> dict[str, Any]:
        """Get configuration for a specific platform.

        Args:
            platform: Platform name (github, twitter, linkedin).

        Returns:
            Platform configuration dictionary.
        """
        config = self.load()
        platforms = config.get("platforms", {})
        return platforms.get(platform, {})

    def get_screenshot_config(self) -> dict[str, Any]:
        """Get screenshot configuration.

        Returns:
            Screenshot configuration dictionary.
        """
        config = self.load()
        return config.get("screenshots", {})

    def get_scheduler_config(self) -> dict[str, Any]:
        """Get scheduler configuration.

        Returns:
            Scheduler configuration dictionary.
        """
        config = self.load()
        return config.get("scheduler", {})


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get application settings singleton.

    Returns:
        Settings instance.
    """
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore
    return _settings


def get_config_loader(settings: Settings | None = None) -> ConfigurationLoader:
    """Get configuration loader.

    Args:
        settings: Settings instance (optional, will use global if not provided).

    Returns:
        ConfigurationLoader instance.
    """
    if settings is None:
        settings = get_settings()
    return ConfigurationLoader(settings.config_file)
