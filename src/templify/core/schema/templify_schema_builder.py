from __future__ import annotations
import os
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

from templify.core.analysis.matcher import route_match
from templify.core.analysis.utils.section import Section
from templify.core.schema.utils.section_builder import build_sections_from_headings
from templify.core.schema.schema_generator import SchemaGenerator

from templify.core.analysis.detectors.heuristics.heading_detector import detect_headings
from templify.core.schema.utils.mappers.docx_styles_mapper import DocxStylesMapper
from templify.core.schema.utils.mappers.docx_sections_mapper import DocxSectionsMapper
from templify.core.schema.utils.mappers.docx_tables_mapper import DocxTablesMapper
from templify.core.schema.utils.mappers.docx_numbering_mapper import DocxNumberingMapper
from templify.core.schema.utils.mappers.docx_headers_footers_mapper import DocxHeadersFootersMapper
from templify.core.schema.utils.mappers.docx_themes_mapper import DocxThemesMapper
from templify.core.schema.utils.mappers.docx_text_mapper import DocxTextMapper


class TemplifySchemaBuilder:
    """
    Parse a DOCX XML and build a Templify schema.

    Orchestrates extraction via mappers, then delegates schema assembly
    to SchemaGenerator.
    """

    def __init__(self, document_xml_path: str, docx_extract_dir: str | None = None):
        if not os.path.exists(document_xml_path):
            raise FileNotFoundError(f"document.xml not found: {document_xml_path}")

        with open(document_xml_path, "r", encoding="utf-8") as f:
            document_xml = f.read()

        self.nsmap = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        self.tree = ET.fromstring(document_xml)
        self.body = self.tree.find(".//w:body", namespaces=self.nsmap)

        self.document_xml_path = document_xml_path
        self.docx_extract_dir = docx_extract_dir

        # containers for extraction results
        self.sections: List[Section] = []
        self.layout_groups: List[Dict[str, Any]] = []
        self.global_defaults: Dict[str, Any] = {}
        self.pattern_descriptors: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Extractors
    # ------------------------------------------------------------------
    def generate_pattern_descriptors(self) -> List[Dict[str, Any]]:
        """Detect all paragraphs and build pattern descriptors with taxonomy + styles."""
        # preload styles + defaults
        styles = self.extract_styles()
        defaults = self.extract_global_defaults()
        text_mapper = DocxTextMapper(self.nsmap, styles, defaults)

        # extract paragraphs (text + style + id)
        paragraphs_info = text_mapper.extract_paragraphs(self.body)
        descriptors = []
        lines = []
        para_ids = []

        for i, pinfo in enumerate(paragraphs_info):
            text = (pinfo["text"] or "").strip()
            if not text:
                continue

            para_id = pinfo["paragraph_id"] or f"p_{i+1}"

            desc = route_match(
                text = text,
                features=pinfo["style"],  
                domain=None,
            )  

            # attach metadata
            desc.paragraph_id = para_id
            desc.features.update({"clean_text": text})
            desc.style = pinfo["style"]

            descriptors.append(desc)
            lines.append(text)
            para_ids.append(para_id)

        # save descriptors into builder
        self.pattern_descriptors = [d.to_dict() for d in descriptors]

        # 🔹 still build section tree from heading-like descriptors
        detections = detect_headings(lines)
        self.sections = build_sections_from_headings(detections, descriptors)

        return self.pattern_descriptors
    
    def extract_global_defaults(self) -> Dict[str, Any]:
        """Baseline defaults (could be enhanced to parse document.xml)."""
        self.global_defaults = {
            "page_size": {"width": 12240, "height": 15840},
            "font": {"name": "Arial", "size": 12},
            "paragraph": {"alignment": "left"},
        }
        return self.global_defaults

        if not self.docx_extract_dir:
            return {}
        core_path = os.path.join(self.docx_extract_dir, "docProps", "core.xml")
        if not os.path.exists(core_path):
            return {}
        core_tree = ET.parse(core_path).getroot()
        nsmap = {
            "dc": "http://purl.org/dc/elements/1.1/",
            "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
        }
        return {
            "title": (core_tree.find("dc:title", nsmap).text if core_tree.find("dc:title", nsmap) is not None else ""),
            "subject": (core_tree.find("dc:subject", nsmap).text if core_tree.find("dc:subject", nsmap) is not None else ""),
            "creator": (core_tree.find("dc:creator", nsmap).text if core_tree.find("dc:creator", nsmap) is not None else ""),
            "keywords": (core_tree.find("cp:keywords", nsmap).text if core_tree.find("cp:keywords", nsmap) is not None else ""),
        }

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------
    def run(self) -> Dict[str, Any]:
        pattern_descriptors = self.generate_pattern_descriptors()
        global_defaults = self.extract_global_defaults()

        generator = SchemaGenerator(
            sections=self.sections,
            layout_groups=self.layout_groups,
            global_defaults=global_defaults,
            pattern_descriptors=pattern_descriptors,
        )
        return generator.generate()
