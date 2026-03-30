"""Raw log loading utilities.

This stage is responsible for turning a run directory into a set of readable
inputs for the rest of the pipeline. It should enumerate files, read supported
log inputs, and preserve source lineage so later reports can point back to the
original evidence.
"""

from collections.abc import Iterable
from pathlib import Path

from app.ingest.metadata import infer_source_and_host
from app.ingest.parsers import infer_component, infer_severity, parse_timestamp
from app.models.schemas import LogRecord

SUPPORTED_LOG_SUFFIXES = {".log", ".txt"}


def discover_log_files(root_path: Path) -> list[Path]:
    """Recursively discover supported log files under a directory."""
    if root_path.is_file():
        return [root_path] if root_path.suffix.lower() in SUPPORTED_LOG_SUFFIXES else []

    return sorted(
        path
        for path in root_path.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_LOG_SUFFIXES
    )


def load_log_records(root_path: Path, job_id: str | None = None) -> tuple[list[Path], list[LogRecord]]:
    """Load supported log files into structured records."""
    files = discover_log_files(root_path)
    records: list[LogRecord] = []

    for file_path in files:
        source, host = infer_source_and_host(file_path)
        records.extend(iter_file_records(file_path=file_path, source=source, host=host, job_id=job_id))

    return files, records


def iter_file_records(
    file_path: Path,
    source: str | None,
    host: str | None,
    job_id: str | None,
) -> Iterable[LogRecord]:
    """Yield structured records from a single log file."""
    with file_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            raw_text = raw_line.strip()
            if not raw_text:
                continue

            yield LogRecord(
                timestamp=parse_timestamp(raw_text),
                source=source,
                host=host,
                job_id=job_id,
                severity=infer_severity(raw_text),
                component=infer_component(raw_text),
                raw_text=raw_text,
                file_path=file_path,
                source_path=file_path,
                line_number=line_number,
            )
