# src/templify/core/templify_schema_runner.py
from __future__ import annotations
import logging
from typing import List, Dict, Any, Tuple

from templify.core.analysis.matcher import route_match, PatternDescriptor

logger = logging.getLogger(__name__)


class TemplifySchemaRunner:
    """
    Loops over plaintext lines, runs the matcher, and collects tuples:
    (line, pattern_descriptor, style_obj)
    """

    def __init__(self, plaintext_lines: List[str], schema: Dict[str, Any]):
        self.plaintext_lines = plaintext_lines
        self.schema = schema
        self.pattern_descriptors = schema.get("pattern_descriptors", [])
        self.global_defaults = schema.get("global_defaults", {})

    def run(self) -> List[Tuple[str, PatternDescriptor, Dict[str, Any]]]:
        """
        Iterate through plaintext lines, run matcher, look up styles.
        Returns list of (line, pattern_descriptor, style_obj).
        """
        results: List[Tuple[str, PatternDescriptor, Dict[str, Any]]] = []

        for line in self.plaintext_lines:
            logger.debug(f"[RUNNER] Processing line: {line!r}")

            # Step 1: run matcher → PatternDescriptor
            descriptor = route_match(line)

            # Step 2: lookup style for this pattern (if any in schema)
            style_obj = self._lookup_style(descriptor)

            # Collect
            results.append((line, descriptor, style_obj))

        return results

    def _lookup_style(self, descriptor: PatternDescriptor) -> Dict[str, Any]:
        """
        Find style object from schema pattern_descriptors that matches
        the same type or regex pattern. Fallback → global defaults.
        """
        for pat in self.pattern_descriptors:
            if pat.get("type") == descriptor.type:
                return pat.get("style", {})

        # fallback
        return self.global_defaults.get("paragraph", {})
