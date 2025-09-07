# templify/core/analysis/features.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, List
import re
import string

__all__ = ["LineFeatures", "extract_line_features", "batch_extract_features"]

# -----------------------------
# Precompiled regexes (speed!)
# -----------------------------

# Bullets: require a space after the glyph to avoid false positives on dashes in sentences.
_BULLET_RE = re.compile(r'^\s*([•·∙●◦○▪▸▶\-–—\*])\s+')

# Numbering prefixes: decimal/alpha/roman, allow ) or . and optional nesting like 1.1.1
_DECIMAL_RE = re.compile(r'^\s*((?:\d+\.)+\d+\.?|(?:\d+)[\.\)])\s+')
_ALPHA_RE = re.compile(r'^\s*(([A-Za-z])[\.\)])\s+')
_ROMAN_RE = re.compile(r'^\s*(\(?[ivxlcdmIVXLCDM]+\)?[\.\)])\s+')
_BRACKETED_RE = re.compile(r'^\s*\[((?:\d+|[A-Za-z]))\]\s+')

# Leader dots typical of TOC lines: many dots then page number at end.
_LEADER_DOTS_RE = re.compile(r'\.{3,}\s*\d+\s*$')

# URL-ish detector (very light; not a validator)
_URL_LIKE_RE = re.compile(r'(?i)\b(?:https?://|www\.)\S+')

# Sentence boundary heuristic: ., !, ? followed by space or end
_SENTENCE_RE = re.compile(r'[.!?](?=\s|$)')

# Collapse internal whitespace for text_norm
_WS_RE = re.compile(r'\s+')

# Treat these as punctuation for density calc
_EXTRA_PUNCT = "—–…“”‘’·•∙◦▪"

# -----------------------------
# Data model
# -----------------------------

@dataclass(frozen=True)
class LineFeatures:
    # Source
    text: str
    # Light-normalized for matching (trim/collapse only)
    text_norm: str

    # Shape
    token_count: int
    char_len: int
    sentence_count: int

    # Ratios
    uppercase_ratio: float       # uppercase letters / letters
    titlecase_rate: float        # titlecase tokens / alpha tokens
    digit_ratio: float           # digits / chars
    punct_density: float         # punctuation chars / chars

    # Flags
    ends_with_period: bool
    starts_with_bullet: bool
    bullet_glyph: Optional[str]
    numbering_prefix: Optional[str]   # "1.", "1.1", "a)", "iv.)", "[1]"
    indent_level: int
    has_leader_dots: bool
    trailing_colon: bool
    has_allcaps_word: bool
    contains_bar: bool           # e.g., "Name | Role"
    contains_emdash: bool        # em or en dash present
    contains_url_like: bool

# -----------------------------
# Public API
# -----------------------------

def extract_line_features(line: str, *, indent_level: int = 0) -> LineFeatures:
    """
    Extract fast, deterministic features from a single *already-normalized* line.
    Only light cleanup is applied to text_norm (strip + whitespace collapse).
    """
    # Preserve the incoming (post-intake) line text
    raw = line.rstrip("\n")

    # Light match-layer normalization
    text_norm = _normalize_for_match(raw)

    # Tokenization (on normalized text so counts are stable)
    tokens = _tokenize(text_norm)
    alpha_tokens = [t for t in tokens if any(ch.isalpha() for ch in t)]

    # Shape
    token_count = len(tokens)
    char_len = len(text_norm)
    sentence_count = _sentence_count(text_norm)

    # Ratios
    uppercase_ratio = _uppercase_ratio(text_norm)
    titlecase_rate = _titlecase_rate(alpha_tokens)
    digit_ratio = _digit_ratio(text_norm, char_len)
    punct_density = _punct_density(text_norm, char_len)

    # Flags (order matters slightly for performance)
    ends_with_period = text_norm.endswith(".")
    contains_bar = "|" in text_norm
    contains_emdash = ("—" in text_norm) or ("–" in text_norm)
    trailing_colon = text_norm.endswith(":")
    has_allcaps_word = any(_is_allcaps_word(t) for t in tokens)

    # Bullets & numbering prefixes
    starts_with_bullet, bullet_glyph = _detect_bullet_prefix(text_norm)
    numbering_prefix = _detect_numbering_prefix(text_norm)

    # TOC leader dots
    has_leader_dots = bool(_LEADER_DOTS_RE.search(text_norm))

    # URL-ish
    contains_url_like = bool(_URL_LIKE_RE.search(text_norm))

    return LineFeatures(
        text=raw,
        text_norm=text_norm,
        token_count=token_count,
        char_len=char_len,
        sentence_count=sentence_count,
        uppercase_ratio=uppercase_ratio,
        titlecase_rate=titlecase_rate,
        digit_ratio=digit_ratio,
        punct_density=punct_density,
        ends_with_period=ends_with_period,
        starts_with_bullet=starts_with_bullet,
        bullet_glyph=bullet_glyph,
        numbering_prefix=numbering_prefix,
        indent_level=indent_level,
        has_leader_dots=has_leader_dots,
        trailing_colon=trailing_colon,
        has_allcaps_word=has_allcaps_word,
        contains_bar=contains_bar,
        contains_emdash=contains_emdash,
        contains_url_like=contains_url_like,
    )


