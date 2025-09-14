from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional, List, Union
from templify.core.analysis.detectors.semantic_classifier import SemanticPrediction
from templify.core.analysis.forms.headings import HeadingForm
from templify.core.analysis.forms.paragraphs import ParagraphForm

@dataclass
class PatternDescriptor:
    """
    Unified schema for all detector outputs.

    Always represents one logical classification result.
    Produced by route_match() and consumed by config + plaintext pipeline.
    """
    class_: str
    signals: List[str]
    granularity: str
    regex: Optional[str] = None
    pattern: Optional[str] = None
    features: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    style_hint: Optional[str] = None
    domain_hint: Optional[str] = "GENERIC"

    def to_json(self) -> Dict[str, Any]:
        out = asdict(self)
        out["class"] = out.pop("class_")  # rename for JSON
        return out

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict, excluding None values."""
        d = asdict(self)
        # remove None or empty values for compactness
        return {k: v for k, v in d.items() if v not in (None, [], {}, "")}

def coerce_to_descriptor(raw: Any, signal: str = "GENERIC") -> PatternDescriptor:
    """
    Normalize raw detector outputs into a PatternDescriptor.
    Accepts dicts, enums (HeadingForm, ParagraphForm), SemanticPrediction(s), 
    or PatternDescriptor itself. Always returns a single PatternDescriptor.
    """

    # Already a descriptor
    if isinstance(raw, PatternDescriptor):
        return raw

    # Dict-style detector outputs
    if isinstance(raw, dict):
        return PatternDescriptor(
            class_=raw.get("class", "UNKNOWN"),
            signals=[signal],
            granularity=raw.get("granularity", "LINE"),
            regex=raw.get("regex"),
            pattern=raw.get("pattern"),
            features=raw.get("features"),
            confidence=raw.get("confidence", 0.0),
            style_hint=raw.get("style_hint"),
            domain_hint=raw.get("domain_hint", "GENERIC"),
        )

    # Handle HeadingForm
    if isinstance(raw, HeadingForm):
        return PatternDescriptor(
            class_=raw.value,
            signals=[signal],
            granularity="LINE",
            confidence=0.9,
            style_hint="Heading1",
        )

    # Handle ParagraphForm
    if isinstance(raw, ParagraphForm):
        return PatternDescriptor(
            class_=raw.value,
            signals=[signal],
            granularity="PARAGRAPH",
            confidence=0.8,
            style_hint="BodyText",
        )

    # Single semantic prediction
    if isinstance(raw, SemanticPrediction):
        return PatternDescriptor(
            class_="P-BODY",  # default semantic fallback class
            signals=["SEMANTIC"],
            granularity="LINE",
            confidence=raw.score,
            style_hint="BodyText",
            domain_hint="GENERIC",
            features={"title": raw.title},
        )

    # List of semantic predictions → pick best scoring
    if isinstance(raw, list) and raw and all(isinstance(p, SemanticPrediction) for p in raw):
        best = max(raw, key=lambda p: p.score)
        return coerce_to_descriptor(best, signal="SEMANTIC")

    # Fallback: unknown
    return PatternDescriptor(
        class_="UNKNOWN",
        signals=[signal],
        granularity="LINE",
        confidence=0.0,
    )
