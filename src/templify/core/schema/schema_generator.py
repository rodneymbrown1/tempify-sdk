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
    """
    Assembles the final Templify schema JSON.

    Input:
      - sections (tree of Section objects)
      - layout_groups (list of group dicts)
      - global_defaults (dict)

    Output:
      - JSON-compatible dict matching skeleton config spec
    """

    def __init__(
        self,
        sections: List[Section],
        layout_groups: List[Dict[str, Any]],
        global_defaults: Dict[str, Any],
    ):
        self.sections = sections
        self.layout_groups = layout_groups
        self.global_defaults = global_defaults

    def generate(self) -> Dict[str, Any]:
        """Produce the skeleton schema."""
        return {
            "sections": [s.to_dict() for s in self.sections],
            "layout_groups": self.layout_groups,
            "global_defaults": self.global_defaults,
        }
