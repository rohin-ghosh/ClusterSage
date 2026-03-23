"""HTTP routes for health checks and future pipeline orchestration.

Routes should remain small and explicit. The main analysis logic belongs in the
pipeline modules, where it is easier to test and reason about.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Return a minimal service health payload."""
    return {"status": "ok", "service": "clustersage"}
