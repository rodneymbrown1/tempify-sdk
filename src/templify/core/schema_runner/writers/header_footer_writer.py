# src/templify/core/schema_runner/writers/header_footer_writer.py

from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH


class HeaderFooterWriter:
    """
    Handles writing headers and footers into the document.
    Schema format:
    {
      "id": "hdr_1",
      "scope": "default",  # default, first_page, even_page
      "location": "header",  # or "footer"
      "style": {
        "style_id": "Header",
        "font": {"name": "Arial", "size": 10, "italic": true},
        "paragraph": {"alignment": "center"}
      },
      "text": "Confidential Resume"
    }
    """

    def __init__(self, document):
        self.doc = document

    def write(self, descriptor: dict, style: dict = None):
        """
        Write a header or footer based on schema descriptor.
        :param descriptor: schema["headers"][i] or schema["footers"][i]
        :param style: optional override style dict
        """
        location = descriptor.get("location", "header")  # header or footer
        scope = descriptor.get("scope", "default")
        text = descriptor.get("text", "")

        # For now, apply to the first section (most resumes are single-section docs)
        section = self.doc.sections[0]
        container = section.header if location.lower() == "header" else section.footer

        # Add paragraph
        p = container.add_paragraph(text)

        # Merge style (descriptor + override)
        merged_style = dict(descriptor.get("style", {}))
        if style:
            merged_style.update(style)

        # Apply style_id if valid
        if "style_id" in merged_style:
            valid_names = [s.name for s in self.doc.styles]
            if merged_style["style_id"] in valid_names:
                p.style = merged_style["style_id"]

        # Font overrides
        if "font" in merged_style:
            run = p.runs[0] if p.runs else p.add_run()
            font = merged_style["font"]
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
                run.font.color.rgb = font["color"]

        # Paragraph properties
        if "paragraph" in merged_style and "alignment" in merged_style["paragraph"]:
            align = merged_style["paragraph"]["alignment"].lower()
            if align == "left":
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            elif align == "center":
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif align == "right":
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            elif align == "justify":
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        return p
    
#     ⚠️ Limitations (python-docx):

# You can’t set "scope": "first_page" or "even_page" directly without editing section properties. python-docx has partial support, but most resumes only need "default".

# If you want page numbers (Page 1 of X), that requires a field code (XML injection).