def batch_extract_features(lines: Sequence[str]) -> List[LineFeatures]:
    """Vectorized convenience wrapper over extract_line_features."""
    # If you later track true indent levels from DOCX/XML, pass them here.
    return [extract_line_features(ln, indent_level=0) for ln in lines]

# -----------------------------
# Private helpers (pure funcs)
# -----------------------------

def _normalize_for_match(s: str) -> str:
    """
    Light, non-lossy normalization for matching:
    - strip leading/trailing whitespace
    - collapse internal whitespace runs to a single space
    (No lowercasing; preserve casing for heading heuristics.)
    """
    s = s.strip()
    if not s:
        return s
    return _WS_RE.sub(" ", s)


def _tokenize(s: str) -> List[str]:
    # Simple whitespace tokenization; keeps punctuation attached (fine for our metrics)
    return s.split() if s else []


def _sentence_count(s: str) -> int:
    # Heuristic: count ., !, ? as sentence enders
    if not s:
        return 0
    return len(_SENTENCE_RE.findall(s))


def _uppercase_ratio(s: str) -> float:
    letters = [ch for ch in s if ch.isalpha()]
    if not letters:
        return 0.0
    ups = sum(1 for ch in letters if ch.isupper())
    return ups / len(letters)


def _titlecase_rate(tokens: Sequence[str]) -> float:
    if not tokens:
        return 0.0
    tc = sum(1 for t in tokens if _is_titlecase_word(t))
    return tc / len(tokens)


def _is_titlecase_word(w: str) -> bool:
    # Titlecase-ish: First char upper, rest lower (ignore non-alpha tail like ":" or ",")
    core = w.strip(string.punctuation)
    return len(core) >= 2 and core[0].isupper() and core[1:].islower()


def _is_allcaps_word(w: str) -> bool:
    core = w.strip(string.punctuation)
    # >=2 letters avoids counting "I" as ALLCAPS
    letters = [c for c in core if c.isalpha()]
    return len(letters) >= 2 and all(c.isupper() for c in letters)


def _digit_ratio(s: str, char_len: int) -> float:
    if char_len == 0:
        return 0.0
    digs = sum(1 for ch in s if ch.isdigit())
    return digs / char_len


def _punct_density(s: str, char_len: int) -> float:
    if char_len == 0:
        return 0.0
    punct_set = set(string.punctuation + _EXTRA_PUNCT)
    pn = sum(1 for ch in s if ch in punct_set)
    return pn / char_len


def _detect_bullet_prefix(s: str) -> tuple[bool, Optional[str]]:
    m = _BULLET_RE.match(s)
    if m:
        glyph = m.group(1)
        # Avoid treating hyphen-minus as bullet when it's a negative number like "-3.5"
        if glyph in "-–—*":
            # Check next non-space token; if it's purely digits, treat as not a bullet
            tail = s[m.end():].lstrip()
            if tail and tail[0].isdigit():
                return False, None
        return True, glyph
    return False, None


def _detect_numbering_prefix(s: str) -> Optional[str]:
    for pat in (_DECIMAL_RE, _BRACKETED_RE, _ROMAN_RE, _ALPHA_RE):
        m = pat.match(s)
        if m:
            return m.group(1).strip()
    return None
