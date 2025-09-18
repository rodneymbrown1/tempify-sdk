# src/templify/core/analysis/forms/tables.py
from __future__ import annotations
import re
from enum import Enum
from typing import Optional


class TableForm(str, Enum):
    """Axis 1 — Subtypes of table-related lines."""
    T_ROW = "T-ROW"           # Normal data row
    T_HEADER = "T-HEADER"     # Header row (bold/ALLCAPS)
    T_CAPTION = "T-CAPTION"   # Table caption/title above/below
    T_FOOTNOTE = "T-FOOTNOTE" # Notes under the table


# Regex helpers
_PIPE_SEPARATED = re.compile(r"\s*\|\s*")
_TAB_SEPARATED = re.compile(r"\t+")


def guess_table_form(text: str) -> Optional[TableForm]:
    """
    Roughly classify a line of text as a table row/caption/etc.
    """
    if not text:
        return None

    s = " ".join(text.split())

    # Captions (common "Table 1. ..." or "TABLE 1:" patterns)
    if s.lower().startswith("table "):
        return TableForm.T_CAPTION

    # Pipe/tab separated → assume row
    if _PIPE_SEPARATED.search(s) or _TAB_SEPARATED.search(s):
        return TableForm.T_ROW

    # ALLCAPS row → header
    if s.isupper() and len(s.split()) <= 6:
        return TableForm.T_HEADER

    return None
