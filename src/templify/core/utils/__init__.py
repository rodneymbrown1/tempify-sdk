"""
templify.core.utils
-------------------
Utility functions and helpers for intake and preprocessing.

Exports:
    - intake_plaintext     : normalize and ingest raw text input
    - PlaintextIntakeResult: dataclass result of plaintext intake
    - decode_bytes, normalize_text, detect_line_ending (low-level helpers)
    - Docx intake helpers (if needed later)
"""

from .plaintext_intake import (
    intake_plaintext,
    PlaintextIntakeResult,
    _decode_bytes as decode_bytes,
    _normalize_text as normalize_text,
    _detect_line_ending as detect_line_ending,
)

from .docx_intake import *  # if you want docx intake helpers exposed here

__all__ = [
    "intake_plaintext",
    "PlaintextIntakeResult",
    "decode_bytes",
    "normalize_text",
    "detect_line_ending",
]
