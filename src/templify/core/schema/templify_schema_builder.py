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
    def extract_paragraphs(self) -> List[Dict[str, Any]]:
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

    def extract_styles(self) -> Dict[str, Any]:
        mapper = DocxStylesMapper(self.document_xml_path, self.docx_extract_dir)
        return mapper.collect_styles()

    def extract_sections(self) -> List[Dict[str, Any]]:
        mapper = DocxSectionsMapper(self.document_xml_path)
        return mapper.collect_sections()

    def extract_tables(self) -> List[Dict[str, Any]]:
        mapper = DocxTablesMapper(self.document_xml_path)
        return mapper.collect_tables()

    def extract_numbering(self) -> Dict[str, Any]:
        if not self.docx_extract_dir:
            return {}
        numbering_path = os.path.join(self.docx_extract_dir, "word", "numbering.xml")
        if os.path.exists(numbering_path):
            return DocxNumberingMapper(numbering_path).collect_numbering()
        return {}

    def extract_headers_footers(self) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]]]:
        if not self.docx_extract_dir:
            return [], []
        mapper = DocxHeadersFootersMapper(self.docx_extract_dir)
        hf = mapper.collect_headers_footers()
        return hf["headers"], hf["footers"]

    def extract_theme(self) -> Dict[str, Any]:
        if not self.docx_extract_dir:
            return {}
        theme_path = os.path.join(self.docx_extract_dir, "word", "theme", "theme1.xml")
        if os.path.exists(theme_path):
            return DocxThemesMapper(theme_path).collect_theme()
        return {}

    def extract_hyperlinks(self) -> List[Dict[str, Any]]:
        if not self.docx_extract_dir:
            return []
        rels_path = os.path.join(self.docx_extract_dir, "word", "_rels", "document.xml.rels")
        rels_map = {}
        if os.path.exists(rels_path):
            rels_tree = ET.parse(rels_path).getroot()
            for rel in rels_tree.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
                r_id = rel.attrib.get("Id")
                target = rel.attrib.get("Target")
                rels_map[r_id] = target
        links = []
        for link in self.body.findall(".//w:hyperlink", namespaces=self.nsmap):
            r_id = link.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            text = "".join(t.text for t in link.findall(".//w:t", namespaces=self.nsmap) if t.text)
            links.append({"text": text, "target": rels_map.get(r_id, "")})
        return links

    def extract_images(self) -> List[Dict[str, Any]]:
        if not self.docx_extract_dir:
            return []
        rels_path = os.path.join(self.docx_extract_dir, "word", "_rels", "document.xml.rels")
        rels_map = {}
        if os.path.exists(rels_path):
            rels_tree = ET.parse(rels_path).getroot()
            for rel in rels_tree.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
                if "image" in rel.attrib.get("Target", ""):
                    rels_map[rel.attrib.get("Id")] = rel.attrib.get("Target")
        images = []
        for drawing in self.body.findall(".//w:drawing", namespaces=self.nsmap):
            blip = drawing.find(".//a:blip", namespaces={"a": "http://schemas.openxmlformats.org/drawingml/2006/main"})
            if blip is not None:
                r_id = blip.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed", "")
                images.append({"rId": r_id, "path": rels_map.get(r_id, "")})
        return images

    def extract_bookmarks(self) -> List[Dict[str, Any]]:
        bookmarks = []
        for bm in self.body.findall(".//w:bookmarkStart", namespaces=self.nsmap):
            name = bm.attrib.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}name")
            bookmarks.append({"name": name})
        return bookmarks

    def extract_inline_formatting(self) -> List[Dict[str, Any]]:
        flags = []
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
            flags.append(formats)
        return flags

    def extract_metadata(self) -> Dict[str, Any]:
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
        pattern_descriptors = self.extract_paragraphs()
        global_defaults = self.extract_global_defaults()

        styles = self.extract_styles()
        sections = self.extract_sections()
        tables = self.extract_tables()
        numbering = self.extract_numbering()
        headers, footers = self.extract_headers_footers()
        theme = self.extract_theme()

        hyperlinks = self.extract_hyperlinks()
        images = self.extract_images()
        bookmarks = self.extract_bookmarks()
        inline_formatting = self.extract_inline_formatting()
        metadata = self.extract_metadata()

        generator = SchemaGenerator(
            sections=self.sections,
            layout_groups=self.layout_groups,
            global_defaults=global_defaults,
            # styles=styles,
            # tables=tables,
            # numbering=numbering,
            # headers=headers,
            # footers=footers,
            # theme=theme,
            # hyperlinks=hyperlinks,
            # images=images,
            # bookmarks=bookmarks,
            # inline_formatting=inline_formatting,
            # metadata=metadata,
            pattern_descriptors=pattern_descriptors,
        )
        return generator.generate()
