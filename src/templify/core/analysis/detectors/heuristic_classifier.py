# src/templify/core/analysis/detectors/heuristic_classifier.py
from __future__ import annotations

import re
from dataclasses import dataclass, is_dataclass, asdict
from typing import Callable, Iterable, List, Dict, Any, Sequence, Union, Optional

from templify.core.analysis.features import extract_line_features
from templify.core.analysis.plaintext_context import PlaintextContext
from templify.core.analysis.detectors.utils import coerce_to_lines, normalize_line

# ---------- Public model ----------
@dataclass(frozen=True)
class HeuristicPrediction:
    line_idx: int
    label: str
    score: float
    method: str = "heuristic"

# ---------- Clue infrastructure ----------
Predicate = Callable[[str], bool]
Preprocessor = Callable[[str], str]

@dataclass(frozen=True)
class HeuristicClue:
    """A single heuristic signal."""
    name: str
    weight: float
    predicate: Predicate
    # Optional textual preprocessor run *before* predicate (e.g., strip numbering)
    pre: Optional[Preprocessor] = None

    def fires(self, text: str) -> bool:
        s = self.pre(text) if self.pre else text
        return bool(self.predicate(s))

# Utilities for reuse
def _features_to_dict(features: Any | None) -> Dict[str, Any]:
    if features is None:
        return {}
    if isinstance(features, dict):
        return features
    if is_dataclass(features):
        return asdict(features)
    return dict(getattr(features, "__dict__", {}))

# ---------- Common regexes & preprocessors ----------
# Accept "1 ", "1. ", "1.2 ", "1.2.3 ", "1) ", "1.2) ", etc.
_NUM_HEAD_RE   = re.compile(r"^\(?\d+(?:\.\d+)*[.)]?\s+")
# Roman headings require '.' or ')' to avoid false positives like "IV infusion"
_ROMAN_HEAD_RE = re.compile(r"^[IVXLCDM]+[.)]\s+", re.IGNORECASE)

_TITLE_CASE_RE        = re.compile(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,5}\s*$")
_TITLE_CASE_COLON_RE  = re.compile(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,5}:\s*$")  # NEW
_ALL_CAPS_RE = re.compile(r"^[A-Z0-9][A-Z0-9\s\-\&/\W]*$")
_COLON_RE             = re.compile(r"[:]\s*$")
_BULLET_RE            = re.compile(r"^\s*([\-–—•▪◦●·])\s+")
_TOC_DOTS_RE          = re.compile(r"[.]{2,}\s*\d+$")
_TRAILING_DOT_RE      = re.compile(r"[ \t\.]+$")  # strip only spaces and dots (keep colons etc.)

def strip_leading_numbering(s: str) -> str:
    return _NUM_HEAD_RE.sub("", s).strip()

def strip_leading_heading(s: str) -> str:
    """Remove numeric OR Roman heading prefix (with dot/paren), returning trimmed text."""
    out = _NUM_HEAD_RE.sub("", s, count=1)
    if out != s:
        return out.strip()
    return _ROMAN_HEAD_RE.sub("", s, count=1).strip()

def strip_trailing_dot(s: str) -> str:
    """Remove a harmless trailing period (and adjacent whitespace). Keeps colons intact."""
    return _TRAILING_DOT_RE.sub("", s)

def compose_pre(*funcs: Preprocessor) -> Preprocessor:
    """Compose multiple preprocessors into one, in order."""
    def _f(x: str) -> str:
        for f in funcs:
            x = f(x)
        return x
    return _f

# ---------- Base clues (extensible registry) ----------
def _re_pred(rgx: re.Pattern[str]) -> Predicate:
    return lambda s: bool(rgx.search(s))

