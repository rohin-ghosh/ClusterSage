"""Normalization rule loading and orchestration.

Rules defined in YAML will be mapped into a deterministic normalization pass so
unstable tokens can be replaced consistently across datasets. The point is to
make recurring events comparable, not to erase detail that may matter later.
"""

from dataclasses import dataclass
from pathlib import Path
import re

import yaml


@dataclass(slots=True)
class NormalizationRule:
    """A compiled regex rule used to canonicalize unstable tokens."""

    name: str
    pattern: re.Pattern[str]
    replacement: str


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
