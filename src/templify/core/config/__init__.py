"""
templify.core.config
--------------------
Configuration utilities for DOCX parsing and reconstruction.

Exports:
    - ConfigGenerator : assemble JSON configs from parsed DOCX content
    - ConfigExporter  : write configs to disk
    - DocxStylesMapper: collect style definitions from unzipped DOCX
    - DocxToJsonParser: parse DOCX XML into structured configs
"""

from .config_generator import ConfigGenerator
from .config_exporter import ConfigExporter
from .docx_styles_mapper import DocxStylesMapper
from .docx_to_json import DocxToJsonParser

__all__ = [
    "ConfigGenerator",
    "ConfigExporter",
    "DocxStylesMapper",
    "DocxToJsonParser",
]
