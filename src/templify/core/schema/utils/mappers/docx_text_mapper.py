# src/templify/core/schema/utils/mappers/docx_text_mapper.py
import xml.etree.ElementTree as ET
from typing import Dict, Any, List

class DocxTextMapper:
    def __init__(self, nsmap: Dict[str, str], styles: Dict[str, Any], defaults: Dict[str, Any]):
        self.nsmap = nsmap
        self.styles = styles
        self.defaults = defaults

    def extract_paragraphs(self, body: ET.Element) -> List[Dict[str, Any]]:
        """Return list of dicts (text + style + para_id) for each paragraph in <w:body>."""
        paragraphs = []
        for p in body.findall("w:p", namespaces=self.nsmap):
            text = self._get_text(p)
            style = self._resolve_style(p)
            para_id = p.attrib.get("{http://schemas.microsoft.com/office/word/2010/wordml}paraId")
            paragraphs.append({
                "text": text,
                "style": style,
                "paragraph_id": para_id,
                "p_elem": p  # keep original element if needed downstream
            })
        return paragraphs

    def _get_text(self, p: ET.Element) -> str:
        return " ".join(t.text for t in p.findall(".//w:t", namespaces=self.nsmap) if t.text)

    def _resolve_style(self, p: ET.Element) -> Dict[str, Any]:
        style: Dict[str, Any] = {}

        # paragraph props
        pPr = p.find("w:pPr", namespaces=self.nsmap)
        if pPr is not None:
            style_elem = pPr.find("w:pStyle", namespaces=self.nsmap)
            if style_elem is not None:
                style_id = style_elem.attrib.get(f"{{{self.nsmap['w']}}}val")
                style["style_id"] = style_id
                if style_id and style_id in self.styles.get("paragraphs", {}):
                    style.update(self.styles["paragraphs"][style_id])

            jc = pPr.find("w:jc", namespaces=self.nsmap)
            if jc is not None:
                style.setdefault("paragraph", {})["alignment"] = jc.attrib.get(f"{{{self.nsmap['w']}}}val")

        # run props
        for r in p.findall(".//w:r", namespaces=self.nsmap):
            rPr = r.find("w:rPr", namespaces=self.nsmap)
            if rPr is not None:
                self._merge_run_properties(style, rPr)

        return style

    def _merge_run_properties(self, style: Dict[str, Any], rPr: ET.Element):
        font = style.setdefault("font", {})
        if rPr.find("w:b", namespaces=self.nsmap) is not None:
            font["bold"] = True
        if rPr.find("w:i", namespaces=self.nsmap) is not None:
            font["italic"] = True
        if rPr.find("w:u", namespaces=self.nsmap) is not None:
            font["underline"] = True
        if rPr.find("w:strike", namespaces=self.nsmap) is not None:
            font["strike"] = True
        if rPr.find("w:caps", namespaces=self.nsmap) is not None:
            font["all_caps"] = True
        if rPr.find("w:smallCaps", namespaces=self.nsmap) is not None:
            font["small_caps"] = True

        rFonts = rPr.find("w:rFonts", namespaces=self.nsmap)
        if rFonts is not None:
            ascii_font = rFonts.attrib.get(f"{{{self.nsmap['w']}}}ascii")
            if ascii_font:
                font["name"] = ascii_font

        sz = rPr.find("w:sz", namespaces=self.nsmap)
        if sz is not None:
            font["size"] = int(sz.attrib.get(f"{{{self.nsmap['w']}}}val")) // 2

        color = rPr.find("w:color", namespaces=self.nsmap)
        if color is not None:
            font["color"] = color.attrib.get(f"{{{self.nsmap['w']}}}val")

        highlight = rPr.find("w:highlight", namespaces=self.nsmap)
        if highlight is not None:
            font["highlight"] = highlight.attrib.get(f"{{{self.nsmap['w']}}}val")
