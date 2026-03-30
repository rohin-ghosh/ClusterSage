"""Tests for recursive ingest, metadata inference, and timestamp behavior."""

from pathlib import Path

from app.ingest.loader import discover_log_files, load_log_records
from app.ingest.metadata import infer_source_and_host


def test_recursive_file_loading(tmp_path: Path) -> None:
    """Loader should find nested `.log` and `.txt` files only."""
    nested = tmp_path / "nested"
    nested.mkdir()
    (tmp_path / "trainer_node03.log").write_text("line one\n", encoding="utf-8")
    (nested / "scheduler_node01.txt").write_text("line two\n", encoding="utf-8")
    (nested / "ignore.json").write_text("{}", encoding="utf-8")

    files = discover_log_files(tmp_path)

    assert [path.name for path in files] == ["scheduler_node01.txt", "trainer_node03.log"]


def test_metadata_inference_from_filename() -> None:
    """Source and host should be inferred from structured filenames."""
    source, host = infer_source_and_host(Path("trainer_node03.log"))

    assert source == "trainer"
    assert host == "node03"


def test_timestamp_fallback_behavior(tmp_path: Path) -> None:
    """Lines without a leading timestamp should still be preserved."""
    log_file = tmp_path / "worker_node09.log"
    log_file.write_text(
        "2026-03-30 10:15:00 INFO startup complete\nplain message without timestamp\n",
        encoding="utf-8",
    )

    _, records = load_log_records(tmp_path, job_id="run_042")

    assert len(records) == 2
    assert records[0].timestamp is not None
    assert records[1].timestamp is None
    assert records[1].raw_text == "plain message without timestamp"
