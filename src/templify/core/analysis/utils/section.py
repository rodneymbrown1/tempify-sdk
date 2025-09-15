from __future__ import annotations
from typing import List, Optional
from templify.core.analysis.utils.pattern_descriptor import PatternDescriptor
from templify.core.analysis.detectors.heuristics.heading_detector import HeadingDetection


class Section:
    def __init__(
        self,
        title: str,
        level: int,
        *,
        paragraph_id: Optional[str] = None,
        pattern_ref: Optional[str] = None,
        style_ref: Optional[str] = None,
        layout_group: Optional[str] = None,
        children: Optional[list["Section"]] = None,
    ):
        self.id = paragraph_id or f"p_{id(self)}"
        self.title = title
        self.level = level
        self.pattern_ref = pattern_ref
        self.style_ref = style_ref
        self.layout_group = layout_group
        self.children: list[Section] = children or []

    @classmethod
    def from_heading(
        cls,
        det: HeadingDetection,
        desc: PatternDescriptor,
        *,
        layout_group: str | None = None,
    ) -> "Section":
        """Factory: build Section from a HeadingDetection + PatternDescriptor."""
        return cls(
            title=det.clean_text or desc.text,
            level=det.level or desc.features.get("level", 1),
            paragraph_id=desc.paragraph_id,
            pattern_ref=desc.id,
            style_ref=desc.style.get("style_id") if desc.style else None,
            layout_group=layout_group,
        )

    def add_subsection(self, subsection: "Section"):
        """Attach a subsection to this section."""
        self.children.append(subsection)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "level": self.level,
            "pattern_ref": self.pattern_ref,
            "style_ref": self.style_ref,
            "layout_group": self.layout_group,
            "children": [c.to_dict() for c in self.children],
        }
