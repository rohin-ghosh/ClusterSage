"""Line parsing helpers.

Parsing should remain conservative in the MVP. The goal is to recover useful
structure where possible without forcing every line into a brittle schema or
discarding the original text when parsing is uncertain.
"""

from datetime import datetime, timezone
import re

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
    """Infer a lightweight component label from a log line when obvious."""
    match = BRACKET_COMPONENT_PATTERN.search(text)
    return match.group(1) if match else None
