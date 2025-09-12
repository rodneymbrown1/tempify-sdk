from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Sequence, Union, Dict, Any

from templify.core.analysis.utils.plaintext_context import PlaintextContext
from templify.core.analysis.detectors.utils import coerce_to_lines, normalize_line


@dataclass(frozen=True)
class TabularDetection:
    line_idx: int
    label: str = "tabular"
    score: float = 0.0
    method: str = "heuristic"


# ---------- Regex helpers ----------
PIPE_RE = re.compile(r"\|")
DELIM_RE = re.compile(r"[;,\t]")
GRID_BORDER_RE = re.compile(r"^[\+\-\|\=]+$")  # ASCII table lines


def score_tabular_line(text: str, *, debug: bool = False) -> float:
    """
    Score how tabular/grid-like a line is. Returns 0..1.
    """
    s = normalize_line(text or "")
    if not s:
        return 0.0

    score = 0.0
    logs = []

    tokens = s.split()
    num_tokens = len(tokens)

    # Positive: many tokens (columns)
    if num_tokens >= 4:
        score += 0.8; logs.append(("multi_column", +0.8))

    # Positive: delimiters (pipes, commas, tabs, semicolons)
    if PIPE_RE.search(s) or DELIM_RE.search(s):
        score += 0.3; logs.append(("delimiter", +0.3))

    # Positive: mostly digits
    digit_ratio = sum(c.isdigit() for c in s) / max(1, len(s))
    if digit_ratio > 0.3:
        score += 0.3; logs.append(("digit_ratio", +0.3))

    # Positive: ASCII borders
    # In score_tabular_line
    if GRID_BORDER_RE.match(s):
        score += 0.9; logs.append(("grid_border", +0.9))

    # Negative: stopwords (likely prose, not table)
    if any(stop in s.lower().split() for stop in {"the", "is", "and", "of", "in"}):
        score -= 0.3; logs.append(("stopwords", -0.3))

    final = max(0.0, min(1.0, score))

    if debug:
        print(f"[Tabular scoring] {text!r} → {final:.3f}")
        for name, delta in logs:
            print(f"  - {name}: {delta:+.2f}")

    return final


def detect_tabular(
    source: Union[Sequence[str], PlaintextContext],
    threshold: float = 0.55,
    label: str = "tabular",
) -> List[TabularDetection]:
    lines = coerce_to_lines(source)
    preds: List[TabularDetection] = []

    for i, s in enumerate(lines):
        sc = score_tabular_line(s)
        if sc >= threshold:
            preds.append(TabularDetection(i, label, sc))

    return preds
