"""Simple baseline grouping strategies for benchmark runs."""

from __future__ import annotations

from collections import OrderedDict
from typing import Callable

from pydantic import BaseModel, Field


class PredictedRecord(BaseModel):
    """Predicted grouping output for a single normalized log line."""

    index: int = Field(ge=1)
    predicted_group_id: str
    predicted_template: str


def normalized_identity(records: list[dict]) -> list[PredictedRecord]:
    """Treat each unique normalized line as its own template."""
    return _assign_groups(
        records,
        key_fn=lambda record: record["normalized_text"],
        template_fn=lambda record: record["normalized_text"],
    )


def token_pattern_grouping(records: list[dict]) -> list[PredictedRecord]:
    """Group lines using a lightweight wildcard-aware token signature."""
    return _assign_groups(
        records,
        key_fn=lambda record: build_token_signature(record["normalized_text"]),
        template_fn=lambda record: build_token_signature(record["normalized_text"]),
    )


def available_methods() -> dict[str, Callable[[list[dict]], list[PredictedRecord]]]:
    """Return the supported baseline method registry."""
    return {
        "normalized_identity": normalized_identity,
        "token_pattern": token_pattern_grouping,
    }


def build_token_signature(text: str) -> str:
    """Create a readable, slightly generalized signature from a normalized line."""
    signature_tokens: list[str] = []
    for token in text.split():
        stripped = token.strip(",;")
        if stripped.startswith("<") and stripped.endswith(">"):
            signature_tokens.append(stripped)
        elif stripped.startswith("[") and stripped.endswith("]"):
            signature_tokens.append(stripped.lower())
        elif stripped.upper() in {"DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL", "FATAL"}:
            signature_tokens.append(stripped.upper())
        elif any(char.isdigit() for char in stripped):
            signature_tokens.append("<VAR>")
        else:
            signature_tokens.append(stripped.lower())
    return " ".join(signature_tokens)


def _assign_groups(
    records: list[dict],
    key_fn: Callable[[dict], str],
    template_fn: Callable[[dict], str],
) -> list[PredictedRecord]:
    """Assign deterministic group IDs based on a grouping key."""
    group_map: OrderedDict[str, str] = OrderedDict()
    predictions: list[PredictedRecord] = []

    for record in records:
        key = key_fn(record)
        if key not in group_map:
            group_map[key] = f"group_{len(group_map) + 1:03d}"
        predictions.append(
            PredictedRecord(
                index=record["index"],
                predicted_group_id=group_map[key],
                predicted_template=template_fn(record),
            )
        )
    return predictions
