"""Canonicalization routines for unstable log content.

This module will turn variant-heavy raw lines into more comparable normalized
forms by replacing IDs, addresses, and other noisy fields with placeholders.
The resulting text should be easier to group and rank while still traceable to
the original log line.
"""

from pathlib import Path

from app.normalize.rules import NormalizationRule, load_normalization_rules


class TextNormalizer:
    """Deterministic text normalizer backed by regex replacement rules."""

    def __init__(self, rules: list[NormalizationRule]) -> None:
        self.rules = rules

    @classmethod
    def from_yaml(cls, config_path: Path) -> "TextNormalizer":
        """Create a normalizer from a YAML rule set."""
        return cls(load_normalization_rules(config_path))

    def normalize(self, text: str) -> str:
        """Normalize unstable tokens while preserving overall readability."""
        normalized = text
        for rule in self.rules:
            normalized = rule.pattern.sub(rule.replacement, normalized)
        return normalized
