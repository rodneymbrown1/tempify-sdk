# src/templify/core/schema_runner/style_resolver.py
from typing import Any, Dict
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

def resolve_style(
    descriptor_type: str,
    schema: Dict[str, Any],
    global_defaults: Dict[str, Any],
    docx_styles,
) -> Dict[str, Any]:
    schema_style = {}
    for pat in schema.get("pattern_descriptors", []):
        if pat.get("type") == descriptor_type:
            schema_style = pat.get("style", {})
            break

    merged: Dict[str, Any] = {}

    # Always include style_id if schema provided it
    if "style_id" in schema_style:
        merged["style_id"] = schema_style["style_id"]

    # Explicit overrides
    if "font" in schema_style:
        merged["font"] = schema_style["font"]

    if "paragraph" in schema_style:
        merged["paragraph"] = schema_style["paragraph"]

    # Fallbacks
    merged.setdefault("font", global_defaults.get("font", {}))
    merged.setdefault("paragraph", global_defaults.get("paragraph", {}))

    return merged


def apply_style_to_paragraph(paragraph, style: Dict[str, Any]):
    """
    Given a python-docx paragraph and merged style dict,
    apply styles safely.
    """
    # Style ID (if valid)
    if "style_id" in style and style["style_id"] in [s.name for s in paragraph.part.styles]:
        paragraph.style = style["style_id"]


    # Font properties
    if "font" in style:
        run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()
        font = style["font"]
        if "name" in font:
            run.font.name = font["name"]
        if "size" in font:
            run.font.size = Pt(font["size"])
        if "bold" in font:
            run.font.bold = font["bold"]

    # Paragraph properties
    if "paragraph" in style:
        para = style["paragraph"]
        if "alignment" in para:
            if para["alignment"].lower() == "left":
                paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            elif para["alignment"].lower() == "center":
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif para["alignment"].lower() == "right":
                paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
