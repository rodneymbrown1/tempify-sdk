# src/templify/core/config/generator.py
import re

class ConfigGenerator:
    """
    Assemble JSON configs from parsed DOCX content.

    Produces:
      - titles_config: rules for identifying section titles
      - docx_config: layout groups, styles, and elements
    """

    def __init__(
        self,
        extracted_titles,
        layout_groups=None,
        lists=None,
        images=None,
        hyperlinks=None,
        headers=None,
        footers=None,
        patterns=None,
    ):
        self.patterns = patterns or []
        # Core extracted values
        self.extracted_titles = extracted_titles

        # Optional features, defaulting to empty lists
        self.layout_groups = layout_groups if layout_groups is not None else []
        self.lists = lists if lists is not None else []
        self.images = images if images is not None else []
        self.hyperlinks = hyperlinks if hyperlinks is not None else []
        self.headers = headers if headers is not None else []
        self.footers = footers if footers is not None else []

    # ======================================================
    # Public API
    # ======================================================

    def build(self) -> dict:
        """
        Main entrypoint.
        Returns a combined configuration payload for downstream consumers.
        """
        return {
            "titles_config": self.build_titles_config(),
            "docx_config": self.build_docx_config(),
        }

    # ======================================================
    # Titles configuration
    # ======================================================

    def build_titles_config(self):
        return {
            "titles": [
                {
                    "title": t["title"],
                    "layout_group": t["layout_group"],
                    "section_type": t["section_type"],
                    "title_detection": t.get(
                        "title_detection",
                        {"pattern": re.escape(t["title"]), "case_sensitive": False}
                    ),
                }
                for t in self.extracted_titles
            ]
        }


    # ======================================================
    # DOCX configuration
    # ======================================================

    def build_docx_config(self):
        # Start from existing groups
        group_map = {grp["group"]: dict(grp) for grp in self.layout_groups}

        # ---------- Titles ----------
        for title in self.extracted_titles:
            group_id = title["layout_group"]
            style = title.get("style", {})
            font, paragraph = self._extract_style(style)
            docx_style = style.get("pStyle")

            if group_id not in group_map:
                group_map[group_id] = {
                    "group": group_id,
                    "layout": {},
                    "section_types": [],
                    "elements": [],
                }

            group_map[group_id].setdefault("section_types", []).append(
                {
                    "section_type": title["section_type"],
                    "title_detection": {
                        "pattern": re.escape(title["title"]),
                        "case_sensitive": False,
                    },
                    "style": docx_style,
                    "font": font,
                    "paragraph": paragraph,
                }
            )

        # Ensure elements is always present
        for g in group_map.values():
            g.setdefault("elements", [])

        # ---------- Lists ----------
        for lst in self.lists:
            self._append_element(
                group_map,
                lst.get("layout_group", "group0"),
                {
                    "type": "list",
                    "text": lst["text"],
                    "list_info": lst.get("list_info"),
                    "list_type": lst.get("list_type", "bullet"),
                },
            )

        # ---------- Images ----------
        for img in self.images:
            self._append_element(
                group_map,
                img.get("layout_group", "group0"),
                {"type": "image", "xml": img["xml"]},
            )

        # ---------- Hyperlinks ----------
        for link in self.hyperlinks:
            self._append_element(
                group_map,
                link.get("layout_group", "group0"),
                {
                    "type": "hyperlink",
                    "display_text": link["display_text"],
                    "rId": link.get("rId"),
                },
            )

        # ---------- Headers / Footers ----------
        for g in group_map.values():
            g.setdefault("header", None)
            g.setdefault("footer", None)

        self._assign_headers(group_map)
        self._assign_footers(group_map)

        # ---------- Defaults ----------
        return {
        "global_defaults": self._default_config(),
        "layout_groups": list(group_map.values()),
        "patterns": [p.to_dict() if hasattr(p, "to_dict") else p for p in self.patterns],
    }

    # ======================================================
    # Helpers
    # ======================================================

    def _extract_style(self, style):
        """Split style dict into font and paragraph specs."""
        font, paragraph = {}, {}

        # Font
        for k in ("font_size", "bold", "italic", "underline", "color", "name"):
            if k in style:
                key = "size" if k == "font_size" else k
                font[key] = style[k]

        # Paragraph
        if "alignment" in style:
            paragraph["alignment"] = style["alignment"]

        if any(k in style for k in ("spacing_before", "spacing_after", "indentation")):
            paragraph["spacing_before"] = style.get("spacing_before", 0)
            paragraph["spacing_after"] = style.get("spacing_after", 0)
            paragraph["indentation"] = style.get(
                "indentation", {"left": 0, "right": 0, "first_line": 0}
            )

        if "list_type" in style:
            paragraph["list_type"] = style["list_type"]

        return font, paragraph

    def _append_element(self, group_map, group_name, element):
        """Safely attach an element into the correct group."""
        if group_name not in group_map:
            group_map[group_name] = {
                "group": group_name,
                "layout": {},
                "section_types": [],
                "elements": [],
            }
        group_map[group_name]["elements"].append(element)

    def _assign_headers(self, group_map):
        for idx, h in enumerate(self.headers):
            target = f"group{idx}" if f"group{idx}" in group_map else "group0"
            group_map[target]["header"] = {"file": h["file"], "text": h["text"]}

    def _assign_footers(self, group_map):
        for idx, f in enumerate(self.footers):
            target = f"group{idx}" if f"group{idx}" in group_map else "group0"
            group_map[target]["footer"] = {"file": f["file"], "text": f["text"]}

    def _default_config(self):
        return {
            "page_margins": {
                "top": 1440,
                "bottom": 1440,
                "left": 1440,
                "right": 1440,
                "header": 720,
                "footer": 720,
                "gutter": 0,
            },
            "page_size": {
                "width": 12240,
                "height": 15840,
                "orientation": "portrait",
            },
            "font": {
                "name": "Arial",
                "size": 16,
                "bold": False,
                "italic": False,
                "underline": False,
                "color": "000000",
            },
            "paragraph": {
                "alignment": "left",
                "spacing_before": 0,
                "spacing_after": 0,
                "indentation": {"left": 0, "right": 0, "first_line": 0},
                "list_type": None,
            },
        }
