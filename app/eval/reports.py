"""Report writing for benchmark runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_benchmark_reports(result: dict[str, Any], report_dir: Path, run_id: str) -> dict[str, Path]:
    """Write JSON and Markdown benchmark reports and return their paths."""
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / f"{run_id}.json"
    markdown_path = report_dir / f"{run_id}.md"

    json_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    markdown_path.write_text(render_markdown_report(result), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def render_markdown_report(result: dict[str, Any]) -> str:
    """Render a simple, inspectable Markdown benchmark summary."""
    dataset = result["dataset"]
    normalization = result["normalization"]
    sections: list[str] = [
        f"# ClusterSage Benchmark Report: {dataset['name']}",
        "",
        f"- Dataset type: `{dataset['dataset_type']}`",
        f"- Record count: `{dataset['record_count']}`",
        f"- Source path: `{dataset['source_path']}`",
        "",
        "## Normalization Summary",
        "",
        f"- Changed lines: `{normalization['changed_lines']}` / `{normalization['total_lines']}`",
        f"- Percent changed: `{normalization['percent_changed']}`",
        f"- Placeholder replacement counts: `{normalization['placeholder_replacement_counts']}`",
        "",
    ]

    if normalization["changed_examples"]:
        sections.extend(["### Before/After Examples", ""])
        for example in normalization["changed_examples"]:
            sections.extend(
                [
                    f"- Raw: `{example['raw_text']}`",
                    f"- Normalized: `{example['normalized_text']}`",
                ]
            )
        sections.append("")

    for method in result["methods"]:
        metrics = method["metrics"]
        errors = method["error_analysis"]
        sections.extend(
            [
                f"## Method: `{method['method']}`",
                "",
                f"- Predicted template count: `{metrics['predicted_template_count']}`",
                f"- Expected template count: `{metrics['expected_template_count']}`",
                f"- Exact template match rate: `{metrics['exact_template_match_rate']}`",
                f"- Grouping pair accuracy: `{metrics['grouping_pair_accuracy']}`",
                f"- Over-splitting pairs: `{metrics['over_splitting_pairs']}`",
                f"- Over-merging pairs: `{metrics['over_merging_pairs']}`",
                "",
            ]
        )
        if errors["template_mismatches"]:
            sections.extend(["### Template Mismatches", ""])
            for example in errors["template_mismatches"]:
                sections.extend(
                    [
                        f"- Raw: `{example['raw_text']}`",
                        f"- Expected: `{example['expected_template']}`",
                        f"- Predicted: `{example['predicted_template']}`",
                    ]
                )
            sections.append("")
        if errors["false_splits"]:
            sections.extend(["### False Splits", ""])
            for example in errors["false_splits"]:
                sections.append(
                    f"- Expected same group `{example['expected_group_id']}` but split: "
                    f"`{example['left_text']}` || `{example['right_text']}`"
                )
            sections.append("")
        if errors["false_merges"]:
            sections.extend(["### False Merges", ""])
            for example in errors["false_merges"]:
                sections.append(
                    f"- Incorrectly merged into `{example['predicted_group_id']}`: "
                    f"`{example['left_text']}` || `{example['right_text']}`"
                )
            sections.append("")
        if errors["common_failure_patterns"]:
            sections.extend(["### Common Failure Patterns", ""])
            for example in errors["common_failure_patterns"]:
                sections.append(f"- `{example['pattern']}`: `{example['count']}`")
            sections.append("")

    return "\n".join(sections).rstrip() + "\n"
