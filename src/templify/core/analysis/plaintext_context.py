# templify/core/analysis/context.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Dict

from .features import LineFeatures, extract_line_features
from .domain_scoring import DomainScores, score_line_domain

__all__ = ["PlaintextContext", "build_line_context"]


@dataclass(frozen=True)
class PlaintextContext:
    """
    Immutable bundle passed to detectors/matcher.

    - text: the already-normalized line text (from plaintext_intake)
    - features: per-line structural features (features.extract_line_features)
    - domain: per-line domain probabilities (domain_scoring.score_line_domain)
    - prior: optional document-level EMA prior over domains
    """
    text: str
    features: LineFeatures
    domain: DomainScores              # per-line domain probs
    prior: Optional[Mapping[str, float]] = None  # doc-level EMA prior (optional)


def build_line_context(
    text: str,
    packs: Mapping[str, object],       # typically Mapping[str, DomainPack]
    *,
    prior: Optional[Mapping[str, float]] = None,
    indent_level: int = 0,
    temperature: float = 1.0,
) -> PlaintextContext:
    """
    Create a LineContext from raw line text using your loaded domain packs.

    Args:
        text: single line of (post-intake) plaintext.
        packs: domain packs dict from load_domain_packs_from_dir(...).
        prior: optional doc-level domain prior (EMA).
        indent_level: pass a real indent if you have layout info; else 0.
        temperature: softmax temperature for domain scoring (lower = peakier).

    Returns:
        PlaintextContext
    """
    lf = extract_line_features(text, indent_level=indent_level)
    ds = score_line_domain(text, packs, lf=lf, temperature=temperature)
    return PlaintextContext(text=text, features=lf, domain=ds, prior=prior)
