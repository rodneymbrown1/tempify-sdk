from .detectors import exact_matcher, regex_maker, semantic_classifier
from .detectors.heuristics import (
    heading_detector, list_detector, paragraph_detector, tabular_detector, callouts,
)
from .utils.pattern_descriptor import coerce_to_descriptor, PatternDescriptor

MATCHERS = {
    "exact": exact_matcher.match,
    "regex": regex_maker.match,
    "heuristic": {
        "heading": heading_detector.match,      # should return H-SHORT, H-LONG, etc.
        "list": list_detector.match,            # should return L-BULLET, L-ORDERED, etc.
        "paragraph": paragraph_detector.match,  # should return P-BODY, P-LEAD, etc.
        "table": tabular_detector.match,        # should return T-ROW, T-CAPTION, etc.
        "callout": callouts.match,              # should return C-WARNING, C-QUOTE, etc.
    },
    "semantic": semantic_classifier.match,
}


def route_match(structure: str, text: str, features=None, domain=None):
    """
    Run detectors in priority order and normalize outputs into PatternDescriptor.
    Ensures type is always an Axis-1 code (H-*, L-*, P-*, T-*, C-*).
    """
    # 1. Exact
    if m := MATCHERS["exact"](text, domain=domain):
        return coerce_to_descriptor(m, signal="EXACT")

    # 2. Regex
    if m := MATCHERS["regex"](text, domain=domain):
        return coerce_to_descriptor(m, signal="REGEX")

    # 3. Heuristic by structure
    if structure in MATCHERS["heuristic"]:
        if m := MATCHERS["heuristic"][structure](text, features=features, domain=domain):
            return coerce_to_descriptor(m, signal="HEURISTIC")

    # 4. Semantic fallback (usually maps to P-BODY or H-LONG)
    if m := MATCHERS["semantic"](text, features=features, domain=domain):
        return coerce_to_descriptor(m, signal="SEMANTIC")

    # 5. Hard fallback
    return PatternDescriptor(
        type="UNKNOWN",
        signals=["FALLBACK"],
        confidence=0.0,
        features={"text": text},
        domain_hint=domain or "GENERIC",
    )
