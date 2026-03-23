"""Normalization rule loading and orchestration.

Rules defined in YAML will be mapped into a deterministic normalization pass so
unstable tokens can be replaced consistently across datasets. The point is to
make recurring events comparable, not to erase detail that may matter later.
"""
