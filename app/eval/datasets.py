"""Dataset loaders for lightweight benchmark and evaluation runs.

The evaluation layer supports two small, inspectable dataset formats:

1. a local labeled benchmark format with `logs.txt` and `labels.json`
2. synthetic sample-run datasets with an optional `benchmark_manifest.json`
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from app.ingest import load_log_records


class EvalRecord(BaseModel):
    """A single benchmarkable log line with optional expected labels."""

    index: int = Field(ge=1)
    raw_text: str
    source: str | None = None
    host: str | None = None
    file_path: Path | None = None
    line_number: int | None = None
    expected_template: str | None = None
    expected_group_id: str | None = None


class EvalDataset(BaseModel):
    """A loaded benchmark dataset."""

    name: str
    dataset_type: str
    source_path: Path
    records: list[EvalRecord]


def load_dataset(dataset_path: Path, mode: str = "auto") -> EvalDataset:
    """Load a benchmark dataset from a local labeled or synthetic directory."""
    resolved_mode = resolve_dataset_mode(dataset_path, mode)
    if resolved_mode == "local":
        return load_local_dataset(dataset_path)
    if resolved_mode == "synthetic":
        return load_synthetic_dataset(dataset_path)
    raise ValueError(f"Unsupported dataset mode: {resolved_mode}")


def resolve_dataset_mode(dataset_path: Path, mode: str) -> str:
    """Resolve dataset mode from the path when `auto` is requested."""
    if mode != "auto":
        return mode
    if (dataset_path / "logs.txt").exists() and (dataset_path / "labels.json").exists():
        return "local"
    return "synthetic"


def load_local_dataset(dataset_path: Path) -> EvalDataset:
    """Load the simple local benchmark format from `logs.txt` and `labels.json`."""
    logs_path = dataset_path / "logs.txt"
    labels_path = dataset_path / "labels.json"

    lines = [
        line.rstrip("\n")
        for line in logs_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    label_lookup = {
        int(item["line_index"]): item
        for item in labels.get("records", [])
    }

    records: list[EvalRecord] = []
    for index, raw_text in enumerate(lines, start=1):
        label = label_lookup.get(index, {})
        records.append(
            EvalRecord(
                index=index,
                raw_text=raw_text,
                expected_template=label.get("expected_template"),
                expected_group_id=label.get("expected_group_id"),
            )
        )

    return EvalDataset(
        name=labels.get("name", dataset_path.name),
        dataset_type="local",
        source_path=dataset_path,
        records=records,
    )


def load_synthetic_dataset(dataset_path: Path) -> EvalDataset:
    """Load synthetic sample logs and optional expected labels from a manifest."""
    manifest_path = dataset_path / "benchmark_manifest.json"
    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    label_lookup = {
        (item["file"], int(item["line_number"])): item
        for item in manifest.get("records", [])
    }

    _, log_records = load_log_records(root_path=dataset_path)
    records: list[EvalRecord] = []
    for index, record in enumerate(log_records, start=1):
        relative_path = record.file_path.relative_to(dataset_path)
        label = label_lookup.get((str(relative_path), record.line_number), {})
        records.append(
            EvalRecord(
                index=index,
                raw_text=record.raw_text,
                source=record.source,
                host=record.host,
                file_path=record.file_path,
                line_number=record.line_number,
                expected_template=label.get("expected_template"),
                expected_group_id=label.get("expected_group_id"),
            )
        )

    return EvalDataset(
        name=manifest.get("name", dataset_path.name),
        dataset_type="synthetic",
        source_path=dataset_path,
        records=records,
    )
