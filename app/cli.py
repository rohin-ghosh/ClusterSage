"""Typer CLI entrypoints for local ClusterSage workflows.

The CLI is expected to be the primary interface during early development:
loading runs, inspecting intermediate artifacts, and rendering reports from a
single machine without extra infrastructure.
"""

from pathlib import Path

import typer

from app.config import get_settings
from app.eval.benchmark import run_benchmark
from app.ingest import load_log_records
from app.normalize import TextNormalizer
from app.schemas import IngestSummary
from app.storage import connect, initialize_database, insert_log_records

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
    normalization_config = settings.load_yaml_config().get(
        "normalization_config",
        "configs/normalization.yaml",
    )
    normalizer = TextNormalizer.from_yaml(settings.resolved_path(Path(normalization_config)))

    files, raw_records = load_log_records(root_path=path, job_id=job_id)
    records = [
        record.model_copy(update={"normalized_text": normalizer.normalize(record.raw_text)})
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


@app.command()
def benchmark(
    dataset_path: Path,
    mode: str = typer.Option("auto", help="Dataset mode: auto, local, or synthetic."),
    perturb: bool = typer.Option(False, help="Benchmark perturbed variants of the dataset."),
    seed: int = typer.Option(7, help="Seed for deterministic perturbation."),
) -> None:
    """Run the lightweight evaluation harness and write benchmark reports."""
    settings = get_settings()
    project_config = settings.load_yaml_config()
    normalization_config = project_config.get("normalization_config", "configs/normalization.yaml")
    eval_config_path = Path(project_config.get("eval_config", "configs/eval.yaml"))
    eval_config = settings.load_yaml_config(eval_config_path)

    normalizer = TextNormalizer.from_yaml(settings.resolved_path(Path(normalization_config)))
    report_dir = settings.resolved_path(Path(eval_config.get("report_dir", "data/reports/benchmarks")))
    result = run_benchmark(
        dataset_path=dataset_path,
        normalizer=normalizer,
        mode=mode,
        report_dir=report_dir,
        max_examples=int(eval_config.get("max_examples", 5)),
        perturb=perturb,
        seed=seed,
    )

    typer.echo(f"Dataset: {result['dataset']['name']}")
    typer.echo(f"Dataset type: {result['dataset']['dataset_type']}")
    typer.echo(f"Record count: {result['dataset']['record_count']}")
    typer.echo(
        "Normalization changed: "
        f"{result['normalization']['changed_lines']} / {result['normalization']['total_lines']} "
        f"({result['normalization']['percent_changed']}%)"
    )
    for method in result["methods"]:
        metrics = method["metrics"]
        typer.echo(f"Method: {method['method']}")
        typer.echo(f"  predicted templates: {metrics['predicted_template_count']}")
        typer.echo(f"  expected templates: {metrics['expected_template_count']}")
        typer.echo(f"  exact template match rate: {metrics['exact_template_match_rate']}")
        typer.echo(f"  grouping pair accuracy: {metrics['grouping_pair_accuracy']}")
        typer.echo(f"  over-splitting pairs: {metrics['over_splitting_pairs']}")
        typer.echo(f"  over-merging pairs: {metrics['over_merging_pairs']}")
    typer.echo(f"JSON report: {result['report_paths']['json']}")
    typer.echo(f"Markdown report: {result['report_paths']['markdown']}")


if __name__ == "__main__":
    app()
