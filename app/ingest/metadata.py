"""Metadata extraction helpers.

This module will infer run-level and file-level metadata such as host names,
component labels, job identifiers, and collection context when available. That
metadata makes later clustering and reporting more useful without requiring a
heavy schema at ingest time.
"""

from pathlib import Path
import re

FILENAME_METADATA_PATTERN = re.compile(
    r"^(?P<source>[a-zA-Z][a-zA-Z0-9-]*?)(?:[_-](?P<host>[a-zA-Z]+[a-zA-Z0-9-]*\d+))?$"
)


def infer_source_and_host(path: Path) -> tuple[str | None, str | None]:
    """Infer `source` and `host` from a log filename when possible."""
    match = FILENAME_METADATA_PATTERN.match(path.stem)
    if not match:
        return None, None

    source = match.group("source")
    host = match.group("host")
    return source, host
