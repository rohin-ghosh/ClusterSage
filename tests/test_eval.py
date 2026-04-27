"""Tests for the lightweight benchmark and evaluation layer."""

from pathlib import Path

from app.eval.baselines import normalized_identity, token_pattern_grouping
from app.eval.benchmark import run_benchmark
from app.eval.datasets import load_dataset
from app.eval.metrics import compute_grouping_metrics
from app.eval.perturb import perturb_text
from app.normalize import TextNormalizer


def test_load_local_benchmark_dataset(tmp_path: Path) -> None:
    """Local labeled benchmark datasets should load from logs and labels."""
    dataset_dir = tmp_path / "sample_eval"
    dataset_dir.mkdir()
    (dataset_dir / "logs.txt").write_text("alpha\nbeta\n", encoding="utf-8")
    (dataset_dir / "labels.json").write_text(
        '{"name":"tiny_eval","records":[{"line_index":1,"expected_group_id":"g1"}]}',
        encoding="utf-8",
    )

    dataset = load_dataset(dataset_dir, mode="local")

    assert dataset.name == "tiny_eval"
    assert len(dataset.records) == 2
    assert dataset.records[0].expected_group_id == "g1"


def test_baseline_grouping_methods() -> None:
    """Baseline grouping methods should produce deterministic groupings."""
    records = [
        {"index": 1, "normalized_text": "INFO [scheduler] assigned job <INT> to node03"},
        {"index": 2, "normalized_text": "INFO [scheduler] assigned job <INT> to node07"},
    ]

    identity_predictions = normalized_identity(records)
    pattern_predictions = token_pattern_grouping(records)

    assert identity_predictions[0].predicted_group_id != identity_predictions[1].predicted_group_id
    assert pattern_predictions[0].predicted_group_id == pattern_predictions[1].predicted_group_id


def test_compute_metrics_on_tiny_labeled_sample() -> None:
    """Grouping metrics should detect false splits in a tiny sample."""
    normalized_records = [
        {"index": 1, "expected_group_id": "timeout", "expected_template": "timeout", "raw_text": "a"},
        {"index": 2, "expected_group_id": "timeout", "expected_template": "timeout", "raw_text": "b"},
    ]
    predictions = [
        {"index": 1, "predicted_group_id": "group_001", "predicted_template": "timeout"},
        {"index": 2, "predicted_group_id": "group_002", "predicted_template": "timeout"},
    ]

    metrics = compute_grouping_metrics(normalized_records, predictions)

    assert metrics["exact_template_match_rate"] == 1.0
    assert metrics["grouping_pair_accuracy"] == 0.0
    assert metrics["over_splitting_pairs"] == 1


def test_perturbation_utility_behavior() -> None:
    """Perturbation should change unstable tokens while remaining deterministic."""
    text = "WARN request_id=abc123def456ghi789 from 10.0.0.5 after 3000 ms"

    first = perturb_text(text, seed=11)
    second = perturb_text(text, seed=11)

    assert first == second
    assert first != text


def test_benchmark_report_generation_sanity(tmp_path: Path) -> None:
    """Benchmark runs should produce JSON and Markdown reports."""
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    (dataset_dir / "logs.txt").write_text(
        "ERROR [rdma] link timeout after 3000 ms to 10.0.0.5\n"
        "ERROR [rdma] link timeout after 4500 ms to 10.0.0.9\n",
        encoding="utf-8",
    )
    (dataset_dir / "labels.json").write_text(
        (
            '{"name":"tiny_parser_eval","records":['
            '{"line_index":1,"expected_group_id":"timeout","expected_template":"ERROR [rdma] link timeout after <DURATION> to <IP>"},'
            '{"line_index":2,"expected_group_id":"timeout","expected_template":"ERROR [rdma] link timeout after <DURATION> to <IP>"}'
            "]} "
        ),
        encoding="utf-8",
    )
    normalization_config = tmp_path / "normalization.yaml"
    normalization_config.write_text(
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

    result = run_benchmark(
        dataset_path=dataset_dir,
        normalizer=TextNormalizer.from_yaml(normalization_config),
        mode="local",
        report_dir=tmp_path / "reports",
    )

    assert "report_paths" in result
    assert Path(result["report_paths"]["json"]).exists()
    assert Path(result["report_paths"]["markdown"]).exists()
