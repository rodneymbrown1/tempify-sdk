# src/templify/core/schema_runner/writers/theme_writer.py

from docx.shared import Pt

# src/templify/core/schema_runner/writers/theme_writer.py

from docx.shared import Pt, RGBColor

class ThemeWriter:
    """
    Handles applying document-wide theme settings by flattening theme palette
    colors into explicit RGB values on known styles.
    
    Schema format:
    {
      "fonts": {
        "major": "Calibri Light",
        "minor": "Calibri"
      },
      "colors": {
        "dk1": "000000",
        "lt1": "FFFFFF",
        "dk2": "454545",
        "lt2": "E0E0E0",
        "accent1": "F81B02",
        "accent2": "FC7715",
        "accent3": "AFBF41",
        "accent4": "50C49F",
        "accent5": "3B95C4",
        "accent6": "B560D4",
        "hlink": "FC5A1A",
        "folHlink": "B49E74"
      },
      "defaults": {
        "font": {"name": "Arial", "size": 11},
        "paragraph": {"alignment": "left"}
      }
    }
    """

    def __init__(self, document):
        self.doc = document

    def _apply_color_to_style(self, style_name: str, hex_color: str):
        """Apply RGB color to the font of a named style (if exists)."""
        if style_name in [s.name for s in self.doc.styles]:
            try:
                self.doc.styles[style_name].font.color.rgb = RGBColor.from_string(hex_color)
            except Exception:
                pass  # fallback, ignore bad hex strings

    def write(self, descriptor: dict, style: dict = None):
        merged_theme = dict(descriptor)
        if style:
            merged_theme.update(style)

        colors = merged_theme.get("colors", {})
        fonts = merged_theme.get("fonts", {})
        defaults = merged_theme.get("defaults", {})

        # 1. Apply default font to Normal style
        if "Normal" in [s.name for s in self.doc.styles]:
            normal_style = self.doc.styles["Normal"]
            font_defaults = defaults.get("font", {})
            if "name" in font_defaults:
                normal_style.font.name = font_defaults["name"]
            if "size" in font_defaults:
                normal_style.font.size = Pt(font_defaults["size"])

        # 2. Map theme colors to common Word styles
        # (user can expand this mapping as needed)
        color_map = {
            "dk1": ["Normal"],  # body text
            "lt1": ["Heading 1"],  # heading base
            "dk2": ["Heading 2"],
            "lt2": ["Heading 3"],
            "accent1": ["Heading 4"],
            "accent2": ["Heading 5"],
            "accent3": ["Heading 6"],
            "accent4": ["Heading 7"],
            "accent5": ["Heading 8"],
            "accent6": ["Heading 9"],
            "hlink": ["Hyperlink"],
            "folHlink": ["FollowedHyperlink"],
        }

        for theme_key, style_names in color_map.items():
            if theme_key in colors:
                for style_name in style_names:
                    self._apply_color_to_style(style_name, colors[theme_key])

        # 3. Store theme metadata for reference/export
        self.doc._templify_theme = {
            "fonts": fonts,
            "colors": colors,
        }

        return self.doc._templify_theme
