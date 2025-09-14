from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Sequence, Union, Optional, Dict, Any

from templify.core.analysis.utils.plaintext_context import PlaintextContext
from templify.core.analysis.detectors.utils import coerce_to_lines, normalize_line
from templify.core.analysis.forms.callouts import CalloutForm

# ---------- Public model ----------
@dataclass(frozen=True)
class DetectedCallout:
    line_idx: int
    score: float
    method: str = "heuristic"
    label: str = "callout"
    form: Optional[CalloutForm] = None  # classification filled in later

# ---------- Regex cues ----------
_WARNING_RE = re.compile(r"\b(WARNING|CAUTION|BLACK BOX)\b", re.IGNORECASE)
_QUOTE_RE   = re.compile(r'^(["\'>])')
_ATTRIB_RE  = re.compile(r"^-\s*[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*")
_CODE_RE    = re.compile(r"^\s{4,}|\t")
_MONO_RE    = re.compile(r"[;{}]|`.*`")

# ---------- Core scoring ----------
def score_callout_line(text: str) -> float:
    """
    Return a heuristic score [0,1] for whether a line looks like a callout.
    """
    if not text:
        return 0.0

    # indentation check (raw)
    if text.startswith("    ") or text.startswith("\t"):
        return 0.8

    s = normalize_line(text)

    score = 0.0
    if _WARNING_RE.search(s):
        score += 0.9
    if _QUOTE_RE.match(s) or _ATTRIB_RE.match(s):
        score += 0.7
    if _MONO_RE.search(s):
        score += 0.6

    return min(1.0, score)

# ---------- Classification ----------
def guess_callout_form(text: str) -> Optional[CalloutForm]:
    """
    Map a line into a CalloutForm type (classification).
    """
    if not text:
        return None

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

# ---------- Detector ----------
class CalloutHeuristicDetector:
    """Detect call-outs & special blocks using surface cues."""

    def detect(
        self, source: Union[Sequence[str], PlaintextContext], threshold: float = 0.5
    ) -> List[DetectedCallout]:
        lines = coerce_to_lines(source)
        results: List[DetectedCallout] = []

        for i, s in enumerate(lines):
            sc = score_callout_line(s)
            if sc >= threshold:
                results.append(
                    DetectedCallout(
                        line_idx=i,
                        score=sc,
                        method="heuristic",
                        form=None,  # form applied later in pipeline
                    )
                )
        return results

def match(lines, features=None, domain=None, threshold: float = 0.5, **kwargs):
    """
    Standardized entrypoint for the router.
    Delegates to the heuristic callout detector.
    """
    detector = CalloutHeuristicDetector()
    return detector.detect(lines, threshold=threshold)

