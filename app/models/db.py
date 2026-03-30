"""DuckDB integration points for ClusterSage.

DuckDB is used as the local analytical store for intermediate and derived
artifacts. It supports inspection and reproducible analysis without requiring
distributed infrastructure for the MVP.
"""

from pathlib import Path
from typing import Iterable

import duckdb

from app.models.schemas import LogRecord


CREATE_LOG_RECORDS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS log_records (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMP,
    source TEXT,
    host TEXT,
    job_id TEXT,
    severity TEXT,
    component TEXT,
    raw_text TEXT NOT NULL,
    normalized_text TEXT,
    file_path TEXT NOT NULL,
    line_number INTEGER NOT NULL
)
"""

INSERT_LOG_RECORD_SQL = """
INSERT OR REPLACE INTO log_records (
    id,
    timestamp,
    source,
    host,
    job_id,
    severity,
    component,
    raw_text,
    normalized_text,
    file_path,
    line_number
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def connect(database_path: Path) -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection for local analysis."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(database_path))


def initialize_database(connection: duckdb.DuckDBPyConnection) -> None:
    """Create the minimal tables required for the ingest pipeline."""
    connection.execute(CREATE_LOG_RECORDS_TABLE_SQL)


def insert_log_records(
    connection: duckdb.DuckDBPyConnection,
    records: Iterable[LogRecord],
) -> int:
    """Persist processed log records and return the number written."""
    rows = [
        (
            record.id,
            record.timestamp,
            record.source,
            record.host,
            record.job_id,
            record.severity,
            record.component,
            record.raw_text,
            record.normalized_text,
            str(record.file_path),
            record.line_number,
        )
        for record in records
    ]
    if not rows:
        return 0

    connection.executemany(INSERT_LOG_RECORD_SQL, rows)
    return len(rows)
