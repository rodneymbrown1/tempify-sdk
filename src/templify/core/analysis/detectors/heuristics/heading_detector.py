from __future__ import annotations
import re
from dataclasses import dataclass, asdict, is_dataclass
from typing import Callable, Iterable, List, Dict, Any, Sequence, Union, Optional

from templify.core.analysis.features import extract_line_features
from templify.core.analysis.utils.plaintext_context import PlaintextContext
from templify.core.analysis.detectors.utils import coerce_to_lines, normalize_line

# ---------- Public model ----------
@dataclass(frozen=True)
class HeadingDetection:
    line_idx: int
    label: str
    score: float
    method: str = "heuristic"

# ---------- Infrastructure ----------
Predicate = Callable[[str], bool]
Preprocessor = Callable[[str], str]

@dataclass(frozen=True)
class HeadingClue:
    """A single heuristic signal for heading detection."""
    name: str
    weight: float
    predicate: Predicate
    pre: Optional[Preprocessor] = None  # run before predicate

    def fires(self, text: str) -> bool:
        s = self.pre(text) if self.pre else text
        return bool(self.predicate(s))

def _features_to_dict(features: Any | None) -> Dict[str, Any]:
    if features is None:
        return {}
    if isinstance(features, dict):
        return features
    if is_dataclass(features):
        return asdict(features)
    return dict(getattr(features, "__dict__", {}))

# ---------- Regexes ----------
_NUM_HEAD_RE   = re.compile(r"^\(?\d+(?:\.\d+)*[.)]?\s+")
_ROMAN_HEAD_RE = re.compile(r"^[IVXLCDM]+[.)]\s+", re.IGNORECASE)
_TITLE_CASE_RE = re.compile(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,5}\s*$")
_TITLE_CASE_COLON_RE = re.compile(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,5}:\s*$")
_ALL_CAPS_RE   = re.compile(r"^[A-Z0-9][A-Z0-9\s\-\&/\W]*$")
_COLON_RE      = re.compile(r"[:]\s*$")
_BULLET_RE     = re.compile(r"^\s*([\-–—•▪◦●·])\s+")
_TOC_DOTS_RE   = re.compile(r"[.]{2,}\s*\d+$")
_TRAILING_DOT_RE = re.compile(r"[ \t\.]+$")

def strip_leading_numbering(s: str) -> str:
    return _NUM_HEAD_RE.sub("", s).strip()

def strip_leading_heading(s: str) -> str:
    out = _NUM_HEAD_RE.sub("", s, count=1)
    if out != s:
        return out.strip()
    return _ROMAN_HEAD_RE.sub("", s, count=1).strip()

def strip_trailing_dot(s: str) -> str:
    return _TRAILING_DOT_RE.sub("", s)

def compose_pre(*funcs: Preprocessor) -> Preprocessor:
    def _f(x: str) -> str:
        for f in funcs: x = f(x)
        return x
    return _f

# ---------- Clues ----------
def _re_pred(rgx: re.Pattern[str]) -> Predicate:
    return lambda s: bool(rgx.search(s))

BASE_CLUES: List[HeadingClue] = [
    HeadingClue("all_caps",        0.55, _re_pred(_ALL_CAPS_RE)),
    HeadingClue("title_case",      0.39, _re_pred(_TITLE_CASE_RE)),
    HeadingClue("trailing_colon",  0.25, _re_pred(_COLON_RE)),
    HeadingClue("title_case_with_colon", 0.39, _re_pred(_TITLE_CASE_COLON_RE)),
    HeadingClue("num_heading",     0.30, _re_pred(_NUM_HEAD_RE)),
    HeadingClue("roman_heading",   0.30, _re_pred(_ROMAN_HEAD_RE)),
    HeadingClue(
        "title_after_num",
        0.39,
        _re_pred(_TITLE_CASE_RE),
        pre=compose_pre(strip_leading_heading, strip_trailing_dot),
    ),
    # Negative
    HeadingClue("bullet_or_dash", -0.30, _re_pred(_BULLET_RE)),
    HeadingClue("toc_dots",       -0.20, _re_pred(_TOC_DOTS_RE)),
]

SYNERGY_RULES: List[tuple[set[str], float]] = [
    ({"num_heading", "title_after_num"}, 0.50),
    ({"roman_heading", "title_after_num"}, 0.10),
    ({"trailing_colon", "title_case"}, 0.25),
]

# ---------- Core scoring ----------
def score_heading(text: str, features: Dict[str, Any] | None = None,
                  clues: Iterable[HeadingClue] = BASE_CLUES) -> float:
    s = normalize_line(text or "")
    if not s:
        return 0.0

    score, fired = 0.0, set()

    for clue in clues:
        if clue.fires(s):
            score += clue.weight
            fired.add(clue.name)

    feats = _features_to_dict(features)
    if feats:
        is_heading = bool({"num_heading", "roman_heading"} & fired)

        if feats.get("bold"): score += 0.10
        if (feats.get("font_size", 0) or 0) >= 14: score += 0.10
        if feats.get("contains_list_numbering") and not is_heading: score -= 0.15

    for need, bonus in SYNERGY_RULES:
        if need.issubset(fired):
            score += bonus

    return max(0.0, min(1.0, score))

# ---------- Public API ----------
def detect_headings(
    source: Union[Sequence[str], PlaintextContext],
    threshold: float = 0.55,
    label: str = "heading",
    clues: Iterable[HeadingClue] = BASE_CLUES,
) -> List[HeadingDetection]:
    lines = coerce_to_lines(source)
    preds: List[HeadingDetection] = []

    for i, s in enumerate(lines):
        feats = None
        if extract_line_features:
            try: feats = extract_line_features(s)
            except Exception: feats = None

        sc = score_heading(s, feats, clues=clues)
        if sc >= threshold:
            preds.append(HeadingDetection(i, label, sc))

    return preds
