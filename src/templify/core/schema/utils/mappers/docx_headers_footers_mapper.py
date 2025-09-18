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

    def _extract_style(self, p_elem: ET.Element) -> Dict[str, Any]:
        style: Dict[str, Any] = {}

        # Paragraph properties
        pPr = p_elem.find("w:pPr", namespaces=self.nsmap)
        if pPr is not None:
            # Style id
            pStyle = pPr.find("w:pStyle", namespaces=self.nsmap)
            if pStyle is not None:
                style["style_id"] = pStyle.attrib.get(f"{{{self.nsmap['w']}}}val")

            # Alignment
            jc = pPr.find("w:jc", namespaces=self.nsmap)
            if jc is not None:
                style.setdefault("paragraph", {})["alignment"] = jc.attrib.get(f"{{{self.nsmap['w']}}}val")

        # Run properties (first run only)
        r = p_elem.find("w:r", namespaces=self.nsmap)
        if r is not None:
            rPr = r.find("w:rPr", namespaces=self.nsmap)
            if rPr is not None:
                font: Dict[str, Any] = {}
                if rPr.find("w:b", namespaces=self.nsmap) is not None:
                    font["bold"] = True
                if rPr.find("w:i", namespaces=self.nsmap) is not None:
                    font["italic"] = True
                if rPr.find("w:u", namespaces=self.nsmap) is not None:
                    font["underline"] = True
                sz = rPr.find("w:sz", namespaces=self.nsmap)
                if sz is not None:
                    try:
                        font["size"] = int(sz.attrib.get(f"{{{self.nsmap['w']}}}val")) / 2
                    except Exception:
                        pass
                color = rPr.find("w:color", namespaces=self.nsmap)
                if color is not None:
                    font["color"] = color.attrib.get(f"{{{self.nsmap['w']}}}val")
                if font:
                    style["font"] = font

        return style

    def _extract_segments(self, p_elem: ET.Element) -> List[Dict[str, Any]]:
        """
        Extract segments from a paragraph with optional tab stops.
        Returns [{"text": str, "alignment": str}, ...].
        """
        segments: List[Dict[str, Any]] = []
        current_align = "left"  # Default alignment if no tab stops

        for child in p_elem:
            tag = child.tag.split("}")[-1]

            if tag == "sdt":  # Structured Document Tag (content control)
                t_elem = child.find(".//w:t", namespaces=self.nsmap)
                if t_elem is not None and t_elem.text:
                    segments.append({"text": t_elem.text, "alignment": current_align})

            elif tag == "r":  # Run
                t_elem = child.find("w:t", namespaces=self.nsmap)
                if t_elem is not None and t_elem.text:
                    segments.append({"text": t_elem.text, "alignment": current_align})

            elif tag == "ptab":  # Positioning tab (Word tab stop)
                align = child.attrib.get(f"{{{self.nsmap['w']}}}alignment")
                if align:
                    # normalize to templify style
                    align = align.lower()
                    if align in ("left", "center", "right", "decimal"):
                        current_align = align
                    else:
                        current_align = "left"  # fallback for unknown
                else:
                    # no explicit alignment → keep left
                    current_align = "left"

        return segments

    def collect_headers_footers(self) -> Dict[str, List[Dict[str, Any]]]:
        results = {"headers": [], "footers": []}

        for r_id, target in self.rels_map.items():
            if not target.endswith(".xml"):
                continue
            path = os.path.join(self.docx_extract_dir, "word", target)
            if not os.path.exists(path):
                continue

            tree = ET.parse(path).getroot()

            for p_elem in tree.findall(".//w:p", namespaces=self.nsmap):
                texts = [t.text for t in p_elem.findall(".//w:t", namespaces=self.nsmap) if t.text]
                raw_text = " ".join(texts).strip()

                # Inline PAGE/NUMPAGES placeholders (non-tabbed paragraphs)
                instr = p_elem.find(".//w:instrText", namespaces=self.nsmap)
                if instr is not None:
                    if "PAGE" in instr.text:
                        raw_text = "Page [i]"
                    elif "NUMPAGES" in instr.text:
                        raw_text = "of [total]"

                style = self._extract_style(p_elem)
                segments = self._extract_segments(p_elem)

                entry: Dict[str, Any] = {
                    "file": target,
                    "rId": r_id,
                    "style": style,
                }

                if segments:
                    entry["layout"] = "tabbed"
                    entry["segments"] = segments
                else:
                    entry["text"] = raw_text

                if "header" in target:
                    results["headers"].append(entry)
                elif "footer" in target:
                    results["footers"].append(entry)

        return results
