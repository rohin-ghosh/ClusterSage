"""Pydantic schemas for API payloads and pipeline records.

These models define the stable shapes exchanged between ingestion,
normalization, template extraction, scoring, incident grouping, and reporting.
They are part of the repository's contract: each stage should be able to evolve
without changing the meaning of the data it hands off.
"""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class LogRecord(BaseModel):
    """Canonical log record shape preserved across early pipeline stages.

    The record keeps raw text and lightweight metadata together so downstream
    steps can improve legibility without losing access to the source evidence.
    """

    source_path: Path
    line_number: int = Field(ge=1)
    raw_text: str
    timestamp: datetime | None = None
    component: str | None = None
    host: str | None = None


class HealthResponse(BaseModel):
    """Minimal API response schema."""

    status: str
    service: str
