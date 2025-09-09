"""
Utility functions for detectors.
Exports `normalize_line` and `coerce_to_lines` for easy import.
"""

from .coerce_to_lines import coerce_to_lines
from .normalize_line import normalize_line

__all__ = [
    "coerce_to_lines",
    "normalize_line",
]
