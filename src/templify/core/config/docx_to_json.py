# src/templify/core/config/docx_to_json.py

import os
import glob
import re
import xml.etree.ElementTree as ET

from templify.core.config.generator import ConfigGenerator
from templify.core.config.exporter import ConfigExporter
from templify.core.config.docx_styles_mapper import DocxStylesMapper


class DocxToJsonParser:
    """
    Parses a DOCX (document.xml + related parts) into structured JSON configs.

    Produces two configs:
      - titles_config: rules for detecting section titles
      - docx_config: layout groups, elements, and styles

    This is the main entrypoint for transforming DOCX into JSON that can later
    be consumed by downstream pattern recognition or reconstruction tools.
    """

    def __init__(self, document_xml_path, docx_extract_dir=None, expected_titles=None):
        if not os.path.exists(document_xml_path):
            raise FileNotFoundError(f"document.xml not found: {document_xml_path}")

        with open(document_xml_path, "r", encoding="utf-8") as f:
            document_xml = f.read()

        self.nsmap = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        self.tree = ET.fromstring(document_xml)
        self.body = self.tree.find(".//w:body", namespaces=self.nsmap)

        # Collected structures
        self.titles = []
        self.layout_groups = []
        self.lists = []
        self.images = []
        self.hyperlinks = []
        self.headers = []
        self.footers = []

        self.group_counter = 0
        self.current_group = "group0"

        self.style_mapper = DocxStylesMapper(document_xml_path, docx_extract_dir)
        self.style_mapper.collect_styles()

        self.docx_extract_dir = docx_extract_dir
        self.expected_titles = expected_titles

        # Output configs
        self.titles_config = None
        self.docx_config = None

    # -------------------------
    # Title extraction
    # -------------------------
    def extract_titles(self):
        if self.expected_titles:
            # Use rigid expected titles list
            for idx, t in enumerate(self.expected_titles, start=1):
                if isinstance(t, str):
                    title_text = t
                    detection_pattern = f"^{re.escape(t)}$"
                elif isinstance(t, dict) and "title" in t:
                    title_text = t["title"]
                    detection_pattern = t.get("pattern", f"^{re.escape(title_text)}$")
                else:
                    continue

                self.titles.append(
                    {
                        "title": title_text,
                        "layout_group": "group0",
                        "section_type": f"section{idx}_title",
                        "style": {},
                        "title_detection": {
                            "pattern": detection_pattern,
                            "case_sensitive": False,
                        },
                    }
                )
            return

        # Default discovery mode
        for p in self.body.findall("w:p", namespaces=self.nsmap):
            title_candidate = self.parse_paragraph_for_title(p)
            if title_candidate:
                title_text, style_info = title_candidate
                self.titles.append(
                    {
                        "title": title_text,
                        "layout_group": self.current_group,
                        "section_type": f"section{len(self.titles) + 1}_title",
                        "style": style_info,
                        "title_detection": {
                            "pattern": f"^{re.escape(title_text)}$",
                            "case_sensitive": False,
                        },
                    }
                )

            # Detect section breaks
            sectPr = p.find("w:pPr/w:sectPr", namespaces=self.nsmap)
            if sectPr is not None:
                self.group_counter += 1
                self.current_group = f"group{self.group_counter}"

    def parse_paragraph_for_title(self, p):
        texts = [t.text for t in p.findall(".//w:t", namespaces=self.nsmap) if t.text]
        full_text = " ".join(texts).strip()
        if not full_text:
            return None

        # Look for style info if available
        style_info = {}
        pPr = p.find("w:pPr", namespaces=self.nsmap)
        if pPr is not None:
            pStyle = pPr.find("w:pStyle", namespaces=self.nsmap)
            if pStyle is not None:
                style_id = pStyle.attrib.get(f"{{{self.nsmap['w']}}}val")
                style_info = self.style_mapper.styles["paragraphs"].get(style_id, {})

        return full_text, style_info

    # -------------------------
    # Other feature extractors
    # -------------------------
    def extract_lists(self):
        for p in self.body.findall("w:p", namespaces=self.nsmap):
            numPr = p.find("w:pPr/w:numPr", namespaces=self.nsmap)
            if numPr is not None:
                texts = [t.text for t in p.findall(".//w:t", namespaces=self.nsmap) if t.text]
                self.lists.append(
                    {
                        "text": " ".join(texts).strip(),
                        "list_info": ET.tostring(numPr, encoding="unicode"),
                    }
                )

    def extract_images(self):
        for drawing in self.body.findall(".//w:drawing", namespaces=self.nsmap):
            self.images.append({"xml": ET.tostring(drawing, encoding="unicode")})
        for pict in self.body.findall(".//w:pict", namespaces=self.nsmap):
            self.images.append({"xml": ET.tostring(pict, encoding="unicode")})

    def extract_hyperlinks(self):
        for hl in self.body.findall(".//w:hyperlink", namespaces=self.nsmap):
            link_texts = [t.text for t in hl.findall(".//w:t", namespaces=self.nsmap) if t.text]
            self.hyperlinks.append(
                {
                    "display_text": " ".join(link_texts).strip(),
                    "rId": hl.attrib.get(
                        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
                    ),
                }
            )

    def extract_headers_footers(self):
        if not self.docx_extract_dir:
            return
        header_files = glob.glob(os.path.join(self.docx_extract_dir, "word", "header*.xml"))
        footer_files = glob.glob(os.path.join(self.docx_extract_dir, "word", "footer*.xml"))

        for hf in header_files:
            xml = ET.parse(hf).getroot()
            texts = [t.text for t in xml.findall(".//w:t", namespaces=self.nsmap) if t.text]
            self.headers.append({"file": os.path.basename(hf), "text": " ".join(texts).strip()})

        for ff in footer_files:
            xml = ET.parse(ff).getroot()
            texts = [t.text for t in xml.findall(".//w:t", namespaces=self.nsmap) if t.text]
            self.footers.append({"file": os.path.basename(ff), "text": " ".join(texts).strip()})

    def extract_layouts(self):
        self.layout_groups = []
        group_index = -1
        for p in self.body.findall("w:p", namespaces=self.nsmap):
            sectPr = p.find("w:pPr/w:sectPr", namespaces=self.nsmap)
            if sectPr is not None:
                group_index += 1
                group_name = f"group{group_index}"
                layout = {"group": group_name, "layout": {}, "section_types": []}

                sect_type = sectPr.find("w:type", namespaces=self.nsmap)
                if sect_type is not None:
                    layout["layout"]["section_break"] = sect_type.attrib.get(
                        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val", "nextPage"
                    )

                self.layout_groups.append(layout)

    # -------------------------
    # Run the pipeline
    # -------------------------
    def run(self):
        self.extract_titles()
        self.extract_layouts()
        self.extract_lists()
        self.extract_images()
        self.extract_hyperlinks()
        self.extract_headers_footers()

        generator = ConfigGenerator(
            self.titles,
            self.layout_groups,
            self.lists,
            self.images,
            self.hyperlinks,
            self.headers,
            self.footers,
        )
        self.titles_config = generator.build_titles_config()
        self.docx_config = generator.build_docx_config()

    # -------------------------
    # Optional: export to disk
    # -------------------------
    def export(self, output_dir):
        if self.titles_config is None or self.docx_config is None:
            raise RuntimeError("Parser must be run() before export().")
        exporter = ConfigExporter(self.titles_config, self.docx_config)
        return exporter.save_to_files(output_dir)
