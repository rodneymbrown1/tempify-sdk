# src/templify/core/config/docx_styles_mapper.py

import os
import glob
import xml.etree.ElementTree as ET


class DocxStylesMapper:
    """
    Collects style definitions from an unzipped DOCX package and organizes them
    into a Python dictionary. This provides access to high-level features of
    Word styles (paragraphs, tables, lists, headers, footers).
    """

    def __init__(self, document_xml_path, docx_extract_dir=None):
        self.document_xml_path = document_xml_path
        self.docx_extract_dir = docx_extract_dir
        self.nsmap = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        self.styles = {
            "paragraphs": {},
            "tables": {},
            "lists": {},
            "headers": {},
            "footers": {},
        }

    def _open_xml(self, path):
        """Utility: open an XML file and return its root element."""
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return ET.parse(f).getroot()

    def collect_styles(self):
        """Scan the DOCX folder for style-related parts and collect their info."""
        if not self.docx_extract_dir:
            return

        self._parse_paragraph_definitions()
        self._parse_table_definitions()
        self._parse_list_definitions()
        self._parse_headers_and_footers()

    # ------------------------
    # Internal parsing helpers
    # ------------------------
    def _parse_paragraph_definitions(self):
        path = os.path.join(self.docx_extract_dir, "word", "styles.xml")
        root = self._open_xml(path)
        if root is None:
            return

        for style in root.findall("w:style", namespaces=self.nsmap):
            if style.get(f"{{{self.nsmap['w']}}}type") != "paragraph":
                continue
            style_id = style.get(f"{{{self.nsmap['w']}}}styleId")
            name = style.find("w:name", namespaces=self.nsmap)
            self.styles["paragraphs"][style_id] = {
                "label": name.get(f"{{{self.nsmap['w']}}}val") if name is not None else None,
                "definition": ET.tostring(style, encoding="unicode"),
            }

    def _parse_table_definitions(self):
        path = os.path.join(self.docx_extract_dir, "word", "styles.xml")
        root = self._open_xml(path)
        if root is None:
            return

        for style in root.findall("w:style", namespaces=self.nsmap):
            if style.get(f"{{{self.nsmap['w']}}}type") != "table":
                continue
            style_id = style.get(f"{{{self.nsmap['w']}}}styleId")
            name = style.find("w:name", namespaces=self.nsmap)
            tblPr = style.find("w:tblPr", namespaces=self.nsmap)
            self.styles["tables"][style_id] = {
                "label": name.get(f"{{{self.nsmap['w']}}}val") if name is not None else None,
                "properties": ET.tostring(tblPr, encoding="unicode") if tblPr is not None else None,
            }

    def _parse_list_definitions(self):
        path = os.path.join(self.docx_extract_dir, "word", "numbering.xml")
        root = self._open_xml(path)
        if root is None:
            return

        for num in root.findall("w:num", namespaces=self.nsmap):
            num_id = num.get(f"{{{self.nsmap['w']}}}numId")
            abstract_ref = num.find("w:abstractNumId", namespaces=self.nsmap)
            self.styles["lists"][num_id] = {
                "abstract_ref": abstract_ref.get(f"{{{self.nsmap['w']}}}val") if abstract_ref is not None else None,
                "definition": ET.tostring(num, encoding="unicode"),
            }

    def _parse_headers_and_footers(self):
        header_files = glob.glob(os.path.join(self.docx_extract_dir, "word", "header*.xml"))
        footer_files = glob.glob(os.path.join(self.docx_extract_dir, "word", "footer*.xml"))

        for hf in header_files:
            root = self._open_xml(hf)
            if root is not None:
                text_content = " ".join([t.text for t in root.findall(".//w:t", namespaces=self.nsmap) if t.text])
                self.styles["headers"][os.path.basename(hf)] = text_content.strip()

        for ff in footer_files:
            root = self._open_xml(ff)
            if root is not None:
                text_content = " ".join([t.text for t in root.findall(".//w:t", namespaces=self.nsmap) if t.text])
                self.styles["footers"][os.path.basename(ff)] = text_content.strip()
