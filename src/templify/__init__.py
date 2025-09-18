"""
Templify SDK
============

A toolkit for analyzing, mapping, and generating schemas from DOCX and plaintext sources.
Provides a unified API around:
- Analysis (detectors, forms, matchers)
- Schema building (TemplifySchemaBuilder, SchemaGenerator)
- Utilities (mappers, intake, workspace)
"""

from importlib.metadata import version, PackageNotFoundError

__all__ = [
    "__version__",
    "TemplifySchemaBuilder",
    "SchemaGenerator",
    "build_schema",
]

# ----------------------------------------------------------------------
# Package version
# ----------------------------------------------------------------------
try:
    __version__ = version("templify")
except PackageNotFoundError:
    __version__ = "0.0.0"

# ----------------------------------------------------------------------
# Public imports
# ----------------------------------------------------------------------
from templify.core.schema.build_schema import TemplifySchemaBuilder
from templify.core.schema.schema_generator import SchemaGenerator
from templify.runner import build_schema
