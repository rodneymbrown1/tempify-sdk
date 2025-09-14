# src/templify/core/config/docx_to_json.py
from __future__ import annotations
import os
import glob
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

from templify.core.analysis.matcher import route_match
from templify.core.analysis.utils.pattern_descriptor import PatternDescriptor
from templify.core.analysis.utils.section import Section
from templify.core.schema.utils.section_builder import build_sections_from_headings
from templify.core.schema.schema_generator import SchemaGenerator
from templify.core.schema.utils.docx_styles_mapper import DocxStylesMapper
from templify.core.analysis.detectors.heuristics.heading_detector import detect_headings
from templify.core.schema.utils.schema_saver import SchemaSaver

class TemplifySchemaBuilder:
    """
    Parse a DOCX XML and build a Templify schema.

    Produces:
      - sections (recursive Section tree)
      - layout_groups
      - global_defaults
    """

    def __init__(self, document_xml_path: str, docx_extract_dir: str | None = None):
        if not os.path.exists(document_xml_path):
            raise FileNotFoundError(f"document.xml not found: {document_xml_path}")

        with open(document_xml_path, "r", encoding="utf-8") as f:
            document_xml = f.read()

        self.nsmap = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        self.tree = ET.fromstring(document_xml)
        self.body = self.tree.find(".//w:body", namespaces=self.nsmap)

        self.docx_extract_dir = docx_extract_dir
        self.style_mapper = DocxStylesMapper(document_xml_path, docx_extract_dir)
        self.style_mapper.collect_styles()

        # Will hold results
        self.sections: List[Section] = []
        self.layout_groups: List[Dict[str, Any]] = []
        self.global_defaults: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Extractors
    # ------------------------------------------------------------------
    def extract_headings(self) -> List[PatternDescriptor]:
        """Detect headings and coerce into PatternDescriptors."""
        lines = []
        for p in self.body.findall("w:p", namespaces=self.nsmap):
            texts = [t.text for t in p.findall(".//w:t", namespaces=self.nsmap) if t.text]
            if texts:
                lines.append(" ".join(texts).strip())

        detections = detect_headings(lines)
        descriptors: List[PatternDescriptor] = []
        for det in detections:
            desc = route_match("heading", det.clean_text or lines[det.line_idx])
            # Inject hierarchy metadata into features
            desc.features = desc.features or {}
            desc.features.update({
                "level": det.level,
                "numbering": det.numbering,
                "clean_text": det.clean_text,
            })
            descriptors.append(desc)

        # Build recursive Section tree
        self.sections = build_sections_from_headings(detections, descriptors)
        return descriptors

    def extract_layouts(self):
        """Simplified: detect sectPr for layout groups."""
        self.layout_groups = []
        group_index = -1
        for p in self.body.findall("w:p", namespaces=self.nsmap):
            sectPr = p.find("w:pPr/w:sectPr", namespaces=self.nsmap)
            if sectPr is not None:
                group_index += 1
                group_name = f"group{group_index}"
                self.layout_groups.append({
                    "group": group_name,
                    "layout": {
                        "columns": 2,  # TODO: parse from sectPr
                        "margins": {"left": 1440, "right": 1440},
                        "orientation": "portrait",
                    },
                })

        # Always add a fallback
        if not self.layout_groups:
            self.layout_groups.append({
                "group": "group0",
                "layout": {
                    "columns": 2,
                    "margins": {"left": 1440, "right": 1440},
                    "orientation": "portrait",
                },
            })

    def extract_global_defaults(self):
        """Baseline defaults (could parse from document.xml later)."""
        self.global_defaults = {
            "page_size": {"width": 12240, "height": 15840},
            "font": {"name": "Arial", "size": 12},
            "paragraph": {"alignment": "left"},
        }

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------
    def run(self) -> Dict[str, Any]:
        self.extract_headings()
        self.extract_layouts()
        self.extract_global_defaults()

        generator = SchemaGenerator(
            sections=self.sections,
            layout_groups=self.layout_groups,
            global_defaults=self.global_defaults,
        )
        return generator.generate()


