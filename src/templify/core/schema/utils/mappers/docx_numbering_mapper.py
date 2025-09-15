# src/templify/core/schema/utils/mappers/docx_numbering_mapper.py
import os
import xml.etree.ElementTree as ET
from typing import Dict, Any


class DocxNumberingMapper:
    """
    Collects list numbering definitions from numbering.xml.
    Resolves numId -> abstractNum -> level formatting.
    """

    def __init__(self, numbering_xml_path: str):
        if not os.path.exists(numbering_xml_path):
            raise FileNotFoundError(f"numbering.xml not found: {numbering_xml_path}")
        with open(numbering_xml_path, "r", encoding="utf-8") as f:
            self.tree = ET.parse(f)
        self.nsmap = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

        # Will hold mapping results
        self.abstract_nums: Dict[str, Any] = {}
        self.nums: Dict[str, Any] = {}

    def collect_numbering(self) -> Dict[str, Any]:
        """Parse abstractNum and num definitions into a structured dict."""
        root = self.tree.getroot()

        # 1. Parse abstractNum definitions
        for abstract in root.findall("w:abstractNum", namespaces=self.nsmap):
            abs_id = abstract.attrib.get(f"{{{self.nsmap['w']}}}abstractNumId")
            levels = {}
            for lvl in abstract.findall("w:lvl", namespaces=self.nsmap):
                ilvl = lvl.attrib.get(f"{{{self.nsmap['w']}}}ilvl")
                numFmt = lvl.find("w:numFmt", namespaces=self.nsmap)
                lvlText = lvl.find("w:lvlText", namespaces=self.nsmap)
                start = lvl.find("w:start", namespaces=self.nsmap)

                levels[ilvl] = {
                    "format": numFmt.attrib.get(f"{{{self.nsmap['w']}}}val") if numFmt is not None else None,
                    "text": lvlText.attrib.get(f"{{{self.nsmap['w']}}}val") if lvlText is not None else None,
                    "start": start.attrib.get(f"{{{self.nsmap['w']}}}val") if start is not None else "1",
                }
            self.abstract_nums[abs_id] = {"levels": levels}

        # 2. Parse num (links numId -> abstractNumId)
        for num in root.findall("w:num", namespaces=self.nsmap):
            num_id = num.attrib.get(f"{{{self.nsmap['w']}}}numId")
            abs_elem = num.find("w:abstractNumId", namespaces=self.nsmap)
            abs_id = abs_elem.attrib.get(f"{{{self.nsmap['w']}}}val") if abs_elem is not None else None
            self.nums[num_id] = {"abstractNumId": abs_id}

        return {
            "abstractNums": self.abstract_nums,
            "nums": self.nums,
        }

    def resolve_level(self, num_id: str, ilvl: str) -> Dict[str, Any]:
        """
        Given a numId + ilvl (from document.xml), return the resolved numbering style.
        """
        num_def = self.nums.get(num_id)
        if not num_def:
            return {}
        abs_id = num_def.get("abstractNumId")
        abs_def = self.abstract_nums.get(abs_id)
        if not abs_def:
            return {}
        return abs_def["levels"].get(ilvl, {})
