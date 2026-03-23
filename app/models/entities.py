"""Database-oriented entities for persisted ClusterSage artifacts.

These lightweight models will represent tables such as raw events, normalized
events, templates, scored windows, and candidate incidents.
"""

from dataclasses import dataclass


@dataclass(slots=True)
class TemplateEntity:
    """Placeholder entity representing an extracted event template."""

    template_id: str
    template_text: str
