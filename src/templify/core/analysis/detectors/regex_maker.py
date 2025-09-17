import re
from dataclasses import dataclass
from typing import List, Sequence, Union
from templify.core.analysis.utils.plaintext_context import PlaintextContext
from templify.core.analysis.detectors.utils import coerce_to_lines
import logging
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class RegexDetection:
    line_idx: int
    title: str         # raw line text
    score: float
    pattern: str
    label: str         # classification (EMAIL, PHONE, etc.)
    method: str = "regex"



# --- Normalization helpers ---

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

MONTH_REGEX = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"


def normalize_to_regex(line: str) -> str:
    """Convert a raw line of text into a generalized regex pattern."""

    text = line.strip()
    if not text:
        return r"^\s*$"

    # --- Special structures (high confidence) ---
    if re.match(r"^[\w\.-]+@[\w\.-]+\.[A-Za-z]{2,}$", text):  # Email
        return r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    if re.match(r"^https?://", text):  # URL
        return r"^https?://[^\s]+$"

    if re.match(r"^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$", text):  # Phone
        return r"^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$"

    if re.match(rf"^{MONTH_REGEX}\s+\d{{4}}$", text):  # Date: MMM YYYY
        return rf"^{MONTH_REGEX}\s+\d{{4}}$"

    if re.match(r"^\d{2}/\d{2}/\d{4}$", text):  # Date: MM/DD/YYYY
        return r"^\d{2}/\d{2}/\d{4}$"

    if re.match(r"^\d+[\.\)]\s+", text):  # Numbered list
        return r"^\d+[\.\)]\s+[A-Za-z]+.*$"

    if re.match(r"^[\u2022\-\*]\s+", text):  # Bulleted list
        return r"^[\u2022\-\*]\s+[A-Za-z]+.*$"

    if re.match(r"^[A-Za-z\s]+:\s*$", text):  # Heading with colon
        return r"^[A-Za-z\s]+:\s*$"

    # --- Fallback: tokenizer-based normalization ---
    tokens = re.findall(r"[A-Za-z]+|\d+|[^\w\s]|\s+", text)
    regex_parts: list[str] = []

    for tok in tokens:
        if tok.isspace():
            regex_parts.append(r"\s+")
        elif re.fullmatch(r"\d{4}", tok):   # 4-digit year
            regex_parts.append(r"\d{4}")
        elif tok.isdigit():
            regex_parts.append(r"\d+")
        elif tok in {"-", "•", "*"}:        # bullet-like
            regex_parts.append(r"[\u2022\-\*]")
        elif re.fullmatch(r"[A-Za-z]+", tok):
            if tok in {"Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"}:
                regex_parts.append(MONTH_REGEX)
            else:
                regex_parts.append(r"[A-Za-z]+")
        else:
            regex_parts.append(re.escape(tok))  # literal punctuation

    return "^" + "".join(regex_parts) + "$"

def _regex_score(pattern: str) -> float:
    """Simple scoring heuristic: more structure = higher score."""
    if any(tok in pattern for tok in [r"\d{4}", r"@", "https?", r"\d+\)", r"\d+\.", MONTH_REGEX]):
        return 0.6
    if "[A-Za-z]+" in pattern and r"\d+" in pattern:
        return 0.5
    return 0.3


def regex_fallback(
    lines: Union[Sequence[str], PlaintextContext],
) -> List[RegexDetection]:
    """Fallback detection: always returns a regex for every line."""
    L = coerce_to_lines(lines)
    hits: List[RegexDetection] = []

    for i, s in enumerate(L):
        text = (s or "").strip()
        pattern = normalize_to_regex(text)
        score = _regex_score(pattern)
        classification = classify_regex(pattern, text)
        hits.append(
            RegexDetection(
                line_idx=i,
                title=text,
                score=score,
                pattern=pattern,
                label=f"REGEX-{classification}",
            )
        )

    return hits





def classify_regex(pattern: str, text: str) -> str:
    """Map regex pattern (and raw text) to a descriptor type."""
    if "@" in pattern:
        return "EMAIL"
    if "https?" in pattern:
        return "URL"
    if r"\d{3}" in pattern and r"\d{4}" in pattern and "(" in pattern:
        return "PHONE"
    if MONTH_REGEX in pattern or r"\d{2}/\d{2}/\d{4}" in pattern:
        return "DATE"
    if pattern.startswith(r"^\d+[\.\)]"):
        return "L-NUMBERED"
    if pattern.startswith(r"^[\u2022\-\*]"):
        return "L-BULLET"
    if pattern.endswith(":$"):
        return "H-COLON"
    return "UNKNOWN"

def match(lines, domain=None, **kwargs) -> RegexDetection | None:
    logger.debug("→ using regex maker fallback")
    if isinstance(lines, str):
        lines = [lines]

    logger.debug(f"→ input lines: {lines}")
    hits = regex_fallback(lines)

    if not hits:
        return None

    # pick the highest-scoring detection
    best = max(hits, key=lambda r: r.score)
    logger.debug(f"→ regex best match: {best}")
    return best
