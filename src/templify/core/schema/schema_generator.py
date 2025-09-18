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
        *,
        styles: Dict[str, Any] | None = None,
        tables: List[Dict[str, Any]] | None = None,
        numbering: Dict[str, Any] | None = None,
        headers: List[Dict[str, Any]] | None = None,
        footers: List[Dict[str, Any]] | None = None,
        theme: Dict[str, Any] | None = None,
        hyperlinks: List[Dict[str, Any]] | None = None,
        images: List[Dict[str, Any]] | None = None,
        bookmarks: List[Dict[str, Any]] | None = None,
        inline_formatting: List[Dict[str, Any]] | None = None,
        metadata: Dict[str, Any] | None = None,
        pattern_descriptors: List[Dict[str, Any]] | None = None,
        source_docx: str | None = None, 
    ):
        self.sections = sections
        self.layout_groups = layout_groups
        self.global_defaults = global_defaults
        self.styles = styles or {}
        self.tables = tables or []
        self.numbering = numbering or {}
        self.headers = headers or []
        self.footers = footers or []
        self.theme = theme or {}
        self.hyperlinks = hyperlinks or []
        self.images = images or []
        self.bookmarks = bookmarks or []
        self.inline_formatting = inline_formatting or []
        self.metadata = metadata or {}
        self.pattern_descriptors = pattern_descriptors or []
        self.source_docx = source_docx

    def generate(self) -> Dict[str, Any]:
        return {
            # "sections": [s.to_dict() for s in self.sections],
            "layout_groups": self.layout_groups,
            "global_defaults": self.global_defaults,
            # "styles": self.styles,
            # "tables": self.tables,
            # "numbering": self.numbering,
            "headers": self.headers,
            "footers": self.footers,
            "theme": self.theme,
            # "hyperlinks": self.hyperlinks,
            "images": self.images,
            # "bookmarks": self.bookmarks,
            # "inline_formatting": self.inline_formatting,
            # "metadata": self.metadata,
            "pattern_descriptors": self.pattern_descriptors,
            "source_docx": self.source_docx, 
        }
