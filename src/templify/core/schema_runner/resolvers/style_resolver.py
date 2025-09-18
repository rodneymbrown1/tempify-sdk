# src/templify/core/schema_runner/resolvers/style_resolver.py
from typing import Any, Dict
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two dicts.
    Values in override take precedence over base.
    """
    merged = dict(base)  # copy
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged


def resolve_style(
    descriptor_type: str,
    schema: Dict[str, Any],
    global_defaults: Dict[str, Any],
    docx_styles,
) -> Dict[str, Any]:
    """
    Resolve style precedence:
    1. style_id from schema/descriptor (if present)
    2. schema/descriptor properties (font, paragraph, etc.)
    3. global defaults (fallbacks for missing keys)
    """
    schema_style = {}
    for pat in schema.get("pattern_descriptors", []):
        if pat.get("type") == descriptor_type:
            schema_style = pat.get("style", {})
            break

    merged: Dict[str, Any] = {}

    # --- Step 1: style_id (if present)
    if "style_id" in schema_style:
        merged["style_id"] = schema_style["style_id"]

    # --- Step 2: merge schema style with defaults (per-key deep merge)
    merged["font"] = deep_merge(global_defaults.get("font", {}), schema_style.get("font", {}))
    merged["paragraph"] = deep_merge(global_defaults.get("paragraph", {}), schema_style.get("paragraph", {}))

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
