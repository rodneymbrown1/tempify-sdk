from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Sequence, Union, Dict, Any

from templify.core.analysis.utils.plaintext_context import PlaintextContext
from templify.core.analysis.detectors.utils import coerce_to_lines, normalize_line


@dataclass(frozen=True)
class ListDetection:
    line_idx: int
    label: str = "list"   # generic detection label, not subtype
    score: float = 0.0
    method: str = "heuristic"


# ---------- Regex patterns for heuristics ----------
BULLET_RE = re.compile(r"^\s*([\-–—•▪◦●·\*])\s+")
ORDERED_RE = re.compile(r"^\s*((\d+|[a-zA-Z]|[ivxlcdmIVXLCDM]+)([.)]))\s+")
ORDERED_NESTED_RE = re.compile(r"^\s*\d+(\.\d+)+\s+")
DEFINITION_RE = re.compile(r"^\s*\w+(?:\s+\w+)*\s*[:—–-]\s+")
INDENTED_RE = re.compile(r"^\s{4,}")  # ≥4 spaces → continuation candidate


def score_list_line(text: str) -> float:
    """
    Return a confidence score (0..1) for whether a line is list-like.
    Uses simple regex heuristics only.
    """
    if not text:
        return 0.0

    raw = text
    s = normalize_line(text)

    # Bullet
    if BULLET_RE.match(s):
        return 0.9
    # Ordered
    if ORDERED_RE.match(s) or ORDERED_NESTED_RE.match(s):
        return 0.9
    # Definition
    if DEFINITION_RE.match(s):
        return 0.8
    # Continuation (check raw, not normalized)
    if INDENTED_RE.match(raw):
        return 0.6

    return 0.0


def detect_lists(
    source: Union[Sequence[str], PlaintextContext],
    threshold: float = 0.55,
) -> List[ListDetection]:
    """
    Detect list-like lines. Returns generic ListDetection objects
    that can be further classified downstream.
    """
    lines = coerce_to_lines(source)
    preds: List[ListDetection] = []

    for i, s in enumerate(lines):
        sc = score_list_line(s)
        if sc >= threshold:
            preds.append(ListDetection(i, "list", sc))

    return preds

def match(lines, features=None, domain=None, threshold: float = 0.55, **kwargs):
    """
    Standardized entrypoint for the router.
    Delegates to the heuristic list detector.
    """
    return detect_lists(lines, threshold=threshold)
