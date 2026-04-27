"""Storage sanity tests for the ingest layer."""

from datetime import datetime
from pathlib import Path

from app.schemas import LogRecord
from app.storage import connect, initialize_database, insert_log_records


def test_duckdb_write_read_sanity(tmp_path: Path) -> None:
    """Processed log records should round-trip through DuckDB."""
    database_path = tmp_path / "clustersage.duckdb"
    record = LogRecord(
        timestamp=datetime(2026, 3, 30, 10, 15, 0),
        source="trainer",
        host="node03",
        job_id="run_042",
        severity="ERROR",
        component="rdma",
        raw_text="2026-03-30 10:15:00 ERROR [rdma] link timeout on node03",
        normalized_text="2026-03-30 <INT>:<INT>:<INT> ERROR [rdma] link timeout on node03",
        file_path=tmp_path / "trainer_node03.log",
        line_number=1,
    )

    with connect(database_path) as connection:
        initialize_database(connection)
        written = insert_log_records(connection, [record])
        stored = connection.execute(
            "SELECT source, host, job_id, raw_text, normalized_text FROM log_records"
        ).fetchone()

    assert written == 1
    assert stored == (
        "trainer",
        "node03",
        "run_042",
        "2026-03-30 10:15:00 ERROR [rdma] link timeout on node03",
        "2026-03-30 <INT>:<INT>:<INT> ERROR [rdma] link timeout on node03",
    )
