from dataclasses import dataclass, asdict,field
from typing import Any, Dict, Optional, List, Union
from templify.core.analysis.detectors.semantic_classifier import SemanticPrediction
from templify.core.analysis.forms.headings import HeadingForm
from templify.core.analysis.forms.paragraphs import ParagraphForm

@dataclass
class PatternDescriptor:
    """
    Unified schema for detector outputs and config serialization.

    Matches new skeleton config spec:
      - Anchors and body patterns carry full descriptors
      - Structured style block (font, paragraph, list_type, etc.)
      - Optional layout_group override
    """

    class_: str
    signals: List[str]
    confidence: float
    features: Dict[str, Any] = field(default_factory=dict)

    # Style properties (structured)
    style: Optional[Dict[str, Any]] = None

    # Optional overrides
    layout_group: Optional[str] = None
    domain_hint: Optional[str] = "GENERIC"

    def to_dict(self) -> Dict[str, Any]:
        """Export to JSON-like dict, drop empty fields."""
        d = asdict(self)
        d["class"] = d.pop("class_")
        return {k: v for k, v in d.items() if v not in (None, [], {}, "")}

def coerce_to_descriptor(raw: Any, signal: str = "GENERIC") -> PatternDescriptor:
    # Already a descriptor
    if isinstance(raw, PatternDescriptor):
        return raw

    # Dict output
    if isinstance(raw, dict):
        return PatternDescriptor(
            class_=raw.get("class", "UNKNOWN"),
            signals=[signal],
            confidence=raw.get("confidence", 0.0),
            features=raw.get("features", {}),
            style=raw.get("style"),   # full structured style now
            layout_group=raw.get("layout_group"),
            domain_hint=raw.get("domain_hint", "GENERIC"),
        )

    # HeadingForm
    if isinstance(raw, HeadingForm):
        return PatternDescriptor(
            class_=raw.value,
            signals=[signal],
            confidence=0.9,
            features={},
            style={
                "pStyle": "Heading1",
                "font": {"bold": True, "size": 14},
                "paragraph": {"alignment": "left"},
            },
        )

    # ParagraphForm
    if isinstance(raw, ParagraphForm):
        return PatternDescriptor(
            class_=raw.value,
            signals=[signal],
            confidence=0.8,
            features={},
            style={
                "pStyle": "Normal",
                "font": {"size": 12},
                "paragraph": {"alignment": "left"},
            },
        )

    # SemanticPrediction
    if isinstance(raw, SemanticPrediction):
        return PatternDescriptor(
            class_="P-BODY",
            signals=["SEMANTIC"],
            confidence=raw.score,
            features={"title": raw.title},
            style={
                "pStyle": "Normal",
                "font": {"size": 12},
                "paragraph": {"alignment": "left"},
            },
        )

    # List[SemanticPrediction]
    if isinstance(raw, list) and raw and all(isinstance(p, SemanticPrediction) for p in raw):
        best = max(raw, key=lambda p: p.score)
        return coerce_to_descriptor(best, signal="SEMANTIC")

    # Fallback
    return PatternDescriptor(
        class_="UNKNOWN",
        signals=[signal],
        confidence=0.0,
        features={"raw": str(raw)},
    )
