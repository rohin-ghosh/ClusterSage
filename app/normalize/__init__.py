"""Regex-based normalization for unstable log tokens."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re

import yaml


@dataclass(slots=True)
class NormalizationRule:
    """A compiled regex rule used to canonicalize unstable tokens."""

    name: str
    pattern: re.Pattern[str]
    replacement: str


class TextNormalizer:
    """Deterministic text normalizer backed by ordered regex rules."""

    def __init__(self, rules: list[NormalizationRule]) -> None:
        self.rules = rules

    @classmethod
    def from_yaml(cls, config_path: Path) -> "TextNormalizer":
        """Create a normalizer from a YAML rule set."""
        return cls(load_normalization_rules(config_path))

    def normalize(self, text: str) -> str:
        """Normalize unstable tokens while preserving overall readability."""
        normalized, _ = self.normalize_with_trace(text)
        return normalized

    def normalize_with_trace(self, text: str) -> tuple[str, dict[str, Any]]:
        """Normalize text and return counts for rules that changed it."""
        normalized = text
        replacement_counts: dict[str, int] = {}

        for rule in self.rules:
            normalized, count = rule.pattern.subn(rule.replacement, normalized)
            if count:
                replacement_counts[rule.name] = replacement_counts.get(rule.name, 0) + count

        return normalized, {
            "changed": normalized != text,
            "replacement_counts": replacement_counts,
        }


def load_normalization_rules(config_path: Path) -> list[NormalizationRule]:
    """Load and compile normalization rules from YAML."""
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    rules: list[NormalizationRule] = []
    for raw_rule in config.get("rules", []):
        if not raw_rule.get("enabled", True):
            continue
        rules.append(
            NormalizationRule(
                name=raw_rule["name"],
                pattern=re.compile(raw_rule["pattern"]),
                replacement=raw_rule["replacement"],
            )
        )
    return rules
