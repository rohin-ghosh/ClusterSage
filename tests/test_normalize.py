"""Tests for regex-based log normalization."""

from pathlib import Path

from app.normalize.canonicalize import TextNormalizer


def test_normalize_major_token_classes() -> None:
    """Major unstable token classes should be replaced deterministically."""
    normalizer = TextNormalizer.from_yaml(Path("configs/normalization.yaml"))
    text = (
        "2026-03-30 10:15:00 ERROR request_id=abc123def456ghi789 "
        "ip=10.24.8.19 uuid=123e4567-e89b-12d3-a456-426614174000 "
        "addr=0xDEADBEEF took 3000 ms score=98.6 retries=7 path=/var/log/nvidia/fabric.log"
    )

    normalized = normalizer.normalize(text)

    assert "<IP>" in normalized
    assert "<UUID>" in normalized
    assert "<HEX>" in normalized
    assert "<DURATION>" in normalized
    assert "<FLOAT>" in normalized
    assert "<INT>" in normalized
    assert "<PATH>" in normalized
    assert "<ID>" in normalized
