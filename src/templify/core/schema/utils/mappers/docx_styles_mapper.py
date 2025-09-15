import os
import glob
import xml.etree.ElementTree as ET


class DocxStylesMapper:
    """
    Collects style definitions from an unzipped DOCX package and organizes them
    into a Python dictionary. This provides access to high-level features of
    Word styles (paragraphs, tables, lists, headers, footers, character, sections, defaults).
    """

    def __init__(self, document_xml_path, docx_extract_dir=None):
        self.document_xml_path = document_xml_path
        self.docx_extract_dir = docx_extract_dir
        self.nsmap = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        self.styles = {
            "paragraphs": {},
            "characters": {},
            "tables": {},
            "lists": {},
            "headers": {},
            "footers": {},
            "sections": {},
            "defaults": {},
            "latent": {},
        }

    def _open_xml(self, path):
        """Utility: open an XML file and return its root element."""
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return ET.parse(f).getroot()

    def collect_styles(self, theme: dict[str, any] | None = None) -> dict:
        """
        Scan the DOCX folder for style-related parts and collect their info.

        Returns:
            dict with style categories (paragraphs, characters, tables, lists, etc.)
            keyed by stable style IDs.
        """
        if not self.docx_extract_dir:
            return {}

        # Run parsers
        self._parse_paragraph_definitions()
        self._parse_character_definitions()
        self._parse_table_definitions()
        self._parse_list_definitions()
        self._parse_headers_and_footers()
        self._parse_section_definitions()
        self._parse_doc_defaults()

        # Post-process: assign stable IDs and resolve theme refs
        styles_with_ids: dict = {}
        for cat, style_map in self.styles.items():
            styles_with_ids[cat] = {}
            for style_name, attrs in style_map.items():
                style_id = f"sty_{style_name.lower().replace(' ', '_')}"
                # Ensure attrs is always a dict
                if not isinstance(attrs, dict):
                    attrs = {"definition": attrs}
                resolved = self._resolve_theme_references(attrs, theme)
                styles_with_ids[cat][style_id] = {
                    "name": style_name,
                    **resolved
                }

        self.styles = styles_with_ids
        return self.styles

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

    def _parse_character_definitions(self):
        path = os.path.join(self.docx_extract_dir, "word", "styles.xml")
        root = self._open_xml(path)
        if root is None:
            return

        for style in root.findall("w:style", namespaces=self.nsmap):
            if style.get(f"{{{self.nsmap['w']}}}type") != "character":
                continue
            style_id = style.get(f"{{{self.nsmap['w']}}}styleId")
            name = style.find("w:name", namespaces=self.nsmap)
            self.styles["characters"][style_id] = {
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
                self.styles["headers"][os.path.basename(hf)] = {
                    "text": text_content.strip()
                }

        for ff in footer_files:
            root = self._open_xml(ff)
            if root is not None:
                text_content = " ".join([t.text for t in root.findall(".//w:t", namespaces=self.nsmap) if t.text])
                self.styles["footers"][os.path.basename(ff)] = {
                    "text": text_content.strip()
                }

    def _parse_section_definitions(self):
        # Look inside document.xml for <w:sectPr>
        path = os.path.join(self.docx_extract_dir, "word", "document.xml")
        root = self._open_xml(path)
        if root is None:
            return

        for i, sectPr in enumerate(root.findall(".//w:sectPr", namespaces=self.nsmap)):
            self.styles["sections"][f"section{i}"] = {
                "definition": ET.tostring(sectPr, encoding="unicode")
            }

    def _parse_doc_defaults(self):
        path = os.path.join(self.docx_extract_dir, "word", "styles.xml")
        root = self._open_xml(path)
        if root is None:
            return

        doc_defaults = root.find("w:docDefaults", namespaces=self.nsmap)
        if doc_defaults is not None:
            self.styles["defaults"]["definition"] = ET.tostring(doc_defaults, encoding="unicode")

    def _parse_latent_styles(self):
        path = os.path.join(self.docx_extract_dir, "word", "styles.xml")
        root = self._open_xml(path)
        if root is None:
            return

        latent = root.find("w:latentStyles", namespaces=self.nsmap)
        if latent is None:
            return

        self.styles["latent"] = {
            "defaults": {k: latent.get(k) for k in latent.keys()},
            "exceptions": []
        }
        for lsd in latent.findall("w:lsdException", namespaces=self.nsmap):
            self.styles["latent"]["exceptions"].append({
                "name": lsd.get(f"{{{self.nsmap['w']}}}name"),
                "props": {k: lsd.get(k) for k in lsd.keys()}
            })

    def _resolve_theme_references(self, attrs: dict, theme: dict | None) -> dict:
        """
        Replace themeColor/themeFont references in attrs with actual values
        from a DocxThemesMapper dict.
        """
        if not theme:
            return attrs

        resolved = {}
        for k, v in attrs.items():
            if k == "color" and v in theme.get("colors", {}):
                resolved[k] = theme["colors"][v]
            elif k == "font" and v in theme.get("fonts", {}):
                resolved[k] = theme["fonts"][v]
            else:
                resolved[k] = v
        return resolved
