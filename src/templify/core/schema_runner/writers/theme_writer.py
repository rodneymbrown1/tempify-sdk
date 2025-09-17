# src/templify/core/schema_runner/writers/theme_writer.py

from docx.shared import Pt


class ThemeWriter:
    """
    Handles applying document-wide theme settings.
    Schema format:
    {
      "fonts": {
        "major": "Calibri Light",
        "minor": "Calibri"
      },
      "colors": {
        "accent1": "4472C4",
        "accent2": "ED7D31"
      },
      "defaults": {
        "font": {"name": "Arial", "size": 11},
        "paragraph": {"alignment": "left"}
      }
    }
    """

    def __init__(self, document):
        self.doc = document

    def write(self, descriptor: dict, style: dict = None):
        """
        Apply theme settings to the document.
        NOTE: python-docx has limited support for full theme editing,
              so this writer applies font defaults and records colors.
        :param descriptor: schema["themes"]
        :param style: optional style override dict
        """
        merged_theme = dict(descriptor)
        if style:
            merged_theme.update(style)

        # Apply font defaults to "Normal" style
        defaults = merged_theme.get("defaults", {})
        font_defaults = defaults.get("font", {})

        if "Normal" in [s.name for s in self.doc.styles]:
            normal_style = self.doc.styles["Normal"]

            if "name" in font_defaults:
                normal_style.font.name = font_defaults["name"]
            if "size" in font_defaults and font_defaults["size"]:
                normal_style.font.size = Pt(font_defaults["size"])
            if "bold" in font_defaults:
                normal_style.font.bold = font_defaults["bold"]
            if "italic" in font_defaults:
                normal_style.font.italic = font_defaults["italic"]

        # Save fonts/colors into docx custom properties (not natively supported)
        # You can later export these from schema instead of doc
        self.doc._templify_theme = {
            "fonts": merged_theme.get("fonts", {}),
            "colors": merged_theme.get("colors", {}),
        }

        return self.doc._templify_theme

# ⚠️ Limitations (python-docx)

# You can’t fully set a DOCX theme (accent colors, theme fonts) without raw XML injection.

# For now, we’re treating this as:

# Apply defaults to Normal style.

# Store theme metadata for reference/export.