# src/templify/core/schema/utils/mappers/docx_themes_mapper.py
import os
import xml.etree.ElementTree as ET
from typing import Dict, Any


class DocxThemesMapper:
    """
    Collects theme definitions (colors, fonts) from theme/theme1.xml.
    Useful for resolving themeColor/themeFont references in styles.
    """

    def __init__(self, theme_xml_path: str):
        if not os.path.exists(theme_xml_path):
            raise FileNotFoundError(f"theme1.xml not found: {theme_xml_path}")
        with open(theme_xml_path, "r", encoding="utf-8") as f:
            self.tree = ET.parse(f)
        self.nsmap = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}

    def collect_theme(self) -> Dict[str, Any]:
        root = self.tree.getroot()
        theme_data: Dict[str, Any] = {"colors": {}, "fonts": {}}

        # Parse color scheme
        clrScheme = root.find(".//a:clrScheme", namespaces=self.nsmap)
        if clrScheme is not None:
            for child in clrScheme:
                tag = child.tag.split("}")[1]  # e.g. dk1, lt1, accent1
                color_elem = list(child)[0] if len(child) else None
                if color_elem is not None:
                    if "srgbClr" in color_elem.tag:
                        val = color_elem.attrib.get("val")
                    elif "sysClr" in color_elem.tag:
                        val = color_elem.attrib.get("lastClr")
                    else:
                        val = None
                    theme_data["colors"][tag] = val

        # Parse font scheme
        fontScheme = root.find(".//a:fontScheme", namespaces=self.nsmap)
        if fontScheme is not None:
            major = fontScheme.find("a:majorFont/a:latin", namespaces=self.nsmap)
            minor = fontScheme.find("a:minorFont/a:latin", namespaces=self.nsmap)
            theme_data["fonts"]["major"] = major.attrib.get("typeface") if major is not None else None
            theme_data["fonts"]["minor"] = minor.attrib.get("typeface") if minor is not None else None

        return theme_data
