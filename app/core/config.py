"""Configuration loading for ClusterSage.

This module centralizes environment-driven settings and will later own YAML
merging, path resolution, and validation for the local log-triage pipeline.
Configuration should remain readable because the project is intended to be
inspected and tuned by engineers and collaborators.
"""

from functools import lru_cache
from pathlib import Path

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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings object for process-wide reuse."""
    return Settings()
