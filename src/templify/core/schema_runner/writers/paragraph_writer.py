# src/templify/core/schema_runner/writers/paragraph_writer.py

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor


class ParagraphWriter:
    """
    Handles writing headings and body paragraphs into the document.
    Applies style_id if available, then font overrides, then paragraph alignment.
    """

    def __init__(self, document):
        self.doc = document

    def write(self, descriptor: dict, style: dict):
        """
        Write a paragraph for the given descriptor and style.

        :param descriptor: pattern_descriptor dict from schema
        :param style: merged style dict from style_resolver
        """
        text = descriptor.get("features", {}).get("clean_text") or descriptor.get("features", {}).get("text") or ""

        # Add paragraph
        p = self.doc.add_paragraph(text)

        # Apply style_id if valid
        if "style_id" in style:
            valid_names = [s.name for s in self.doc.styles]
            if style["style_id"] in valid_names:
                p.style = style["style_id"]

        # Font overrides
        if "font" in style:
            run = p.runs[0] if p.runs else p.add_run()
            font = style["font"]
            if "name" in font:
                run.font.name = font["name"]
            if "size" in font and font["size"]:
                run.font.size = Pt(font["size"])
            if "bold" in font:
                run.font.bold = font["bold"]
            if "italic" in font:
                run.font.italic = font["italic"]
            if "underline" in font:
                run.font.underline = font["underline"]
            if "color" in font and font["color"]:
                color_val = font["color"]
                if isinstance(color_val, str):
                    # accept "FF0000" or "#FF0000"
                    hex_str = color_val.lstrip("#")
                    run.font.color.rgb = RGBColor.from_string(hex_str)
                elif isinstance(color_val, RGBColor):
                    run.font.color.rgb = color_val

        # Paragraph properties
        if "paragraph" in style:
            para = style["paragraph"]
            if "alignment" in para:
                align = para["alignment"].lower()
                if align == "left":
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                elif align == "center":
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                elif align == "right":
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                elif align == "justify":
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        return p
