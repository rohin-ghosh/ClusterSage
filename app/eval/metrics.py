"""Simple, inspectable evaluation metrics for normalization and grouping."""

from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Any


def compute_normalization_metrics(
    normalized_records: list[dict],
    max_examples: int = 5,
) -> dict[str, Any]:
    """Compute basic normalization metrics and readable before/after examples."""
    total_lines = len(normalized_records)
    changed_examples: list[dict[str, str]] = []
    placeholder_counts: Counter[str] = Counter()
    changed_lines = 0

    for record in normalized_records:
        trace = record["normalization_trace"]
        if trace["changed"]:
            changed_lines += 1
            if len(changed_examples) < max_examples:
                changed_examples.append(
                    {
                        "raw_text": record["raw_text"],
                        "normalized_text": record["normalized_text"],
                    }
                )
        placeholder_counts.update(trace["replacement_counts"])

    percent_changed = (changed_lines / total_lines * 100.0) if total_lines else 0.0
    return {
        "total_lines": total_lines,
        "changed_lines": changed_lines,
        "percent_changed": round(percent_changed, 2),
        "placeholder_replacement_counts": dict(placeholder_counts),
        "changed_examples": changed_examples,
    }


def compute_grouping_metrics(
    normalized_records: list[dict],
    predictions: list[dict],
) -> dict[str, Any]:
    """Compute grouping and template metrics against optional expected labels."""
    predicted_by_index = {
        prediction["index"]: prediction
        for prediction in predictions
    }
    labeled_records = [
        record
        for record in normalized_records
        if record.get("expected_group_id") is not None or record.get("expected_template") is not None
    ]

    metrics: dict[str, Any] = {
        "predicted_template_count": len({item["predicted_template"] for item in predictions}),
        "expected_template_count": None,
        "exact_template_match_rate": None,
        "grouping_pair_accuracy": None,
        "over_splitting_pairs": None,
        "over_merging_pairs": None,
        "labeled_record_count": len(labeled_records),
    }

    template_labeled = [
        record
        for record in labeled_records
        if record.get("expected_template") is not None
    ]
    if template_labeled:
        exact_matches = sum(
            1
            for record in template_labeled
            if predicted_by_index[record["index"]]["predicted_template"] == record["expected_template"]
        )
        metrics["expected_template_count"] = len({record["expected_template"] for record in template_labeled})
        metrics["exact_template_match_rate"] = round(exact_matches / len(template_labeled), 4)

    group_labeled = [
        record
        for record in labeled_records
        if record.get("expected_group_id") is not None
    ]
    if len(group_labeled) >= 2:
        total_pairs = 0
        correct_pairs = 0
        over_splitting_pairs = 0
        over_merging_pairs = 0

        for left, right in combinations(group_labeled, 2):
            total_pairs += 1
            expected_same = left["expected_group_id"] == right["expected_group_id"]
            predicted_same = (
                predicted_by_index[left["index"]]["predicted_group_id"]
                == predicted_by_index[right["index"]]["predicted_group_id"]
            )
            if expected_same == predicted_same:
                correct_pairs += 1
            elif expected_same and not predicted_same:
                over_splitting_pairs += 1
            elif not expected_same and predicted_same:
                over_merging_pairs += 1

        metrics["grouping_pair_accuracy"] = round(correct_pairs / total_pairs, 4)
        metrics["over_splitting_pairs"] = over_splitting_pairs
        metrics["over_merging_pairs"] = over_merging_pairs

    return metrics


def build_error_analysis(
    normalized_records: list[dict],
    predictions: list[dict],
    max_examples: int = 5,
) -> dict[str, Any]:
    """Build concrete error examples and a small failure-pattern summary."""
    predicted_by_index = {prediction["index"]: prediction for prediction in predictions}
    template_mismatches: list[dict[str, Any]] = []
    false_splits: list[dict[str, Any]] = []
    false_merges: list[dict[str, Any]] = []
    failure_patterns: Counter[str] = Counter()

    for record in normalized_records:
        expected_template = record.get("expected_template")
        if expected_template is None:
            continue
        predicted_template = predicted_by_index[record["index"]]["predicted_template"]
        if expected_template != predicted_template:
            if len(template_mismatches) < max_examples:
                template_mismatches.append(
                    {
                        "index": record["index"],
                        "raw_text": record["raw_text"],
                        "expected_template": expected_template,
                        "predicted_template": predicted_template,
                    }
                )
            failure_patterns[f"template_mismatch::{expected_template} -> {predicted_template}"] += 1

    labeled_group_records = [
        record
        for record in normalized_records
        if record.get("expected_group_id") is not None
    ]
    for left, right in combinations(labeled_group_records, 2):
        expected_same = left["expected_group_id"] == right["expected_group_id"]
        predicted_same = (
            predicted_by_index[left["index"]]["predicted_group_id"]
            == predicted_by_index[right["index"]]["predicted_group_id"]
        )
        if expected_same and not predicted_same and len(false_splits) < max_examples:
            false_splits.append(
                {
                    "left_index": left["index"],
                    "right_index": right["index"],
                    "left_text": left["raw_text"],
                    "right_text": right["raw_text"],
                    "expected_group_id": left["expected_group_id"],
                }
            )
        if not expected_same and predicted_same and len(false_merges) < max_examples:
            false_merges.append(
                {
                    "left_index": left["index"],
                    "right_index": right["index"],
                    "left_text": left["raw_text"],
                    "right_text": right["raw_text"],
                    "predicted_group_id": predicted_by_index[left["index"]]["predicted_group_id"],
                }
            )

    common_failure_patterns = [
        {"pattern": pattern, "count": count}
        for pattern, count in failure_patterns.most_common(max_examples)
    ]
    return {
        "template_mismatches": template_mismatches,
        "false_splits": false_splits,
        "false_merges": false_merges,
        "common_failure_patterns": common_failure_patterns,
    }
