# src/templify/core/analysis/detectors/__init__.py
"""
Unified public API for the detectors package.

Import from here in tests and calling code, e.g.:

    from templify.core.analysis.detectors import (
        ExactMatcher, find_exact_matches,
        build_regexes_from_phrases, regex_search_lines,
        HeadingDetection, classify_lines,
        SemanticClassifier, semantic_classify,
        RegexDetection, HeuristicPrediction, SemanticPrediction,
        coerce_to_lines,
    )
"""

from .exact_matcher import (
    ExactMatcher,
    find_exact_matches,
    Detection as ExactDetection,  # alias if you want it, optional
)

from .regex_maker import (
    build_regexes_from_phrases,
    regex_search_lines,
    RegexDetection,
)

from .heading_detector import (
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
    "build_regexes_from_phrases",
    "regex_search_lines",
    "RegexDetection",

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
