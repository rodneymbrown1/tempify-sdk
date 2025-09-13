from __future__ import annotations
import re
from enum import Enum
from typing import Dict, Any, Optional

# Precompiled keyword regexes with word boundaries
SUMMARY_PATTERNS = [
    re.compile(rf"\b{kw}\b", re.IGNORECASE)
    for kw in ("summary", "abstract", "overview", "conclusion", "highlights")
]


class ParagraphForm(str, Enum):
    """
    Axis 1 — Paragraph subtypes.

    Canonical forms of paragraphs detected in text or DOCX.
    """

    P_BODY    = "P-BODY"     # Regular body text
    P_LEAD    = "P-LEAD"     # Lead-in / first-after-heading
    P_SUMMARY = "P-SUMMARY"  # Summaries, abstracts, conclusions
    P_UNKNOWN = "P-UNKNOWN"  # Fallback


def classify_paragraph_line(
    text: str,
    features: Optional[Dict[str, Any]] = None,
    *,
    is_first_after_heading: bool = False,
) -> ParagraphForm:
    """
    Map a line (already detected as 'paragraph') into a specific ParagraphForm subtype.
    """
    s = (text or "").strip()
    if not s:
        return ParagraphForm.P_UNKNOWN

    # --- Lead paragraph detection takes precedence ---
    if is_first_after_heading:
        if features and (features.get("bold") or features.get("italic")):
            return ParagraphForm.P_LEAD
        return ParagraphForm.P_LEAD

    # --- Summary/abstract detection (with stricter regex) ---
    lower = s.lower()
    if any(pat.search(lower) for pat in SUMMARY_PATTERNS):
        return ParagraphForm.P_SUMMARY

    # --- Default body text ---
    return ParagraphForm.P_BODY
