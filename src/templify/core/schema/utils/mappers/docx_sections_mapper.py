# src/templify/core/schema/utils/mappers/docx_sections_mapper.py
import os
import xml.etree.ElementTree as ET
from typing import List, Dict, Any


class DocxSectionsMapper:
    """
    Collects section definitions (layouts) from document.xml.
    Extracts page size, margins, orientation, columns, headers/footers,
    borders, numbering, title page, vertical alignment, section type,
    line numbering, and misc layout settings.
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

            # Page borders
            pgBorders = sectPr.find("w:pgBorders", namespaces=self.nsmap)
            if pgBorders is not None:
                borders = {}
                for side in ["top", "bottom", "left", "right"]:
                    elem = pgBorders.find(f"w:{side}", namespaces=self.nsmap)
                    if elem is not None:
                        borders[side] = elem.attrib
                section_data["page_borders"] = borders

            # Page numbering
            pgNumType = sectPr.find("w:pgNumType", namespaces=self.nsmap)
            if pgNumType is not None:
                section_data["page_numbering"] = dict(pgNumType.attrib)

            # Title page flag
            if sectPr.find("w:titlePg", namespaces=self.nsmap) is not None:
                section_data["title_page"] = True

            # Vertical alignment
            vAlign = sectPr.find("w:vAlign", namespaces=self.nsmap)
            if vAlign is not None:
                section_data["vertical_alignment"] = vAlign.attrib.get(f"{{{self.nsmap['w']}}}val")

            # Section break type
            sect_type = sectPr.find("w:type", namespaces=self.nsmap)
            if sect_type is not None:
                section_data["section_type"] = sect_type.attrib.get(f"{{{self.nsmap['w']}}}val")

            # Line numbering
            lnNumType = sectPr.find("w:lnNumType", namespaces=self.nsmap)
            if lnNumType is not None:
                section_data["line_numbering"] = dict(lnNumType.attrib)

            # Misc: text direction, doc grid, form protection
            textDir = sectPr.find("w:textDirection", namespaces=self.nsmap)
            if textDir is not None:
                section_data["text_direction"] = textDir.attrib.get(f"{{{self.nsmap['w']}}}val")

            docGrid = sectPr.find("w:docGrid", namespaces=self.nsmap)
            if docGrid is not None:
                section_data["doc_grid"] = dict(docGrid.attrib)

            formProt = sectPr.find("w:formProt", namespaces=self.nsmap)
            if formProt is not None:
                section_data["form_protection"] = True

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
