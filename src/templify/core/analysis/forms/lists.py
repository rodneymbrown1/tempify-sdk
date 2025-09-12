from __future__ import annotations
from typing import Dict, Any
from templify.core.analysis.detectors.list_detector import (
    BULLET_RE, ORDERED_RE, ORDERED_NESTED_RE,
    DEFINITION_RE, INDENTED_RE,
)

def classify_list_line(text: str, features: Dict[str, Any] | None = None) -> str:
    """
    Map a line (already detected as 'list') into a specific subtype:
    L-BULLET, L-ORDERED, L-CONTINUATION, L-DEFINITION
    """
    s = (text or "").strip()
    if not s:
        return "L-UNKNOWN"

    # Regex-based classification
    if BULLET_RE.match(s):
        return "L-BULLET"
    if ORDERED_RE.match(s) or ORDERED_NESTED_RE.match(s):
        return "L-ORDERED"
    if DEFINITION_RE.match(s):
        return "L-DEFINITION"
    if INDENTED_RE.match(s):
        return "L-CONTINUATION"

    # Metadata fallbacks (from DOCX/plaintext context)
    if features:
        if features.get("is_bullet"):
            return "L-BULLET"
        if features.get("is_numbered"):
            return "L-ORDERED"
        if features.get("indent_level", 0) > 0:
            return "L-CONTINUATION"
        if features.get("style_name", "").lower().startswith("definition"):
            return "L-DEFINITION"

    return "L-UNKNOWN"
