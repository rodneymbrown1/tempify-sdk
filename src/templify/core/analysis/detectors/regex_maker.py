# src/templify/core/analysis/detectors/regex_maker.py
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Iterable, List, Pattern, Tuple, Sequence, Union, Any
from templify.core.analysis.plaintext_context import PlaintextContext
from templify.core.analysis.detectors.utils import coerce_to_lines

@dataclass(frozen=True)
class RegexDetection:
    line_idx: int
    title: str
    score: float
    pattern: str
    method: str = "regex"

def _normalize_phrase(phrase: str) -> str:
    # Make “robust but tight” regex for a phrase:
    # - escape literal chars
    # - allow flexible whitespace between words
    # - optional trailing ":" or " -"
    words = phrase.strip().split()
    escaped = [re.escape(w) for w in words]
    body = r"\s+".join(escaped) if escaped else ""
    if not body:
        return r"^\s*$"
    return rf"^\s*{body}\s*[:\-]?\s*$"


def build_regexes_from_phrases(
    phrases: Iterable[str],
    flags: int = re.IGNORECASE,
) -> List[Tuple[str, Pattern[str]]]:
    out: List[Tuple[str, Pattern[str]]] = []
    for p in phrases:
        pat = _normalize_phrase(str(p))
        out.append((str(p), re.compile(pat, flags)))
    return out


def regex_search_lines(
    lines: Union[Sequence[str], PlaintextContext],
    regexes: List[Tuple[str, Pattern[str]]],
) -> List[RegexDetection]:
    L = coerce_to_lines(lines)
    hits: List[RegexDetection] = []
    for i, s in enumerate(L):
        text = (s or "").strip()
        for title, rgx in regexes:
            if rgx.match(text):
                # Simple scoring: longer patterns are slightly preferred
                score = min(1.0, 0.7 + 0.3 * (len(title) / 40.0))
                hits.append(RegexDetection(i, title, score, rgx.pattern))
                break
    return hits
