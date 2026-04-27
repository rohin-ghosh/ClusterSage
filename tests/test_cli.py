"""CLI integration tests for the ingest command."""

from pathlib import Path

from typer.testing import CliRunner

from app.cli import app

runner = CliRunner()


def test_ingest_command_runs_end_to_end(tmp_path: Path, monkeypatch) -> None:
    """CLI ingest should normalize and persist records with a concise summary."""
    sample_dir = tmp_path / "data" / "raw" / "sample_run"
    sample_dir.mkdir(parents=True)
    (sample_dir / "trainer_node03.log").write_text(
        "2026-03-30 10:15:00 ERROR [rdma] timeout after 3000 ms from 10.0.0.5\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "default.yaml").write_text(
        "\n".join(
            [
                "app_name: ClusterSage",
                "environment: test",
                "duckdb_path: data/processed/clustersage.duckdb",
                "normalization_config: configs/normalization.yaml",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "configs" / "normalization.yaml").write_text(
        "\n".join(
            [
                "rules:",
                "  - name: duration",
                "    enabled: true",
                '    pattern: "\\\\b\\\\d+\\\\s?ms\\\\b"',
                '    replacement: "<DURATION>"',
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["ingest", str(sample_dir), "--job-id", "run_042"])

    assert result.exit_code == 0
    assert "Files processed: 1" in result.stdout
    assert "Log lines ingested: 1" in result.stdout
    assert "Normalized records written: 1" in result.stdout


def test_benchmark_command_runs_end_to_end(tmp_path: Path, monkeypatch) -> None:
    """CLI benchmark should run and write reports for a labeled dataset."""
    dataset_dir = tmp_path / "data" / "benchmarks" / "sample_parser_eval"
    dataset_dir.mkdir(parents=True)
    (dataset_dir / "logs.txt").write_text(
        "ERROR [rdma] timeout after 3000 ms from 10.0.0.5\n",
        encoding="utf-8",
    )
    (dataset_dir / "labels.json").write_text(
        (
            '{"name":"sample_parser_eval","records":['
            '{"line_index":1,"expected_group_id":"timeout","expected_template":"ERROR [rdma] timeout after <DURATION> from <IP>"}'
            "]} "
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "default.yaml").write_text(
        "\n".join(
            [
                "app_name: ClusterSage",
                "environment: test",
                "duckdb_path: data/processed/clustersage.duckdb",
                "normalization_config: configs/normalization.yaml",
                "eval_config: configs/eval.yaml",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "configs" / "normalization.yaml").write_text(
        "\n".join(
            [
                "rules:",
                "  - name: ip_address",
                "    enabled: true",
                '    pattern: "\\\\b(?:\\\\d{1,3}\\\\.){3}\\\\d{1,3}\\\\b"',
                '    replacement: "<IP>"',
                "  - name: duration",
                "    enabled: true",
                '    pattern: "\\\\b\\\\d+\\\\s?ms\\\\b"',
                '    replacement: "<DURATION>"',
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "configs" / "eval.yaml").write_text(
        "\n".join(
            [
                "report_dir: data/reports/benchmarks",
                "max_examples: 3",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["benchmark", str(dataset_dir), "--mode", "local"])

    assert result.exit_code == 0
    assert "Dataset: sample_parser_eval" in result.stdout
    assert "Method: normalized_identity" in result.stdout
    assert "JSON report:" in result.stdout
