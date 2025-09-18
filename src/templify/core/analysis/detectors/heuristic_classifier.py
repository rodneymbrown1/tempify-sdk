"""
Heuristic Classifier

Acts as a unified entrypoint for all heuristic-based detectors
(heading, paragraph, list, callout, tabular).
Provides classify_lines() which orchestrates these detectors.
"""

from __future__ import annotations
from typing import List, Dict, Any

from templify.core.analysis.detectors.heuristics.heading_detector import detect_headings
from templify.core.analysis.detectors.heuristics.list_detector import detect_lists
from templify.core.analysis.detectors.heuristics.paragraph_detector import detect_paragraphs
from templify.core.analysis.detectors.heuristics.callouts import CalloutHeuristicDetector
from templify.core.analysis.detectors.heuristics.tabular_detector import detect_tables


def classify_lines(
    lines: List[str],
    *,
    domain_pack: Dict[str, Any] | None = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Run all heuristic detectors on a list of plaintext lines.
    Returns a flat list of classification results.

    Args:
        lines: List of plaintext lines to classify
        domain_pack: Optional domain-specific patterns/keywords
        kwargs: Extra options passed down to detectors

    Returns:
        List[dict]: Each dict contains at minimum:
            {
              "line_idx": int,
              "label": str,   # e.g. HEADING, PARAGRAPH, LIST, etc.
              "text": str,
              "features": {...}
            }
    """
    results: List[Dict[str, Any]] = []

    detectors = [
        ("HEADING", detect_headings),
        ("LIST", detect_lists),
        ("PARAGRAPH", detect_paragraphs),
        ("CALLOUT", lambda lines, **kwargs: CalloutHeuristicDetector().detect(lines, **kwargs)),
        ("TABLE", detect_tables),
    ]

    for label, detector in detectors:
        try:
            detected = detector(lines, **kwargs)
            for d in detected:
                results.append({
                    "line_idx": d.line_idx,
                    "label": getattr(d, "label", label),
                    "text": lines[d.line_idx] if d.line_idx < len(lines) else "",
                    "features": getattr(d, "__dict__", {}),
                })
        except Exception as e:
            results.append({"error": f"{label.lower()} detector failed: {e}"})

    return results
