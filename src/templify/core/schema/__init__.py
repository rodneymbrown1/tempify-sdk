"""
templify.core.config
--------------------
Configuration utilities for DOCX parsing and reconstruction.

Exports:
    - SchemaGenerator : assemble JSON configs from parsed DOCX content
    - SchemaSaver  : write configs to disk
    - DocxStylesMapper: collect style definitions from unzipped DOCX
    - TemplifySchemaBuilder: parse DOCX XML into structured configs
"""

from .schema_generator import SchemaGenerator
from .utils.schema_saver import SchemaSaver
from .utils.mappers.docx_styles_mapper import DocxStylesMapper
from .templify_schema_builder import TemplifySchemaBuilder

__all__ = [
    "SchemaGenerator",
    "SchemaSaver",
    "DocxStylesMapper",
    "TemplifySchemaBuilder",
]
