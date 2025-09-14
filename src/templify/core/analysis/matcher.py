from .detectors import exact_matcher, regex_maker, semantic_classifier
from .detectors.heuristics import (
    heading_detector, list_detector, paragraph_detector, tabular_detector, callouts,
)
from .utils.pattern_descriptor import coerce_to_descriptor, PatternDescriptor

MATCHERS = {
    "exact": exact_matcher.match,
    "regex": regex_maker.match,
    "heuristic": {
        "heading": heading_detector.match,
        "list": list_detector.match,
        "paragraph": paragraph_detector.match,
        "table": tabular_detector.match,
        "callout": callouts.match,
    },
    "semantic": semantic_classifier.match,
}

def route_match(structure: str, text: str, features=None, domain=None):
    """
    Run detectors in priority order and normalize outputs into PatternDescriptor.
    """
    # 1. Exact
    if m := MATCHERS["exact"](text, domain=domain):
        return coerce_to_descriptor(m, signal="EXACT")

    # 2. Regex
    if m := MATCHERS["regex"](text, domain=domain):
        return coerce_to_descriptor(m, signal="REGEXABLE")

    # 3. Heuristic
    if structure in MATCHERS["heuristic"]:
        if m := MATCHERS["heuristic"][structure](text, features=features, domain=domain):
            return coerce_to_descriptor(m, signal="HEURISTIC")

    # 4. Semantic fallback
    if m := MATCHERS["semantic"](text, features=features, domain=domain):
        return coerce_to_descriptor(m, signal="SEMANTIC")

    # 5. Hard fallback
    return PatternDescriptor(
        class_="UNKNOWN",
        signals=["FALLBACK"],
        confidence=0.0,
        features={"text": text},
        domain_hint=domain or "GENERIC"
    )
