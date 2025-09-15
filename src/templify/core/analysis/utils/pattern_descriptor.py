from dataclasses import dataclass, asdict,field
from typing import Any, Dict, Optional, List, Union
from templify.core.analysis.detectors.semantic_classifier import SemanticPrediction
from templify.core.analysis.forms.headings import HeadingForm
from templify.core.analysis.forms.paragraphs import ParagraphForm

class PatternDescriptor:
    def __init__(
        self,
        text: str | None = None,
        type: str | None = None,   # Axis 1 code (H-SHORT, L-BULLET, etc.)
        *,
        class_: str | None = None, # backward compat
        signals: list[str] | None = None,
        confidence: float = 1.0,
        features: dict | None = None,
        style: dict | None = None,
        layout_group: str | None = None,
        domain_hint: str = "GENERIC",
        method: str = "heuristic",
        paragraph_id: str | None = None,
        score: float = 1.0,
    ):
        # Use Axis 1 taxonomy as canonical type
        self.type = type or class_ or "UNKNOWN"
        self.text = text or ""
        self.signals = signals or []
        self.confidence = confidence
        self.features = features or {}
        self.style = style or {}
        self.layout_group = layout_group
        self.domain_hint = domain_hint
        self.method = method
        self.paragraph_id = paragraph_id
        self.id = f"pat_{id(self)}"  # stable enough for now
        self.score = score

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "paragraph_id": self.paragraph_id,
            "type": self.type,          # <-- Axis 1 code
            "text": self.text,
            "features": self.features,
            "score": self.score,
            "method": self.method,
        }

def coerce_to_descriptor(raw: Any, signal: str = "GENERIC") -> PatternDescriptor:
    if isinstance(raw, PatternDescriptor):
        return raw

    if isinstance(raw, dict):
        return PatternDescriptor(
            type=raw.get("type") or raw.get("class") or "UNKNOWN",
            signals=[signal],
            confidence=raw.get("confidence", 0.0),
            features=raw.get("features", {}),
            style=raw.get("style"),
            layout_group=raw.get("layout_group"),
            domain_hint=raw.get("domain_hint", "GENERIC"),
        )

    if isinstance(raw, HeadingForm):
        return PatternDescriptor(
            type=raw.value,  # Axis 1: H-SHORT, H-LONG, etc.
            signals=[signal],
            confidence=0.9,
            style={"pStyle": "Heading1"},
        )

    if isinstance(raw, ParagraphForm):
        return PatternDescriptor(
            type=raw.value,  # Axis 1: P-BODY, P-LEAD, etc.
            signals=[signal],
            confidence=0.8,
            style={"pStyle": "Normal"},
        )

    if isinstance(raw, SemanticPrediction):
        return PatternDescriptor(
            type="P-BODY",
            signals=["SEMANTIC"],
            confidence=raw.score,
            features={"title": raw.title},
            style={"pStyle": "Normal"},
        )

    if isinstance(raw, list) and raw and all(isinstance(p, SemanticPrediction) for p in raw):
        best = max(raw, key=lambda p: p.score)
        return coerce_to_descriptor(best, signal="SEMANTIC")

    return PatternDescriptor(type="UNKNOWN", signals=[signal], confidence=0.0, features={"raw": str(raw)})
