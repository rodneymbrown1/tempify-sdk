from __future__ import annotations
import re
from typing import Dict, Any

# Keyword triggers for summaries/abstracts
SUMMARY_KEYWORDS = {
    "summary", "abstract", "overview", "conclusion", "highlights"
}

def classify_paragraph_line(
    text: str,
    features: Dict[str, Any] | None = None,
    *,
    is_first_after_heading: bool = False,
) -> str:
    """
    Map a line (already detected as 'paragraph') into a subtype:
    P-BODY, P-LEAD, P-SUMMARY.
    """
    s = (text or "").strip()
    if not s:
        return "P-UNKNOWN"

    # --- Summary/abstract detection ---
    lower = s.lower()
    if any(kw in lower for kw in SUMMARY_KEYWORDS):
        return "P-SUMMARY"

    # --- Lead paragraph detection ---
    if is_first_after_heading:
        # Features can help disambiguate (e.g., bold, italic, font size boost)
        if features:
            if features.get("bold") or features.get("italic"):
                return "P-LEAD"
        # Even without features, first-after-heading can be lead
        return "P-LEAD"

    # --- Default body text ---
    return "P-BODY"
