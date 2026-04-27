"""Pydantic schemas shared by the current ClusterSage pipeline."""

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field


class LogRecord(BaseModel):
    """One parsed and optionally normalized log line."""

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


class IngestSummary(BaseModel):
    """Summary of a completed ingest run."""

    files_processed: int = Field(ge=0)
    log_lines_ingested: int = Field(ge=0)
    records_written: int = Field(ge=0)
    database_path: Path
