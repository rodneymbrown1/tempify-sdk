from __future__ import annotations
import re
from enum import Enum
from typing import Optional, Dict, Any


# ----------------- Canonical heading classes -----------------

class HeadingForm(str, Enum):
    """Axis 1 — Subtypes of headings & titles."""
    H_SHORT = "H-SHORT"          # Short headings (≤6 words, title/ALLCAPS)
    H_LONG = "H-LONG"            # Longer headings (≥7 words)
    H_SECTION_N = "H-SECTION-N"  # Numbered/roman section (1., 1.1, II., §)
    H_CONTENTS = "H-CONTENTS"    # Table of contents entry (leaders + page #)
    H_SUBTITLE = "H-SUBTITLE"    # Subtitle / overline (follows a title)


# ----------------- Regex helpers -----------------

_NUMERIC_SECTION_RE = re.compile(r"^\d+(\.\d+)*[.)]?\s+")
_ROMAN_SECTION_RE   = re.compile(r"^[IVXLCDM]+[.)]\s+", re.IGNORECASE)
_TOC_LEADER_RE      = re.compile(r"\.{2,}\s*\d+$")


# ----------------- Heuristic thresholds -----------------

MAX_SHORT_WORDS = 6
MIN_LONG_WORDS  = 7


# ----------------- Rule metadata -----------------

HEADING_RULES: Dict[HeadingForm, Dict[str, Any]] = {
    HeadingForm.H_SHORT: {
        "max_words": MAX_SHORT_WORDS,
        "casing": "title_or_allcaps",
    },
    HeadingForm.H_LONG: {
        "min_words": MIN_LONG_WORDS,
    },
    HeadingForm.H_SECTION_N: {
        "regex": [_NUMERIC_SECTION_RE, _ROMAN_SECTION_RE],
    },
    HeadingForm.H_CONTENTS: {
        "regex": [_TOC_LEADER_RE],
    },
    HeadingForm.H_SUBTITLE: {
        "position": "after_title",  # handled at aggregation stage
    },
}


# ----------------- Public helper -----------------

def guess_heading_form(text: str) -> Optional[HeadingForm]:
    """
    Roughly assign a heading form subtype (Axis 1) based on simple rules.
    Detectors (heuristic/regex/semantic) should call this to propose a form.
    """
    if not text:
        return None

    # Normalize whitespace
    s = " ".join(text.split())

    # 1. TOC entries
    if _TOC_LEADER_RE.search(s):
        return HeadingForm.H_CONTENTS

    # 2. Numbered / roman section headings
    if _NUMERIC_SECTION_RE.match(s) or _ROMAN_SECTION_RE.match(s):
        return HeadingForm.H_SECTION_N

    # 3. Word count split for short vs long
    word_count = len(s.split())
    if word_count <= MAX_SHORT_WORDS:
        return HeadingForm.H_SHORT
    if word_count >= MIN_LONG_WORDS:
        return HeadingForm.H_LONG

    return None
