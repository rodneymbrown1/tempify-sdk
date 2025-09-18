# src/templify/core/schema_runner/runner.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple
from docx import Document

from templify.core.schema_runner.resolvers.style_resolver import resolve_style
from templify.core.schema_runner.router import SchemaRouter
from templify.core.schema_runner.utils.docx_cleaner import strip_body_content


class TemplifySchemaRunner:
    """
    Loops over plaintext lines, applies descriptors, resolves styles,
    and dispatches to writers.

    Produces a list of tuples:
        (line_text, pattern_descriptor_dict, resolved_style_dict)
    """

    def __init__(self, schema: Dict[str, Any], source_docx: str | None = None):
        """
        :param schema: Full Templify schema (from TemplifySchemaBuilder.run()).
        :param source_docx: Optional override path to .docx template.
                            If None, falls back to schema["source_docx"].
        """
        self.schema = schema
        self.pattern_descriptors: List[Dict[str, Any]] = schema.get("pattern_descriptors", [])
        self.global_defaults: Dict[str, Any] = schema.get("global_defaults", {})

        # Decide which docx path to use
        docx_path = source_docx or schema.get("source_docx")
        if not docx_path:
            raise ValueError("No source_docx provided (param or schema).")

        self.document: Document = strip_body_content(docx_path)
        self.router = SchemaRouter(self.document)


    def run(self) -> List[Tuple[str, Dict[str, Any], Dict[str, Any]]]:
        results: List[Tuple[str, Dict[str, Any], Dict[str, Any]]] = []

        for desc in self.pattern_descriptors:
            line_text = desc.get("features", {}).get("clean_text", "")

            # --- Resolve style precedence ---
            style_obj = resolve_style(
                descriptor_type=desc.get("type", "UNKNOWN"),
                schema=self.schema,
                global_defaults=self.global_defaults,
                docx_styles=None,   # placeholder, resolver doesn’t use this yet
            )

            # --- Dispatch to correct writer ---
            self.router.dispatch(desc, style_obj)

            # --- Collect trace tuple for debugging/testing ---
            results.append((line_text, desc, style_obj))

        return results

    def save(self, output_path: str) -> None:
        """Persist the generated document."""
        self.document.save(output_path)
