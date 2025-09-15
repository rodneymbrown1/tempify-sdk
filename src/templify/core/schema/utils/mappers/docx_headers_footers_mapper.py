# src/templify/core/schema/utils/mappers/docx_headers_footers_mapper.py
import os
import xml.etree.ElementTree as ET
from typing import Dict, Any, List


class DocxHeadersFootersMapper:
    """
    Collects headers and footers from a DOCX package.
    Resolves sectPr -> rels -> header/footer XML content.
    """

    def __init__(self, docx_extract_dir: str):
        if not os.path.exists(docx_extract_dir):
            raise FileNotFoundError(f"docx_extract_dir not found: {docx_extract_dir}")

        self.docx_extract_dir = docx_extract_dir
        self.nsmap = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        self.rns = "http://schemas.openxmlformats.org/package/2006/relationships"

        # Build rels map (rId -> target file)
        rels_path = os.path.join(docx_extract_dir, "word", "_rels", "document.xml.rels")
        self.rels_map: Dict[str, str] = {}
        if os.path.exists(rels_path):
            rels_tree = ET.parse(rels_path).getroot()
            for rel in rels_tree.findall(f".//{{{self.rns}}}Relationship"):
                self.rels_map[rel.attrib.get("Id")] = rel.attrib.get("Target")

    def collect_headers_footers(self) -> Dict[str, List[Dict[str, Any]]]:
        results = {"headers": [], "footers": []}

        # Walk all referenced header/footer XML files
        for r_id, target in self.rels_map.items():
            if not target.endswith((".xml")):
                continue
            path = os.path.join(self.docx_extract_dir, "word", target)
            if not os.path.exists(path):
                continue

            tree = ET.parse(path).getroot()
            texts = [
                t.text
                for t in tree.findall(".//w:t", namespaces=self.nsmap)
                if t.text
            ]
            content = " ".join(texts).strip()

            if "header" in target:
                results["headers"].append({
                    "file": target,
                    "rId": r_id,
                    "text": content
                })
            elif "footer" in target:
                results["footers"].append({
                    "file": target,
                    "rId": r_id,
                    "text": content
                })

        return results
