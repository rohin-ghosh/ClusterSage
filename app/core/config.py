"""Configuration loading for ClusterSage.

This module centralizes environment-driven settings and will later own YAML
merging, path resolution, and validation for the local log-triage pipeline.
Configuration should remain readable because the project is intended to be
inspected and tuned by engineers and collaborators.
"""

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings resolved from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="CLUSTERSAGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="ClusterSage")
    env: str = Field(default="development")
    duckdb_path: Path = Field(default=Path("data/processed/clustersage.duckdb"))
    config_path: Path = Field(default=Path("configs/default.yaml"))

    def resolved_path(self, path: Path) -> Path:
        """Resolve a project-relative path against the current working tree."""
        return path if path.is_absolute() else Path.cwd() / path

    @property
    def resolved_duckdb_path(self) -> Path:
        """Return the fully resolved DuckDB database path."""
        return self.resolved_path(self.duckdb_path)

    def load_yaml_config(self, path: Path | None = None) -> dict:
        """Load a YAML configuration file and return its contents."""
        target_path = self.resolved_path(path or self.config_path)
        with target_path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings object for process-wide reuse."""
    return Settings()
