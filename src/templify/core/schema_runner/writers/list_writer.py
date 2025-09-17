# src/templify/core/schema_runner/writers/list_writer.py

from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH


class ListWriter:
    """
    Handles writing list items (bulleted, numbered, multilevel).
    Uses schema format:
    {
      "id": "list_1",
      "list_type": "bullet",   # bullet, ordered, or custom
      "style": {"style_id": "ListBullet"},
      "items": [
        {
          "text": "First item",
          "style": {"font": {"name": "Arial", "size": 11}, "indent_level": 0}
        },
        {
          "text": "Second item",
          "style": {"indent_level": 1}
        }
      ]
    }
    """

    def __init__(self, document):
        self.doc = document

    def write(self, descriptor: dict, style: dict = None):
        """
        Write a list (bullet or ordered) using schema descriptor.
        :param descriptor: schema["lists"][i]
        :param style: optional override style dict
        """
        list_type = descriptor.get("list_type", "bullet")
        items = descriptor.get("items", [])
        list_style_id = None

        # Determine list style
        if list_type == "bullet":
            list_style_id = "ListBullet"
        elif list_type == "ordered":
            list_style_id = "ListNumber"
        elif list_type == "custom":
            list_style_id = descriptor.get("style", {}).get("style_id")

        # Write each item
        for item in items:
            text = item.get("text", "")
            p = self.doc.add_paragraph(text, style=list_style_id)

            # Apply font overrides
            if "style" in item and "font" in item["style"]:
                run = p.runs[0] if p.runs else p.add_run()
                font = item["style"]["font"]
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

            # Paragraph-level overrides (indentation, alignment)
            if "style" in item:
                if "indent_level" in item["style"]:
                    level = item["style"]["indent_level"]
                    p.paragraph_format.left_indent = Inches(0.25 * level)

                if "paragraph" in item["style"] and "alignment" in item["style"]["paragraph"]:
                    align = item["style"]["paragraph"]["alignment"].lower()
                    if align == "left":
                        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    elif align == "center":
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    elif align == "right":
                        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    elif align == "justify":
                        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        return self.doc

# ⚠️ Limitations

# True multi-level numbering (1.1, 1.2, 2.1) is not exposed in python-docx. That would require XML injection (<w:numPr>), which we can support later if needed.

# For now, indentation + ListNumber style simulates the effect well.