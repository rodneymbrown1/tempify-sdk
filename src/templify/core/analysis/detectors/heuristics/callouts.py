from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Sequence, Union, Optional

from templify.core.analysis.utils.plaintext_context import PlaintextContext
from templify.core.analysis.detectors.utils import coerce_to_lines, normalize_line
from templify.core.analysis.forms.callouts import CalloutForm

# ---------- Public model ----------
@dataclass(frozen=True)
class DetectedCallout:
    line_idx: int
    form: CalloutForm
    score: float
    method: str = "heuristic"

# ---------- Regex cues (written against normalized ASCII forms) ----------
_WARNING_RE = re.compile(r"\b(WARNING|CAUTION|BLACK BOX)\b", re.IGNORECASE)
_QUOTE_RE   = re.compile(r'^(["\'>])')  # leading quote char or markdown blockquote
_ATTRIB_RE  = re.compile(r"^-\s*[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*")  # "- Author", "- Shakespeare"
_CODE_RE    = re.compile(r"^\s{4,}|\t")       # indentation
_MONO_RE    = re.compile(r"[;{}]|`.*`")       # typical monospace/code markers

# ---------- Core scoring ----------
def score_callout_line(text: str) -> Optional[CalloutForm]:
    if not text:
        return None

    # Check indentation BEFORE normalize_line (since normalize strips runs)
    if text.startswith("    ") or text.startswith("\t"):
        return CalloutForm.C_CODE

    # Normalize for other rules
    s = normalize_line(text)

    # Warning / safety boxes
    if _WARNING_RE.search(s):
        return CalloutForm.C_WARNING

    # Quotes / epigraphs
    if _QUOTE_RE.match(s) or _ATTRIB_RE.match(s):
        return CalloutForm.C_QUOTE

    # Code snippets (monospace markers etc.)
    if _MONO_RE.search(s):
        return CalloutForm.C_CODE

    return None

# ---------- Detector ----------
class CalloutHeuristicDetector:
    """Detect call-outs & special blocks using surface cues."""

    def detect(self, source: Union[Sequence[str], PlaintextContext]) -> List[DetectedCallout]:
        lines = coerce_to_lines(source)
        results: List[DetectedCallout] = []
        for i, s in enumerate(lines):
            form = score_callout_line(s)
            if form:
                # fixed confidence for now, could be weighted later
                results.append(DetectedCallout(i, form, score=0.9, method="heuristic"))
        return results
