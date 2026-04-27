"""Log file discovery and line parsing for ClusterSage.

This package is intentionally compact: it discovers `.log` and `.txt` files,
infers a small amount of metadata, parses obvious timestamps, and returns
`LogRecord` objects for normalization and storage.
"""

from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
import re

from app.schemas import LogRecord

SUPPORTED_LOG_SUFFIXES = {".log", ".txt"}

FILENAME_METADATA_PATTERN = re.compile(
    r"^(?P<source>[a-zA-Z][a-zA-Z0-9-]*?)(?:[_-](?P<host>[a-zA-Z]+[a-zA-Z0-9-]*\d+))?$"
)
TIMESTAMP_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"^(?P<value>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)"),
        "iso_zulu",
    ),
    (
        re.compile(r"^(?P<value>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})"),
        "%Y-%m-%d %H:%M:%S,%f",
    ),
    (
        re.compile(r"^(?P<value>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"),
        "%Y-%m-%d %H:%M:%S",
    ),
    (
        re.compile(r"^(?P<value>[A-Z][a-z]{2} \d{2} \d{2}:\d{2}:\d{2})"),
        "syslog",
    ),
)
SEVERITY_PATTERN = re.compile(r"\b(DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL)\b")
BRACKET_COMPONENT_PATTERN = re.compile(r"\[([A-Za-z0-9_.-]+)\]")


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
        records.extend(iter_file_records(file_path, source=source, host=host, job_id=job_id))

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
                line_number=line_number,
            )


def infer_source_and_host(path: Path) -> tuple[str | None, str | None]:
    """Infer `source` and `host` from simple filenames like `trainer_node03.log`."""
    match = FILENAME_METADATA_PATTERN.match(path.stem)
    if not match:
        return None, None

    return match.group("source"), match.group("host")


def parse_timestamp(text: str) -> datetime | None:
    """Parse a timestamp from the start of a log line when present."""
    for pattern, parser in TIMESTAMP_PATTERNS:
        match = pattern.match(text)
        if not match:
            continue

        value = match.group("value")
        if parser == "iso_zulu":
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parser == "syslog":
            parsed = datetime.strptime(value, "%b %d %H:%M:%S")
            return parsed.replace(year=datetime.now(timezone.utc).year)
        return datetime.strptime(value, parser)
    return None


def infer_severity(text: str) -> str | None:
    """Infer a coarse severity token from a log line."""
    match = SEVERITY_PATTERN.search(text)
    return match.group(1) if match else None


def infer_component(text: str) -> str | None:
    """Infer a bracketed component label from a log line."""
    match = BRACKET_COMPONENT_PATTERN.search(text)
    return match.group(1) if match else None
