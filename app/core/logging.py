"""Logging helpers for ClusterSage.

The MVP should log enough information to make each pipeline stage traceable
without burying the user in framework noise.
"""

import logging


def get_logger(name: str) -> logging.Logger:
    """Return a module logger with default configuration."""
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(name)
