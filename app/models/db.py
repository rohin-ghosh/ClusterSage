"""DuckDB integration points for ClusterSage.

DuckDB is used as the local analytical store for intermediate and derived
artifacts. It supports inspection and reproducible analysis without requiring
distributed infrastructure for the MVP.
"""

from pathlib import Path

import duckdb


def connect(database_path: Path) -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection for local analysis."""
    return duckdb.connect(str(database_path))
