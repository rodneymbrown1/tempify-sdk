"""
Unified public API for the detectors package.

Import from here in tests and calling code, e.g.:

    from templify.core.analysis.detectors import (
        ExactMatcher, find_exact_matches,
        RegexDetection, normalize_to_regex, regex_fallback, regex_match,
        HeadingDetection, classify_lines,
        SemanticClassifier, semantic_classify,
        HeuristicPrediction, SemanticPrediction,
        coerce_to_lines,
    )
"""

from .exact_matcher import (
    ExactMatcher,
    find_exact_matches,
    Detection as ExactDetection,  # alias if you want it, optional
)

from .regex_maker import (
    RegexDetection,
    normalize_to_regex,
    regex_fallback,
    match as regex_match,
)

from .heuristics.heading_detector import (
    HeadingDetection,
    score_heading,
    detect_headings,
    BASE_CLUES,
)

from .semantic_classifier import (
    SemanticClassifier,
    semantic_classify,
    SemanticPrediction,
)

from . import utils

__all__ = [
    # Exact matcher
    "ExactMatcher",
    "find_exact_matches",
    "ExactDetection",

    # Regex maker
    "RegexDetection",
    "normalize_to_regex",
    "regex_fallback",
    "regex_match",

    # Heuristic classifier
    "HeadingDetection",
    "classify_lines",
    "HeuristicPrediction",

    # Semantic classifier
    "SemanticClassifier",
    "semantic_classify",
    "SemanticPrediction",

    # Shared util
    "utils",
]