BASE_CLUES: List[HeuristicClue] = [
    # Positive
    HeuristicClue("all_caps",              0.55, _re_pred(_ALL_CAPS_RE)),
    HeuristicClue("title_case",            0.39, _re_pred(_TITLE_CASE_RE)),
    HeuristicClue("title_case_with_colon", 0.39, _re_pred(_TITLE_CASE_COLON_RE)),  # NEW
    HeuristicClue("trailing_colon",        0.25, _re_pred(_COLON_RE)),
    HeuristicClue("num_heading",           0.30, _re_pred(_NUM_HEAD_RE)),
    HeuristicClue("roman_num_heading",     0.30, _re_pred(_ROMAN_HEAD_RE)),

    HeuristicClue(
        "title_case_after_num",
        0.39,
        _re_pred(_TITLE_CASE_RE),
        pre=compose_pre(strip_leading_heading, strip_trailing_dot),
    ),

    # Negative
    HeuristicClue("bullet_or_dash", -0.30, _re_pred(_BULLET_RE)),
    HeuristicClue("toc_dots",       -0.20, _re_pred(_TOC_DOTS_RE)),
]

# Optional domain profile (can diverge later)
STRICT_CLUES: List[HeuristicClue] = BASE_CLUES  # placeholder for future override

# ---------- Synergy bonuses (AND-logic without brittle mega-regexes) ----------
# If every clue in the set fired for a line, apply the small bonus.
SYNERGY_RULES: List[tuple[set[str], float]] = [
    ({"num_heading", "title_case_after_num"},        0.50),  # "1. Introduction"
    ({"roman_num_heading", "title_case_after_num"},  0.10),  # "II. Methods"
     ({"trailing_colon", "title_case"},               0.25), 
    # Example future additions:
    # ({"all_caps", "trailing_colon"}, 0.05),
]

# ---------- Scoring ----------
def score_line_heuristics(
    text: str,
    features: Dict[str, Any] | None = None,
    clues: Iterable[HeuristicClue] = BASE_CLUES,
    *,
    clamp_min: float = 0.0,
    clamp_max: float = 1.0,
) -> float:
    """
    Combine pluggable clues (+ optional features) into a 0..1 score.
    Pass a custom 'clues' list to tune behavior without touching code.
    """
    s = normalize_line(text or "")
    if not s:
        return 0.0

    score = 0.0
    fired: set[str] = set()

    for clue in clues:
        try:
            if clue.fires(s):
                score += clue.weight
                fired.add(clue.name)
        except Exception:
            # Defensive: a bad custom clue should not crash the pipeline.
            continue

    # Feature tweaks (works for DOCX and plaintext; missing keys are harmless)
    feats = _features_to_dict(features)
    if feats:
        is_heading = bool({"num_heading", "roman_num_heading"} & fired)

        if feats.get("contains_text"):
            score += 0.05

        # Don't penalize if we already identified a heading
        if feats.get("begins_non_letter") and not is_heading:
            score -= 0.10

        if feats.get("contains_number"):
            score += 0.05

        if feats.get("contains_list_numbering") and not is_heading:
            score -= 0.15

        if feats.get("bold"):
            score += 0.10

        if (feats.get("font_size", 0) or 0) >= 14:
            score += 0.10
    # Synergy bonuses
    try:
        for need, bonus in SYNERGY_RULES:
            if need.issubset(fired):
                score += bonus
    except Exception:
        # Never let synergy logic break scoring
        pass

    # Optional cap to avoid runaway stacking if you add many positives
    if clamp_max is not None:
        score = min(score, clamp_max)
    if clamp_min is not None:
        score = max(score, clamp_min)
    return score

def classify_lines(
    source: Union[Sequence[str], PlaintextContext],
    threshold: float = 0.55,
    label: str = "title",
    clues: Iterable[HeuristicClue] = BASE_CLUES,
) -> List[HeuristicPrediction]:
    lines = coerce_to_lines(source)
    preds: List[HeuristicPrediction] = []
    for i, s in enumerate(lines):
        feats = None
        if extract_line_features is not None:
            try:
                feats = extract_line_features(s)
            except Exception:
                feats = None
        sc = score_line_heuristics(s, feats, clues=clues)
        if sc >= threshold:
            preds.append(HeuristicPrediction(i, label, sc))
    return preds

class HeuristicClassifier:
    def __init__(self, threshold: float = 0.55, clues: Iterable[HeuristicClue] = BASE_CLUES) -> None:
        self.threshold = threshold
        # freeze a list copy so later global tweaks don’t surprise existing instances
        self.clues = list(clues)

    def classify(self, source: Union[Sequence[str], PlaintextContext]) -> List[HeuristicPrediction]:
        return classify_lines(source, threshold=self.threshold, clues=self.clues)
