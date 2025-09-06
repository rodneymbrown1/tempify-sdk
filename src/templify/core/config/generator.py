# src/templify/core/config/generator.py

import re

class ConfigGenerator:
    """
    Generates JSON configs from parsed DOCX content.

    Produces:
      - titles_config: rules for detecting section titles
      - main_config: layout groups, styles, and elements
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
    ):
        self.extracted_titles = extracted_titles
        self.layout_groups = layout_groups or []
        self.lists = lists or []
        self.images = images or []
        self.hyperlinks = hyperlinks or []
        self.headers = headers or []
        self.footers = footers or []

    # ------------------------------
    # Titles config
    # ------------------------------
    def build_titles_config(self):
        config = {"titles": []}

        for t in self.extracted_titles:
            config["titles"].append(
                {
                    "title": t["title"],
                    "layout_group": t["layout_group"],
                    "section_type": t["section_type"],
                    "title_detection": {
                        "pattern": re.escape(t["title"]),
                        "case_sensitive": False,
                    },
                }
            )

        return config

    # ------------------------------
    # Main config
    # ------------------------------
    def build_main_config(self):
        group_map = {g["group"]: g for g in self.layout_groups}

        for t in self.extracted_titles:
            group_name = t["layout_group"]
            style = t.get("style", {})

            # Prepare font and paragraph style info
            font = {}
            paragraph = {}
            docx_style = style.get("pStyle")

            if "font_size" in style:
                font["size"] = style["font_size"]
            if "bold" in style:
                font["bold"] = style["bold"]
            if "italic" in style:
                font["italic"] = style["italic"]
            if "underline" in style:
                font["underline"] = style["underline"]
            if "color" in style:
                font["color"] = style["color"]
            if "name" in style:
                font["name"] = style["name"]

            if "alignment" in style:
                paragraph["alignment"] = style["alignment"]
            if (
                "spacing_before" in style
                or "spacing_after" in style
                or "indentation" in style
            ):
                paragraph["spacing_before"] = style.get("spacing_before", 0)
                paragraph["spacing_after"] = style.get("spacing_after", 0)
                paragraph["indentation"] = style.get(
                    "indentation", {"left": 0, "right": 0, "first_line": 0}
                )

            if "list_type" in style:
                paragraph["list_type"] = style["list_type"]

            # If the group is not yet defined, create it
            if group_name not in group_map:
                group_map[group_name] = {
                    "group": group_name,
                    "layout": {},
                    "section_types": [],
                    "elements": [],
                }

            entry = {
                "section_type": t["section_type"],
                "title_detection": {
                    "pattern": re.escape(t["title"]),
                    "case_sensitive": False,
                },
                "style": docx_style,
                "font": font,
                "paragraph": paragraph,
            }

            group_map[group_name].setdefault("section_types", []).append(entry)

        # Normalize new elements into each group
        for g in group_map.values():
            g.setdefault("elements", [])

        # Add lists
        for l in self.lists:
            group_name = l.get("layout_group", "group0")
            group_map[group_name]["elements"].append(
                {
                    "type": "list",
                    "text": l["text"],
                    "list_info": l.get("list_info"),
                    "list_type": l.get("list_type", "bullet"),
                }
            )

        # Add images
        for img in self.images:
            group_name = img.get("layout_group", "group0")
            group_map[group_name]["elements"].append(
                {"type": "image", "xml": img["xml"]}
            )

        # Add hyperlinks
        for link in self.hyperlinks:
            group_name = link.get("layout_group", "group0")
            group_map[group_name]["elements"].append(
                {
                    "type": "hyperlink",
                    "display_text": link["display_text"],
                    "rId": link.get("rId"),
                }
            )

        # Add headers/footers
        for g in group_map.values():
            g.setdefault("header", None)
            g.setdefault("footer", None)

        if self.headers:
            for idx, h in enumerate(self.headers):
                target_group = f"group{idx}" if f"group{idx}" in group_map else "group0"
                group_map[target_group]["header"] = {
                    "file": h["file"],
                    "text": h["text"],
                }

        if self.footers:
            for idx, f in enumerate(self.footers):
                target_group = f"group{idx}" if f"group{idx}" in group_map else "group0"
                group_map[target_group]["footer"] = {
                    "file": f["file"],
                    "text": f["text"],
                }

        return {
            "global_defaults": {
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
            },
            "layout_groups": list(group_map.values()),
        }
