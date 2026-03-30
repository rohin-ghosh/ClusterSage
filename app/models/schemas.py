"""Pydantic schemas for API payloads and pipeline records.

These models define the stable shapes exchanged between ingestion,
normalization, template extraction, scoring, incident grouping, and reporting.
They are part of the repository's contract: each stage should be able to evolve
without changing the meaning of the data it hands off.
"""

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field


class LogRecord(BaseModel):
    """Canonical log record shape preserved across early pipeline stages.

    The record keeps raw text and lightweight metadata together so downstream
    steps can improve legibility without losing access to the source evidence.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime | None = None
    source: str | None = None
    host: str | None = None
    job_id: str | None = None
    severity: str | None = None
    component: str | None = None
    line_number: int = Field(ge=1)
    raw_text: str
    normalized_text: str | None = None
    file_path: Path
    source_path: Path
    
    
class IngestSummary(BaseModel):
    """Summary of a completed ingest run."""

    files_processed: int = Field(ge=0)
    log_lines_ingested: int = Field(ge=0)
    records_written: int = Field(ge=0)
    database_path: Path


class HealthResponse(BaseModel):
    """Minimal API response schema."""

    status: str
    service: str
