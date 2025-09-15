# src/templify/core/schema/utils/mappers/docx_tables_mapper.py
import os
import xml.etree.ElementTree as ET
from typing import List, Dict, Any


class DocxTablesMapper:
    """
    Collects table definitions from document.xml.
    Produces a list of table dicts with rows, cells, and style properties.
    """

    def __init__(self, document_xml_path: str):
        if not os.path.exists(document_xml_path):
            raise FileNotFoundError(f"document.xml not found: {document_xml_path}")
        with open(document_xml_path, "r", encoding="utf-8") as f:
            self.tree = ET.parse(f)
        self.nsmap = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    def collect_tables(self) -> List[Dict[str, Any]]:
        tables = []
        for tbl in self.tree.findall(".//w:tbl", namespaces=self.nsmap):
            table_data = {
                "properties": self._parse_tblPr(tbl.find("w:tblPr", namespaces=self.nsmap)),
                "grid": self._parse_tblGrid(tbl.find("w:tblGrid", namespaces=self.nsmap)),
                "rows": self._parse_rows(tbl.findall("w:tr", namespaces=self.nsmap)),
            }
            tables.append(table_data)
        return tables

    def _parse_tblPr(self, tblPr) -> Dict[str, Any]:
        if tblPr is None:
            return {}
        props = {}
        jc = tblPr.find("w:jc", namespaces=self.nsmap)
        if jc is not None:
            props["alignment"] = jc.attrib.get(f"{{{self.nsmap['w']}}}val")
        tblW = tblPr.find("w:tblW", namespaces=self.nsmap)
        if tblW is not None:
            props["width"] = tblW.attrib.get(f"{{{self.nsmap['w']}}}w")
        borders = tblPr.find("w:tblBorders", namespaces=self.nsmap)
        if borders is not None:
            props["borders"] = {
                side.tag.split("}")[1]: side.attrib.get(f"{{{self.nsmap['w']}}}val")
                for side in borders
            }
        return props

    def _parse_tblGrid(self, tblGrid) -> List[Dict[str, Any]]:
        if tblGrid is None:
            return []
        return [
            {"width": gridCol.attrib.get(f"{{{self.nsmap['w']}}}w")}
            for gridCol in tblGrid.findall("w:gridCol", namespaces=self.nsmap)
        ]

    def _parse_rows(self, rows) -> List[Dict[str, Any]]:
        parsed_rows = []
        for tr in rows:
            row_data = {
                "properties": self._parse_trPr(tr.find("w:trPr", namespaces=self.nsmap)),
                "cells": self._parse_cells(tr.findall("w:tc", namespaces=self.nsmap)),
            }
            parsed_rows.append(row_data)
        return parsed_rows

    def _parse_trPr(self, trPr) -> Dict[str, Any]:
        if trPr is None:
            return {}
        props = {}
        trHeight = trPr.find("w:trHeight", namespaces=self.nsmap)
        if trHeight is not None:
            props["height"] = trHeight.attrib.get(f"{{{self.nsmap['w']}}}val")
        return props

    def _parse_cells(self, cells) -> List[Dict[str, Any]]:
        parsed_cells = []
        for tc in cells:
            text = " ".join(
                t.text for t in tc.findall(".//w:t", namespaces=self.nsmap) if t.text
            )
            props = {}
            tcPr = tc.find("w:tcPr", namespaces=self.nsmap)
            if tcPr is not None:
                gridSpan = tcPr.find("w:gridSpan", namespaces=self.nsmap)
                if gridSpan is not None:
                    props["colspan"] = gridSpan.attrib.get(f"{{{self.nsmap['w']}}}val")
                vMerge = tcPr.find("w:vMerge", namespaces=self.nsmap)
                if vMerge is not None:
                    props["rowspan"] = vMerge.attrib.get(f"{{{self.nsmap['w']}}}val")
            parsed_cells.append({"text": text, "properties": props})
        return parsed_cells
