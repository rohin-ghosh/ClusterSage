"""Typer CLI entrypoints for local ClusterSage workflows.

The CLI is expected to be the primary interface during early development:
loading runs, inspecting intermediate artifacts, and rendering reports from a
single machine without extra infrastructure.
"""

from pathlib import Path

import typer

from app.core.config import get_settings

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
def ingest(path: Path) -> None:
    """Placeholder command for future batch log loading."""
    typer.echo(f"Ingest scaffold ready. Target path: {path}")


if __name__ == "__main__":
    app()
