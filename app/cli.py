"""Typer CLI entrypoints for local ClusterSage workflows.

The CLI is expected to be the primary interface during early development:
loading runs, inspecting intermediate artifacts, and rendering reports from a
single machine without extra infrastructure.
"""

from pathlib import Path

import typer

from app.core.config import get_settings
from app.ingest.loader import load_log_records
from app.models.db import connect, initialize_database, insert_log_records
from app.models.schemas import IngestSummary, LogRecord
from app.normalize.canonicalize import TextNormalizer

app = typer.Typer(help="ClusterSage command line interface.")


@app.command()
def version() -> None:
    """Print the current application version."""
    typer.echo("ClusterSage v0.1.0")


@app.command()
def show_config() -> None:
    """Display the resolved application settings."""
    settings = get_settings()
    typer.echo(settings.model_dump_json(indent=2))


@app.command()
def ingest(
    path: Path,
    job_id: str | None = typer.Option(default=None, help="Optional job or run identifier."),
) -> None:
    """Recursively ingest logs, normalize them, and persist them to DuckDB."""
    settings = get_settings()
    normalization_config = settings.load_yaml_config().get("normalization_config", "configs/normalization.yaml")
    normalizer = TextNormalizer.from_yaml(settings.resolved_path(Path(normalization_config)))

    files, raw_records = load_log_records(path=path, job_id=job_id) if False else load_log_records(root_path=path, job_id=job_id)
    records = [
        LogRecord(**record.model_dump(), normalized_text=normalizer.normalize(record.raw_text))
        for record in raw_records
    ]

    database_path = settings.resolved_duckdb_path
    with connect(database_path) as connection:
        initialize_database(connection)
        written = insert_log_records(connection, records)

    summary = IngestSummary(
        files_processed=len(files),
        log_lines_ingested=len(raw_records),
        records_written=written,
        database_path=database_path,
    )
    typer.echo(f"Files processed: {summary.files_processed}")
    typer.echo(f"Log lines ingested: {summary.log_lines_ingested}")
    typer.echo(f"Normalized records written: {summary.records_written}")
    typer.echo(f"Database path: {summary.database_path}")


if __name__ == "__main__":
    app()
