from __future__ import annotations
from enum import Enum
from typing import Dict, Any, Optional

from templify.core.analysis.detectors.heuristics.list_detector import (
    BULLET_RE, ORDERED_RE, ORDERED_NESTED_RE,
    DEFINITION_RE, INDENTED_RE,
)


class ListForm(str, Enum):
    """
    Axis 1 — List subtypes.

    Canonical forms of lists detected in text or DOCX.
    """

    L_BULLET       = "L-BULLET"        # Bulleted list items
    L_ORDERED      = "L-ORDERED"       # Ordered / numbered lists
    L_DEFINITION   = "L-DEFINITION"    # Definition-style lists
    L_CONTINUATION = "L-CONTINUATION"  # Continuation / wrapped lines
    L_UNKNOWN      = "L-UNKNOWN"       # Fallback


def classify_list_line(text: str, features: Optional[Dict[str, Any]] = None) -> ListForm:
    """
    Map a line (already detected as 'list') into a specific ListForm subtype.
    """
    s = (text or "").strip()
    if not s:
        return ListForm.L_UNKNOWN

    # Regex-based classification
    if BULLET_RE.match(s):
        return ListForm.L_BULLET
    if ORDERED_RE.match(s) or ORDERED_NESTED_RE.match(s):
        return ListForm.L_ORDERED
    if DEFINITION_RE.match(s):
        return ListForm.L_DEFINITION
    if INDENTED_RE.match(s):
        return ListForm.L_CONTINUATION

    # Metadata fallbacks (from DOCX/plaintext context)
    if features:
        if features.get("is_bullet"):
            return ListForm.L_BULLET
        if features.get("is_numbered"):
            return ListForm.L_ORDERED
        if features.get("indent_level", 0) > 0:
            return ListForm.L_CONTINUATION
        if features.get("style_name", "").lower().startswith("definition"):
            return ListForm.L_DEFINITION

    return ListForm.L_UNKNOWN
