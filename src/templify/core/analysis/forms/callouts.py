from enum import Enum
import re
from typing import Optional
from templify.core.analysis.detectors.utils import normalize_line

class CalloutForm(str, Enum):
    """
    Axis 1 — Call-outs & special blocks.

    This enum defines canonical subtypes of callouts. Detection
    logic (regex/heuristics) is provided here via a helper so
    that downstream consumers can classify directly.
    """

    C_WARNING = "C-WARNING"  # Boxed warnings, black-box safety notices
    C_QUOTE   = "C-QUOTE"    # Quotes, epigraphs, attributions
    C_CODE    = "C-CODE"     # Code or snippet blocks

# ----------------- Regex cues -----------------
_WARNING_RE = re.compile(r"\b(WARNING|CAUTION|BLACK BOX)\b", re.IGNORECASE)
_QUOTE_RE   = re.compile(r'^(["\'>])')
_ATTRIB_RE  = re.compile(r"^-\s*[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*")
_MONO_RE    = re.compile(r"[;{}]|`.*`")

# ----------------- Classifier -----------------
def guess_callout_form(text: str) -> Optional[CalloutForm]:
    """
    Classify a line into a CalloutForm if it matches known cues.
    Returns None if no match.
    """
    if not text:
        return None

    # Raw indentation first
    if text.startswith("    ") or text.startswith("\t"):
        return CalloutForm.C_CODE

    s = normalize_line(text)

    if _WARNING_RE.search(s):
        return CalloutForm.C_WARNING
    if _QUOTE_RE.match(s) or _ATTRIB_RE.match(s):
        return CalloutForm.C_QUOTE
    if _MONO_RE.search(s):
        return CalloutForm.C_CODE

    return None
