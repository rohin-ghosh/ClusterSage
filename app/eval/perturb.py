"""Small perturbation utilities for robustness testing."""

from __future__ import annotations

import hashlib
import random
import re


IP_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
UUID_PATTERN = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
DURATION_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\s?(?:ms|s|sec|secs|seconds|m|min|mins|minutes|h|hr|hrs|hours)\b")
LONG_ID_PATTERN = re.compile(r"\b[A-Za-z0-9][A-Za-z0-9_-]{11,}\b")


def perturb_text(text: str, seed: int = 7) -> str:
    """Generate a deterministic noisy variant of a log line."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    generator = random.Random(seed + int(digest[:8], 16))
    perturbed = IP_PATTERN.sub(lambda _: _random_ip(generator), text)
    perturbed = UUID_PATTERN.sub(lambda _: _random_uuid(generator), perturbed)
    perturbed = DURATION_PATTERN.sub(lambda match: _random_duration(match.group(0), generator), perturbed)
    perturbed = LONG_ID_PATTERN.sub(lambda _: _random_long_id(generator), perturbed)
    return perturbed


def perturb_records(records: list[str], seed: int = 7) -> list[str]:
    """Generate perturbed variants for a list of log lines."""
    return [perturb_text(record, seed=seed + index) for index, record in enumerate(records)]


def _random_ip(generator: random.Random) -> str:
    return ".".join(str(generator.randint(1, 254)) for _ in range(4))


def _random_uuid(generator: random.Random) -> str:
    chunks = [8, 4, 4, 4, 12]
    alphabet = "0123456789abcdef"
    return "-".join("".join(generator.choice(alphabet) for _ in range(chunk)) for chunk in chunks)


def _random_duration(original: str, generator: random.Random) -> str:
    unit = "".join(character for character in original if character.isalpha()) or "ms"
    value = generator.randint(5, 5000)
    return f"{value} {unit}"


def _random_long_id(generator: random.Random) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(generator.choice(alphabet) for _ in range(16))