class TemplifySchemaBuilder:
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
        for p in self.body.findall("w:p", namespaces=self.nsmap):
            texts = [t.text for t in p.findall(".//w:t", namespaces=self.nsmap) if t.text]
            full_text = " ".join(texts).strip()
            if not full_text:
                continue

            # classify first
            desc = route_match("heading", full_text, features={})
            if not desc.class_.startswith("H-"):   # only keep real headings
                continue

            style_info = {}
            pStyle = p.find("w:pPr/w:pStyle", namespaces=self.nsmap)
            if pStyle is not None:
                style_id = pStyle.attrib.get(f"{{{self.nsmap['w']}}}val")
                style_info = self.style_mapper.styles["paragraphs"].get(style_id, {}).copy()
                style_info["pStyle"] = style_id

            self.titles.append({
                "title": full_text,
                "layout_group": self.current_group,
                "section_type": f"section{len(self.titles) + 1}_title",
                "style": style_info,
                "title_detection": {
                    "pattern": f"^{re.escape(full_text)}$",
                    "case_sensitive": False,
                },
            })
            
    def parse_paragraph_for_title(self, p):
        texts = [t.text for t in p.findall(".//w:t", namespaces=self.nsmap) if t.text]
        full_text = " ".join(texts).strip()
        if not full_text:
            return None

        # Look for style info if available
        style_info = {}
        pStyle = None
        pPr = p.find("w:pPr", namespaces=self.nsmap)
        if pPr is not None:
            pStyle = pPr.find("w:pStyle", namespaces=self.nsmap)

        if pStyle is not None:
            style_id = pStyle.attrib.get(f"{{{self.nsmap['w']}}}val")
            style_info = self.style_mapper.styles["paragraphs"].get(style_id, {}).copy()
            style_info["pStyle"] = style_id
        
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
        # after for-loop
        body_sectPr = self.body.find("w:sectPr", namespaces=self.nsmap)
        if body_sectPr is not None:
            group_name = f"group{len(self.layout_groups)}"
            layout = {"group": group_name, "layout": {}, "section_types": []}
            sect_type = body_sectPr.find("w:type", namespaces=self.nsmap)
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

        # --- Collect patterns ---
        pattern_set = {}

        def add_pattern(desc):
            d = desc.to_dict()
            key = (
                d.get("class"),
                d.get("regex") or d.get("exact_set") or d.get("pattern"),
                d.get("style"),
            )
            pattern_set[key] = d


        for t in self.titles:
            desc = route_match("heading", t["title"], features=t.get("style"))
            add_pattern(desc)

        for lst in self.lists:
            desc = route_match("list", lst["text"])
            add_pattern(desc)

        # Include body paragraphs
        for p in self.body.findall("w:p", namespaces=self.nsmap):
            text = " ".join(t.text for t in p.findall(".//w:t", namespaces=self.nsmap) if t.text)
            if not text.strip():
                continue

            desc = route_match("paragraph", text)

            # --- Heuristic guardrails ---
            # Only keep if confidence ≥ 0.55
            if getattr(desc, "confidence", 0.0) < 0.55:
                continue

            # Deduplicate by class + style + normalized text
            d = desc.to_dict()
            key = (
                d.get("class"),
                d.get("style"),
                d.get("pattern") or d.get("regex") or d.get("exact_set"),
            )

            if key in pattern_set:
                continue  # skip near-duplicates

            add_pattern(desc)


        generator = SchemaGenerator(
            self.titles, self.layout_groups, self.lists, self.images, self.hyperlinks, self.headers, self.footers,
            patterns=list(pattern_set.values()),
        )
        self.titles_config = generator.build_titles_config()
        self.docx_config = generator.build_docx_config()

    # -------------------------
    # Optional: export to disk
    # -------------------------
    def export(self, output_dir):
        if self.titles_config is None or self.docx_config is None:
            raise RuntimeError("Parser must be run() before export().")
        exporter = SchemaSaver(self.titles_config, self.docx_config)
        return exporter.save_to_files(output_dir)
    

