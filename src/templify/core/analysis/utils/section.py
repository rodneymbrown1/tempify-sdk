# src/templify/core/config/section.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from templify.core.analysis.utils.pattern_descriptor import PatternDescriptor
from templify.core.analysis.detectors.heuristics.heading_detector import HeadingDetection


@dataclass
class Section:
    """
    Represents a document section in the skeleton config.

    - `anchor`: a PatternDescriptor (usually from a HeadingDetection)
    - `body_patterns`: list of PatternDescriptors (paragraphs, lists, tables, etc.)
    - `subsections`: recursive list of Section children
    """

    section_type: str
    anchor: PatternDescriptor
    layout_group: str
    body_patterns: List[PatternDescriptor] = field(default_factory=list)
    subsections: List["Section"] = field(default_factory=list)

    def add_subsection(self, subsection: "Section"):
        """Attach a subsection to this section."""
        self.subsections.append(subsection)

    def to_dict(self) -> Dict[str, Any]:
        """Export to JSON-like dict for config output."""
        return {
            "section_type": self.section_type,
            "anchor": self.anchor.to_dict(),
            "layout_group": self.layout_group,
            "body_patterns": [bp.to_dict() for bp in self.body_patterns],
            "subsections": [s.to_dict() for s in self.subsections],
        }

    # --------- Factory helper from HeadingDetection ---------
    @classmethod
    def from_heading(
        cls,
        detection: HeadingDetection,
        anchor_desc: PatternDescriptor,
        layout_group: str,
    ) -> "Section":
        """
        Build a Section from a HeadingDetection and its normalized PatternDescriptor.
        """
        return cls(
            section_type=f"section{detection.level or 1}_{detection.numbering or ''}".strip("_"),
            anchor=anchor_desc,
            layout_group=layout_group,
            body_patterns=[],
            subsections=[],
        )
