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

from templify.core.analysis.detectors.heuristics.heading_detector import detect_headings
from templify.core.schema.utils.mappers.docx_styles_mapper import DocxStylesMapper
from templify.core.schema.utils.mappers.docx_sections_mapper import DocxSectionsMapper
from templify.core.schema.utils.mappers.docx_tables_mapper import DocxTablesMapper
from templify.core.schema.utils.mappers.docx_numbering_mapper import DocxNumberingMapper
from templify.core.schema.utils.mappers.docx_headers_footers_mapper import DocxHeadersFootersMapper
from templify.core.schema.utils.mappers.docx_themes_mapper import DocxThemesMapper


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
        self.layout_groups: List[Dict[str, Any]] = []
        self.global_defaults: Dict[str, Any] = {}

        self.hyperlinks: list[dict] = []
        self.bookmarks: list[dict] = []
        self.metadata: dict[str, str] = {}
        self.inline_formatting: list[dict[str, bool]] = []
        self.images: list[dict] = []
        self.styles: dict = {}
        self.sections: list = []
        self.tables: list = []
        self.numbering: dict = {}
        self.headers: list = []
        self.footers: list = []
        self.theme: dict = {}



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

    def extract_global_defaults(self):
        """Baseline defaults (could parse from document.xml later)."""
        self.global_defaults = {
            "page_size": {"width": 12240, "height": 15840},
            "font": {"name": "Arial", "size": 12},
            "paragraph": {"alignment": "left"},
        }

    def extract_hyperlinks(self):
        """Extract hyperlinks and anchor text from document.xml and rels."""
        rels_path = os.path.join(self.docx_extract_dir, "word", "_rels", "document.xml.rels")
        rels_map = {}
        if os.path.exists(rels_path):
            rels_tree = ET.parse(rels_path).getroot()
            for rel in rels_tree.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
                r_id = rel.attrib.get("Id")
                target = rel.attrib.get("Target")
                rels_map[r_id] = target

        for link in self.body.findall(".//w:hyperlink", namespaces=self.nsmap):
            r_id = link.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            text = "".join(t.text for t in link.findall(".//w:t", namespaces=self.nsmap) if t.text)
            self.hyperlinks.append({"text": text, "target": rels_map.get(r_id, "")})

    def extract_images(self):
        """Extract images and relationships from document.xml."""
        rels_path = os.path.join(self.docx_extract_dir, "word", "_rels", "document.xml.rels")
        rels_map = {}
        if os.path.exists(rels_path):
            rels_tree = ET.parse(rels_path).getroot()
            for rel in rels_tree.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
                if "image" in rel.attrib.get("Target", ""):
                    rels_map[rel.attrib.get("Id")] = rel.attrib.get("Target")

        for drawing in self.body.findall(".//w:drawing", namespaces=self.nsmap):
            r_id = drawing.find(".//a:blip", namespaces={
                "a": "http://schemas.openxmlformats.org/drawingml/2006/main"
            }).attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed", "")
            self.images.append({"rId": r_id, "path": rels_map.get(r_id, "")})

    def extract_bookmarks(self):
        """Extract bookmarks from document.xml."""
        for bm in self.body.findall(".//w:bookmarkStart", namespaces=self.nsmap):
            name = bm.attrib.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}name")
            self.bookmarks.append({"name": name})

    def extract_inline_formatting(self):
        """Collect inline formatting flags (bold, italic, underline)."""
        for p in self.body.findall(".//w:p", namespaces=self.nsmap):
            formats = {"bold": False, "italic": False, "underline": False}
            for r in p.findall(".//w:r", namespaces=self.nsmap):
                rPr = r.find("w:rPr", namespaces=self.nsmap)
                if rPr is not None:
                    if rPr.find("w:b", namespaces=self.nsmap) is not None:
                        formats["bold"] = True
                    if rPr.find("w:i", namespaces=self.nsmap) is not None:
                        formats["italic"] = True
                    if rPr.find("w:u", namespaces=self.nsmap) is not None:
                        formats["underline"] = True
            self.inline_formatting.append(formats)

    def extract_metadata(self):
        """Parse metadata from docProps/core.xml."""
        if not self.docx_extract_dir:
            return
        core_path = os.path.join(self.docx_extract_dir, "docProps", "core.xml")
        if not os.path.exists(core_path):
            return

        core_tree = ET.parse(core_path).getroot()
        nsmap = {
            "dc": "http://purl.org/dc/elements/1.1/",
            "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
        }
        self.metadata = {
            "title": (core_tree.find("dc:title", nsmap).text if core_tree.find("dc:title", nsmap) is not None else ""),
            "subject": (core_tree.find("dc:subject", nsmap).text if core_tree.find("dc:subject", nsmap) is not None else ""),
            "creator": (core_tree.find("dc:creator", nsmap).text if core_tree.find("dc:creator", nsmap) is not None else ""),
            "keywords": (core_tree.find("cp:keywords", nsmap).text if core_tree.find("cp:keywords", nsmap) is not None else ""),
        }

    def extract_styles(self):
        self.styles = self.style_mapper.collect_styles()

    def extract_sections(self):
        mapper = DocxSectionsMapper(self.document_xml_path)
        self.sections = mapper.collect_sections()

    def extract_tables(self):
        mapper = DocxTablesMapper(self.document_xml_path)
        self.tables = mapper.collect_tables()

    def extract_numbering(self):
        numbering_path = os.path.join(self.docx_extract_dir, "word", "numbering.xml")
        if os.path.exists(numbering_path):
            mapper = DocxNumberingMapper(numbering_path)
            self.numbering = mapper.collect_numbering()

    def extract_headers_footers(self):
        mapper = DocxHeadersFootersMapper(self.docx_extract_dir)
        hf = mapper.collect_headers_footers()
        self.headers = hf["headers"]
        self.footers = hf["footers"]

    def extract_theme(self):
        theme_path = os.path.join(self.docx_extract_dir, "word", "theme", "theme1.xml")
        if os.path.exists(theme_path):
            mapper = DocxThemesMapper(theme_path)
            self.theme = mapper.collect_theme()



    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------
    def run(self) -> Dict[str, Any]:
        # Core extractions
        self.extract_headings()
        self.extract_global_defaults()

        # Mappers
        self.extract_styles()
        self.extract_sections()
        self.extract_tables()
        self.extract_numbering()
        self.extract_headers_footers()
        self.extract_theme()

        # Easy integrations
        self.extract_hyperlinks()
        self.extract_images()
        self.extract_bookmarks()
        self.extract_inline_formatting()
        self.extract_metadata()

        # Assemble schema
        generator = SchemaGenerator(
            sections=self.sections,
            layout_groups=self.layout_groups,
            global_defaults=self.global_defaults,
        )
        schema = generator.generate()

        # Attach extras
        schema.update({
            "styles": self.styles,
            "tables": self.tables,
            "numbering": self.numbering,
            "headers": self.headers,
            "footers": self.footers,
            "theme": self.theme,
            "hyperlinks": self.hyperlinks,
            "images": self.images,
            "bookmarks": self.bookmarks,
            "inline_formatting": self.inline_formatting,
            "metadata": self.metadata,
        })
        return schema
