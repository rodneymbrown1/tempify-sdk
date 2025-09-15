# src/templify/core/schema/utils/mappers/docx_sections_mapper.py
import os
import xml.etree.ElementTree as ET
from typing import List, Dict, Any


class DocxSectionsMapper:
    """
    Collects section definitions (layouts) from document.xml.
    Extracts page size, margins, orientation, columns, and header/footer refs.
    """

    def __init__(self, document_xml_path: str):
        if not os.path.exists(document_xml_path):
            raise FileNotFoundError(f"document.xml not found: {document_xml_path}")
        with open(document_xml_path, "r", encoding="utf-8") as f:
            self.tree = ET.parse(f)
        self.nsmap = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    def collect_sections(self) -> List[Dict[str, Any]]:
        sections = []
        for sectPr in self.tree.findall(".//w:sectPr", namespaces=self.nsmap):
            section_data: Dict[str, Any] = {}

            # Page size
            pgSz = sectPr.find("w:pgSz", namespaces=self.nsmap)
            if pgSz is not None:
                section_data["page_size"] = {
                    "width": pgSz.attrib.get(f"{{{self.nsmap['w']}}}w"),
                    "height": pgSz.attrib.get(f"{{{self.nsmap['w']}}}h"),
                    "orientation": pgSz.attrib.get(f"{{{self.nsmap['w']}}}orient", "portrait"),
                }

            # Margins
            pgMar = sectPr.find("w:pgMar", namespaces=self.nsmap)
            if pgMar is not None:
                section_data["margins"] = {
                    "top": pgMar.attrib.get(f"{{{self.nsmap['w']}}}top"),
                    "bottom": pgMar.attrib.get(f"{{{self.nsmap['w']}}}bottom"),
                    "left": pgMar.attrib.get(f"{{{self.nsmap['w']}}}left"),
                    "right": pgMar.attrib.get(f"{{{self.nsmap['w']}}}right"),
                }

            # Columns
            cols = sectPr.find("w:cols", namespaces=self.nsmap)
            if cols is not None:
                section_data["columns"] = {
                    "num": cols.attrib.get(f"{{{self.nsmap['w']}}}num", "1"),
                    "space": cols.attrib.get(f"{{{self.nsmap['w']}}}space", "0"),
                }

            # Header/Footer references
            header_refs = []
            for hdr in sectPr.findall("w:headerReference", namespaces=self.nsmap):
                header_refs.append({
                    "type": hdr.attrib.get(f"{{{self.nsmap['w']}}}type"),
                    "rId": hdr.attrib.get(f"{{http://schemas.openxmlformats.org/officeDocument/2006/relationships}}id"),
                })
            if header_refs:
                section_data["header_refs"] = header_refs

            footer_refs = []
            for ftr in sectPr.findall("w:footerReference", namespaces=self.nsmap):
                footer_refs.append({
                    "type": ftr.attrib.get(f"{{{self.nsmap['w']}}}type"),
                    "rId": ftr.attrib.get(f"{{http://schemas.openxmlformats.org/officeDocument/2006/relationships}}id"),
                })
            if footer_refs:
                section_data["footer_refs"] = footer_refs

            sections.append(section_data)

        return sections
