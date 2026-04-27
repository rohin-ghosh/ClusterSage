"""Benchmark runner for normalization and grouping baselines."""

from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from app.eval.baselines import available_methods
from app.eval.datasets import EvalDataset, load_dataset
from app.eval.metrics import build_error_analysis, compute_grouping_metrics, compute_normalization_metrics
from app.eval.perturb import perturb_records
from app.eval.reports import write_benchmark_reports
from app.normalize import TextNormalizer


def run_benchmark(
    dataset_path: Path,
    normalizer: TextNormalizer,
    mode: str = "auto",
    report_dir: Path | None = None,
    max_examples: int = 5,
    perturb: bool = False,
    seed: int = 7,
) -> dict[str, Any]:
    """Run the benchmark pipeline and optionally write reports to disk."""
    dataset = load_dataset(dataset_path, mode=mode)
    normalized_records = normalize_dataset(dataset, normalizer, perturb=perturb, seed=seed)
    normalization_metrics = compute_normalization_metrics(normalized_records, max_examples=max_examples)

    method_results: list[dict[str, Any]] = []
    for method_name, method_fn in available_methods().items():
        predictions = [prediction.model_dump() for prediction in method_fn(normalized_records)]
        metrics = compute_grouping_metrics(normalized_records, predictions)
        error_analysis = build_error_analysis(normalized_records, predictions, max_examples=max_examples)
        method_results.append(
            {
                "method": method_name,
                "metrics": metrics,
                "error_analysis": error_analysis,
                "predictions": predictions,
            }
        )

    result = {
        "run_id": build_run_id(dataset.name),
        "dataset": {
            "name": dataset.name,
            "dataset_type": dataset.dataset_type,
            "source_path": str(dataset.source_path),
            "record_count": len(dataset.records),
            "perturbed": perturb,
        },
        "normalization": normalization_metrics,
        "methods": method_results,
    }
    if report_dir is not None:
        result["report_paths"] = {
            key: str(value)
            for key, value in write_benchmark_reports(result, report_dir=report_dir, run_id=result["run_id"]).items()
        }
    return result


def normalize_dataset(
    dataset: EvalDataset,
    normalizer: TextNormalizer,
    perturb: bool = False,
    seed: int = 7,
) -> list[dict[str, Any]]:
    """Normalize benchmark records and capture per-line traces."""
    raw_texts = [record.raw_text for record in dataset.records]
    if perturb:
        raw_texts = perturb_records(raw_texts, seed=seed)

    normalized_records: list[dict[str, Any]] = []
    for record, raw_text in zip(dataset.records, raw_texts, strict=True):
        normalized_text, trace = normalizer.normalize_with_trace(raw_text)
        normalized_records.append(
            {
                "index": record.index,
                "raw_text": raw_text,
                "normalized_text": normalized_text,
                "normalization_trace": trace,
                "expected_template": record.expected_template,
                "expected_group_id": record.expected_group_id,
                "source": record.source,
                "host": record.host,
                "file_path": str(record.file_path) if record.file_path else None,
                "line_number": record.line_number,
            }
        )
    return normalized_records


def build_run_id(dataset_name: str) -> str:
    """Build a stable, readable benchmark run identifier."""
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    safe_name = dataset_name.replace(" ", "_")
    return f"{timestamp}_{safe_name}"
