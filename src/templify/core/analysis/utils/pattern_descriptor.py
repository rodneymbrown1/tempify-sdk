from dataclasses import dataclass, asdict,field
from typing import Any, Dict, Optional, List, Union
from templify.core.analysis.detectors.semantic_classifier import SemanticPrediction
from templify.core.analysis.forms.headings import HeadingForm
from templify.core.analysis.forms.paragraphs import ParagraphForm
from typing import Any, List
from templify.core.analysis.forms.headings import HeadingForm
from templify.core.analysis.forms.paragraphs import ParagraphForm
from templify.core.analysis.detectors.heuristics.paragraph_detector import ParagraphDetection
from templify.core.analysis.detectors.heuristics.heading_detector import HeadingDetection
from templify.core.analysis.detectors.heuristics.list_detector import ListDetection
from templify.core.analysis.detectors.heuristics.tabular_detector import TableDetection
from templify.core.analysis.detectors.heuristics.callouts import CalloutDetection
from templify.core.analysis.detectors.semantic_classifier import SemanticPrediction
from templify.core.analysis.detectors.regex_maker import RegexDetection

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
            "style": self.style,
            "signals": self.signals, 
        }

def coerce_to_descriptor(
    raw: Any,
    signal: str = "GENERIC",
    text: str | None = None,
    features: dict | None = None,
    domain: str | None = None,
) -> PatternDescriptor:
    """
    Normalize raw detector outputs into a PatternDescriptor.
    Supports dicts, strings, enums, dataclasses, semantic predictions, and lists.
    """

    # Already normalized
    if isinstance(raw, PatternDescriptor):
        return raw

    # ---------- string (used by regex/exact) ----------
    if isinstance(raw, str):
        return PatternDescriptor(
            type=raw,
            signals=[signal],
            confidence=1.0 if signal in {"EXACT", "REGEX"} else 0.0,
            features={"text": text or ""},
            domain_hint=domain or "GENERIC",
        )

    # ---------- dicts ----------
    if isinstance(raw, dict):
        return PatternDescriptor(
            type=raw.get("type") or raw.get("class") or raw.get("label") or "UNKNOWN",
            signals=[signal],
            confidence=raw.get("confidence", raw.get("score", 0.0)),
            features=raw.get("features", {"text": text} if text else {}),
            style=raw.get("style"),
            layout_group=raw.get("layout_group"),
            domain_hint=raw.get("domain_hint", domain or "GENERIC"),
        )

    # ---------- exact/regex lists of strings ----------
    if isinstance(raw, list) and raw and all(isinstance(r, str) for r in raw):
        best = raw[0]  # or apply a better scoring heuristic
        return coerce_to_descriptor(best, signal=signal, text=text, features=features, domain=domain)

    # ---------- heuristic dataclasses ----------
    if isinstance(raw, ParagraphDetection):
        return PatternDescriptor(
            type=raw.label,
            signals=[signal],
            confidence=raw.score,
            features={"text": text or "", "line_idx": raw.line_idx, "method": raw.method},
            domain_hint=domain or "GENERIC",
        )
    if isinstance(raw, HeadingDetection):
        return PatternDescriptor(
            type=raw.label,
            signals=[signal],
            confidence=raw.score,
            features={"text": text or "", "line_idx": raw.line_idx},
            domain_hint=domain or "GENERIC",
        )
    if isinstance(raw, ListDetection):
        return PatternDescriptor(
            type=raw.label,
            signals=[signal],
            confidence=raw.score,
            features={"text": text or "", "line_idx": raw.line_idx},
            domain_hint=domain or "GENERIC",
        )
    if isinstance(raw, TableDetection):
        return PatternDescriptor(
            type=raw.label,
            signals=[signal],
            confidence=raw.score,
            features={"text": text or "", "line_idx": raw.line_idx},
            domain_hint=domain or "GENERIC",
        )
    if isinstance(raw, CalloutDetection):
        return PatternDescriptor(
            type=raw.label,
            signals=[signal],
            confidence=raw.score,
            features={"text": text or "", "line_idx": raw.line_idx},
            domain_hint=domain or "GENERIC",
        )

    # ---------- semantic ----------
    if isinstance(raw, SemanticPrediction):
        return PatternDescriptor(
            type=raw.label if hasattr(raw, "label") else "P-BODY",
            signals=["SEMANTIC"],
            confidence=raw.score,
            features={"title": getattr(raw, "title", None)},
            style={"pStyle": "Normal"},
            domain_hint=domain or "GENERIC",
        )

    if isinstance(raw, list) and raw:
        # Handle list of SemanticPrediction or Detection dataclasses
        if all(isinstance(p, SemanticPrediction) for p in raw):
            best = max(raw, key=lambda p: p.score)
            return coerce_to_descriptor(best, signal="SEMANTIC", text=text, features=features, domain=domain)
        if all(isinstance(p, (ParagraphDetection, HeadingDetection, ListDetection, TableDetection, CalloutDetection)) for p in raw):
            best = max(raw, key=lambda p: getattr(p, "score", 0.0))
            return coerce_to_descriptor(best, signal=signal, text=text, features=features, domain=domain)

    # ---------- enums ----------
    if isinstance(raw, HeadingForm):
        return PatternDescriptor(
            type=raw.value,
            signals=[signal],
            confidence=0.9,
            style={"pStyle": "Heading1"},
            domain_hint=domain or "GENERIC",
        )
    if isinstance(raw, ParagraphForm):
        return PatternDescriptor(
            type=raw.value,
            signals=[signal],
            confidence=0.8,
            style={"pStyle": "Normal"},
            domain_hint=domain or "GENERIC",
        )
    
    if isinstance(raw, RegexDetection):
        return PatternDescriptor(
            type=raw.label,
            signals=[signal],
            confidence=raw.score,
            features={"text": raw.title, "pattern": raw.pattern},
            domain_hint=domain or "GENERIC",
            method=raw.method,
        )



    # ---------- fallback ----------
    return PatternDescriptor(
        type="UNKNOWN",
        signals=[signal],
        confidence=0.0,
        features={"text": text or str(raw)},
        domain_hint=domain or "GENERIC",
    )
