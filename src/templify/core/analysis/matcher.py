from .detectors import exact_matcher, regex_maker, semantic_classifier
from .detectors.heuristics import (
    heading_detector, list_detector, paragraph_detector, table_detector, callouts,
)
from .utils.pattern_descriptor import coerce_to_descriptor, PatternDescriptor

MATCHERS = {
    "exact": exact_matcher.match,
    "regex": regex_maker.match,
    "heuristic": {
        "heading": heading_detector.match,      # should return H-SHORT, H-LONG, etc.
        "list": list_detector.match,            # should return L-BULLET, L-ORDERED, etc.
        "paragraph": paragraph_detector.match,  # should return P-BODY, P-LEAD, etc.
        "table": table_detector.match,        # should return T-ROW, T-CAPTION, etc.
        "callout": callouts.match,              # should return C-WARNING, C-QUOTE, etc.
    },
    "semantic": semantic_classifier.match,
}

import logging
logger = logging.getLogger(__name__)

def route_match(
    text: str,
    *,
    structure: str | None = None,
    features=None,
    domain=None,
    titles_config=None,
    signal: str | None = None,
):
    """
    Run detectors in priority order.
    Two flows:
      - If a signal is provided, coerce directly with that signal.
      - Otherwise, auto-detect: exact → heuristic → regex → semantic → fallback.
    """
    logger.debug(f"[ROUTE_MATCH] text='{text[:150]}...' structure={structure} signal={signal}")

    # --- Flow 1: Explicit signal passed in ---
    if signal:
        logger.debug(f"→ using provided signal {signal}")
        return coerce_to_descriptor(
            raw=text,
            signal=signal,
            text=text,
            features=features,
            domain=domain,
        )

    # --- Flow 2: Auto-detect ---
    # 1. Exact
    if titles_config:
        m = MATCHERS["exact"](text, candidates=titles_config, domain=domain)
        if m:
            logger.debug("→ exact match hit")
            return coerce_to_descriptor(
                raw=m,
                signal="EXACT",
                text=text,
                features=features,
                domain=domain,
            )

    # 2. Heuristic
    if structure and structure in MATCHERS["heuristic"]:
        m = MATCHERS["heuristic"][structure](text, features=features, domain=domain)
        if m:
            logger.debug(f"→ heuristic match ({structure}) hit")
            return coerce_to_descriptor(
                raw=m,
                signal=f"HEURISTIC-{structure.upper()}",
                text=text,
                features=features,
                domain=domain,
            )
    else:
        logger.debug("→ no structure provided, trying all heuristic matchers")
        HEURISTIC_ORDER = ["heading", "list", "paragraph", "table", "callout"]

        for key in HEURISTIC_ORDER:
            detector = MATCHERS["heuristic"][key]
            m = detector(text, features=features, domain=domain)
            if m:
                logger.debug(f"→ heuristic match ({key}) hit")
                return coerce_to_descriptor(
                    raw=m,
                    signal=f"HEURISTIC-{key.upper()}",
                    text=text,
                    features=features,
                    domain=domain,
        )
            
        logger.debug("→ no heuristic matchers hit, trying regex")
        m = MATCHERS["regex"](text, domain=domain)
        logger.debug(f"→ regex result: {m}")
        if m:
            logger.debug("→ regex match hit")
            return coerce_to_descriptor(
                raw=m,
                signal="REGEX",
                text=text,
                features=features,
                domain=domain,
            )
                


    # 3. Regex
    m = MATCHERS["regex"](text, domain=domain)
    if m:
        logger.debug("→ regex match hit")
        return coerce_to_descriptor(
            raw=m,
            signal="REGEX",
            text=text,
            features=features,
            domain=domain,
        )

    # 4. Semantic
    m = MATCHERS["semantic"](text, features=features, domain=domain)
    if m:
        logger.debug("→ semantic match hit")
        return coerce_to_descriptor(
            raw=m,
            signal="SEMANTIC",
            text=text,
            features=features,
            domain=domain,
        )

    # 5. Fallback
    logger.debug("→ fallback UNKNOWN")
    return PatternDescriptor(
        type="UNKNOWN",
        signals=["FALLBACK"],
        confidence=0.0,
        features={"text": text},
        domain_hint=domain or "GENERIC",
    )
