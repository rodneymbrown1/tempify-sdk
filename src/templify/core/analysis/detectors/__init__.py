# src/templify/core/analysis/detectors/__init__.py
"""
Unified public API for the detectors package.

Import from here in tests and calling code, e.g.:

    from templify.core.analysis.detectors import (
        ExactMatcher, find_exact_matches,
        build_regexes_from_phrases, regex_search_lines,
        HeuristicClassifier, classify_lines,
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

from .heuristic_classifier import (
    HeuristicClassifier,
    classify_lines,
    HeuristicPrediction,
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
    "HeuristicClassifier",
    "classify_lines",
    "HeuristicPrediction",

    # Semantic classifier
    "SemanticClassifier",
    "semantic_classify",
    "SemanticPrediction",

    # Shared util
    "utils",
]
