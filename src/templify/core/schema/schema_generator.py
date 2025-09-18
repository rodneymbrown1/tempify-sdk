from __future__ import annotations
from typing import List, Dict, Any
from templify.core.analysis.utils.section import Section


def merge_styles(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge styles with precedence:
    global_defaults < layout_group < section.anchor.style < body.style
    """
    merged: Dict[str, Any] = {}
    for d in dicts:
        if not d:
            continue
        merged.update(d)
    return merged


class SchemaGenerator:
    def __init__(
        self,
        sections: List[Section],
        layout_groups: List[Dict[str, Any]],
        global_defaults: Dict[str, Any],
        pattern_descriptors: List[Dict[str, Any]] | None = None,
    ):
        self.sections = sections
        self.layout_groups = layout_groups
        self.global_defaults = global_defaults
        self.pattern_descriptors = pattern_descriptors or []

    def generate(self) -> Dict[str, Any]:
        return {
            "layout_groups": self.layout_groups,
            "global_defaults": self.global_defaults,
            "pattern_descriptors": self.pattern_descriptors,
        }
