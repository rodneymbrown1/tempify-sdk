import re
import unicodedata

# -------------------------------
# Universal line normalizer
# -------------------------------
# Common Unicode whitespace (Zs + NBSP variants) → plain space
_WS_RX = re.compile(r"[\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000\u2007]")

# Zero-width & direction/invisible marks to strip:
# ZW: 200B-200D, FEFF; WORD JOINER 2060; BIDI marks/runs 200E-200F, 202A-202E, 2066-2069
_INVIS_RX = re.compile(r"[\u200B\u200C\u200D\u2060\uFEFF\u200E\u200F\u202A-\u202E\u2066-\u2069]")

# Dash/hyphen variants → '-'
_DASH_TABLE = str.maketrans({
    "‐": "-",  # U+2010
    "-": "-",  # ASCII hyphen-minus
    "‒": "-",  # U+2012
    "–": "-",  # U+2013 en dash
    "—": "-",  # U+2014 em dash
    "―": "-",  # U+2015 horizontal bar
})

# Quote variants → ASCII quotes
_QUOTE_TABLE = str.maketrans({
    "“": '"', "”": '"', "„": '"', "«": '"', "»": '"',
    "‘": "'", "’": "'", "‚": "'", "‹": "'", "›": "'",
})

# Bullet variants → canonical bullet (helps consistent detection/logging)
_BULLET_TABLE = str.maketrans({
    "•": "•", "▪": "•", "●": "•", "◦": "•", "·": "•",
})

# Collapse multiple spaces/tabs → single space
_SPACES_RX = re.compile(r"[ \t]+")


def normalize_line(text: str) -> str:
    """
    Canonicalize a single logical 'line' for downstream heuristics.

    Steps:
      1) NFKC unicode normalization (compatibility fold)
      2) Replace exotic spaces with plain space
      3) Strip zero-width/invisible control marks (ZWSP/FEFF/BIDI etc.)
      4) Canonicalize dashes, quotes, bullets
      5) Collapse runs of spaces/tabs to a single space
      6) Trim outer whitespace

    Safe for both DOCX-extracted text and plaintext.
    """
    if text is None:
        return ""

    s = str(text)

    # 1) Unicode canonicalization
    s = unicodedata.normalize("NFKC", s)

    # 2) Normalize exotic spaces to regular space
    s = _WS_RX.sub(" ", s)

    # 3) Remove invisible / bidi marks
    s = _INVIS_RX.sub("", s)

    # 4) Canonical punctuation families
    s = s.translate(_DASH_TABLE).translate(_QUOTE_TABLE).translate(_BULLET_TABLE)

    # 5) Collapse internal spaces/tabs
    s = _SPACES_RX.sub(" ", s)

    # 6) Trim
    return s.strip()