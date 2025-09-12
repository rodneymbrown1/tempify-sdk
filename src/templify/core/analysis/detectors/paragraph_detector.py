from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Sequence, Union, Dict, Any

from templify.core.analysis.features import extract_line_features
from templify.core.analysis.utils.plaintext_context import PlaintextContext
from templify.core.analysis.detectors.utils import coerce_to_lines, normalize_line


@dataclass(frozen=True)
class ParagraphDetection:
    line_idx: int
    label: str
    score: float
    method: str = "heuristic"


# ---------- Regex helpers ----------
_ALL_CAPS_RE   = re.compile(r"^[A-Z0-9\s\W]+$")
_BULLET_RE     = re.compile(r"^\s*([\-–—•▪◦●·])\s+")
_TOC_DOTS_RE   = re.compile(r"[.]{2,}\s*\d+$")


def score_paragraph(text: str, features: Dict[str, Any] | Any | None = None, *, debug: bool = False) -> float:
    """
    Score how paragraph-like a line is. Returns 0..1.
    Positive = looks like a paragraph, Negative = looks like heading/metadata/list/etc.
    """
    s = normalize_line(text or "")
    if not s:
        return 0.0

    words = s.split()
    num_tokens = len(words)

    score = 0.0
    logs = []

    # ---------- Positive signals ----------
    if num_tokens >= 8:
        score += 0.4; logs.append(("tokens>=8", +0.4))
    if re.search(r"[.,;:!?]", s):
        score += 0.2; logs.append(("punctuation", +0.2))
    if s.endswith("."):
        score += 0.2; logs.append(("ends_with_period", +0.2))

    # Extra qualifiers
    if s.count(".") >= 2:  # multiple sentences
        score += 0.2; logs.append(("multi_sentence", +0.2))
    avg_token_len = sum(len(w) for w in words) / max(1, num_tokens)
    if avg_token_len >= 4:
        score += 0.1; logs.append(("avg_token_len>=4", +0.1))
    if any(stop in s.lower().split() for stop in {"the", "is", "of", "and", "in"}):
        score += 0.1; logs.append(("contains_stopwords", +0.1))

    # ---------- Negative signals ----------
    if _ALL_CAPS_RE.match(s):
        score -= 0.5; logs.append(("all_caps", -0.5))
    if _BULLET_RE.match(s):
        score -= 0.5; logs.append(("bullet", -0.5))
    if _TOC_DOTS_RE.search(s):
        score -= 0.5; logs.append(("toc_dots", -0.5))

    # Extra disqualifiers
    if num_tokens < 5:
        score -= 0.5; logs.append(("too_short", -0.5))
    if s.endswith(":"):
        score -= 0.3; logs.append(("ends_with_colon", -0.3))
    upper_ratio = sum(c.isupper() for c in s) / max(1, len(s))
    if upper_ratio > 0.7:
        score -= 0.4; logs.append(("upper_ratio_high", -0.4))
    digit_ratio = sum(c.isdigit() for c in s) / max(1, len(s))
    if digit_ratio > 0.5:
        score -= 0.4; logs.append(("digit_ratio_high", -0.4))
    symbol_ratio = sum(c in "-=*#_" for c in s) / max(1, len(s))
    if symbol_ratio > 0.3:
        score -= 0.3; logs.append(("symbol_ratio_high", -0.3))

    # ---------- Features ----------
    feat_dict: Dict[str, Any] = {}
    if features:
        if isinstance(features, dict):
            feat_dict = features
        else:
            feat_dict = getattr(features, "__dict__", {})

    if feat_dict.get("contains_text"):
        score += 0.1; logs.append(("contains_text", +0.1))
    if feat_dict.get("bold"):
        score -= 0.25; logs.append(("bold_penalty", -0.25))
    if (feat_dict.get("font_size", 0) or 0) >= 14:
        score -= 0.33; logs.append(("large_font_penalty", -0.33))

    final = max(0.0, min(1.0, score))

    if debug:
        print(f"[Paragraph scoring] text={text!r} → {final:.3f}")
        for name, delta in logs:
            print(f"  - {name}: {delta:+.2f}")

    return final

def detect_paragraphs(
    source: Union[Sequence[str], PlaintextContext],
    threshold: float = 0.55,
    label: str = "paragraph",
) -> List[ParagraphDetection]:
    lines = coerce_to_lines(source)
    preds: List[ParagraphDetection] = []

    for i, s in enumerate(lines):
        feats = None
        if extract_line_features:
            try:
                feats = extract_line_features(s)
            except Exception:
                feats = None

        sc = score_paragraph(s, features=feats)
        if sc >= threshold:
            preds.append(ParagraphDetection(i, label, sc))

    return preds
