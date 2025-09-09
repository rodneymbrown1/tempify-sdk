# src/templify/core/analysis/detectors/semantic_classifier.py
from __future__ import annotations
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Iterable, List, Dict, Any, Sequence, Union
from templify.core.analysis.plaintext_context import PlaintextContext
from templify.core.analysis.detectors.utils import coerce_to_lines

@dataclass(frozen=True)
class SemanticPrediction:
    line_idx: int
    title: str
    score: float
    method: str = "semantic"

def _extract_titles(domain_pack: Dict[str, Any] | Iterable[str] | None) -> List[str]:
    if domain_pack is None:
        return []
    if isinstance(domain_pack, dict):
        if "titles" in domain_pack and isinstance(domain_pack["titles"], list):
            return [str(t) for t in domain_pack["titles"]]
        if "sections" in domain_pack and isinstance(domain_pack["sections"], list):
            out = []
            for s in domain_pack["sections"]:
                t = s.get("title") if isinstance(s, dict) else None
                if t:
                    out.append(str(t))
            return out
    return [str(t) for t in domain_pack]


def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(a=a.lower().strip(), b=b.lower().strip()).ratio()


def semantic_scores(
    lines: Union[Sequence[str], PlaintextContext],
    candidates: Iterable[str],
) -> List[List[float]]:
    L = coerce_to_lines(lines)
    C = [str(c) for c in candidates]
    matrix: List[List[float]] = []
    for s in L:
        row = [_ratio(s, c) for c in C]
        matrix.append(row)
    return matrix


def semantic_classify(
    lines: Union[Sequence[str], PlaintextContext],
    candidates: Iterable[str],
    threshold: float = 0.82,
) -> List[SemanticPrediction]:
    L = coerce_to_lines(lines)
    C = [str(c) for c in candidates]
    preds: List[SemanticPrediction] = []
    if not C:
        return preds

    for i, s in enumerate(L):
        best_title = None
        best = 0.0
        for c in C:
            r = _ratio(s, c)
            if r > best:
                best = r
                best_title = c
        if best_title is not None and best >= threshold:
            preds.append(SemanticPrediction(i, best_title, best))
    return preds


class SemanticClassifier:
    def __init__(self, threshold: float = 0.82) -> None:
        self.threshold = threshold

    def classify(
        self,
        context_or_lines: Union[Sequence[str], PlaintextContext],
        domain_pack: Dict[str, Any] | Iterable[str] | None,
    ) -> List[SemanticPrediction]:
        titles = _extract_titles(domain_pack)
        return semantic_classify(context_or_lines, titles, threshold=self.threshold)
