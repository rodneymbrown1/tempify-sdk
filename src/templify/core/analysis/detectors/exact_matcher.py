# src/templify/core/analysis/detectors/exact_matcher.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, List, Dict, Any, Sequence, Union
from templify.core.analysis.utils.plaintext_context import PlaintextContext
from templify.core.analysis.detectors.utils import coerce_to_lines

@dataclass(frozen=True)
class Detection:
    line_idx: int
    title: str
    score: float
    method: str = "exact"

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


def find_exact_matches(
    lines: Union[Sequence[str], PlaintextContext],
    candidates: Iterable[str],
    case_insensitive: bool = True,
) -> List[Detection]:
    """Return detections where a line exactly equals any candidate (ignoring surrounding spaces).
    Accepts variations like 'Title' and 'Title:' by normalizing trailing punctuation.
    """
    L = coerce_to_lines(lines)
    cand_norm = {}
    for c in candidates:
        c0 = c.strip()
        c_key = c0.lower() if case_insensitive else c0
        cand_norm.setdefault(c_key, c0)

    results: List[Detection] = []
    for i, raw in enumerate(L):
        s = (raw or "").strip()
        s_trim = s[:-1] if s.endswith(":") else s
        keys = [s_trim, s]
        for k in keys:
            k_key = k.lower() if case_insensitive else k
            if k_key in cand_norm:
                results.append(Detection(line_idx=i, title=cand_norm[k_key], score=1.0, method="exact"))
                break
    return results


class ExactMatcher:
    def __init__(self, case_insensitive: bool = True) -> None:
        self.case_insensitive = case_insensitive

    def detect(
        self,
        context_or_lines: Union[Sequence[str], PlaintextContext],
        domain_pack: Dict[str, Any] | Iterable[str] | None,
    ) -> List[Detection]:
        titles = _extract_titles(domain_pack)
        return find_exact_matches(context_or_lines, titles, case_insensitive=self.case_insensitive)
    
def match(text, **kwargs):
    """
    Standardized entrypoint for the router.
    Delegates to existing exact-match logic.
    """
    # Strip out keys find_exact_matches doesn’t expect
    candidates = kwargs.pop("candidates", None)
    case_insensitive = kwargs.pop("case_insensitive", True)

    if candidates is None:
        # If no candidates provided, nothing to match
        return []

    return find_exact_matches(text, candidates, case_insensitive=case_insensitive)
