# src/templify/core/utils/plaintext_intake.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, Literal, Dict, List
import uuid
import unicodedata
import hashlib
import re
from templify.core.workspace import Workspace  
from templify.core.analysis.detectors.heuristic_classifier import classify_lines


LineEnding = Literal["LF", "CRLF", "CR", "MIXED", "UNKNOWN"]

_ZW_RE = re.compile(r"[\u200B-\u200D\uFEFF]")  # zero-width chars


@dataclass(frozen=True)
class PlaintextIntakeResult:
    stored_plaintext_path: Optional[Path]
    text_raw: str
    text_norm: str
    lines: List[str]
    encoding: str
    bom_stripped: bool
    original_line_ending: LineEnding
    normalized_line_ending: LineEnding
    checksum_sha256: str
    stats: Dict[str, int]
    line_patterns: Optional[List[Dict[str, object]]] = None  # <-- new: classification metadata


# -------------------------
# Low-level helpers
# -------------------------
def _detect_line_ending(s: str) -> LineEnding:
    crlf = s.count("\r\n")
    cr = s.count("\r") - crlf
    lf = s.count("\n") - crlf
    kinds = sum(1 for n in (crlf, cr, lf) if n > 0)
    if kinds == 0:
        return "UNKNOWN"
    if kinds > 1:
        return "MIXED"
    if crlf > 0:
        return "CRLF"
    if cr > 0:
        return "CR"
    return "LF"


def _normalize_text(
    s: str,
    *,
    unicode_form: Literal["NFC", "NFKC"] = "NFC",
    strip_zero_width: bool = True,
    expand_tabs: Optional[int] = None,
    ensure_final_newline: bool = True,
) -> str:
    # Remove BOM if present at start
    bom_stripped = s.lstrip("\ufeff")
    # Unify line endings to \n
    bom_stripped = bom_stripped.replace("\r\n", "\n").replace("\r", "\n")
    # Unicode normalization
    s_norm = unicodedata.normalize(unicode_form, bom_stripped)
    # Strip zero-width characters
    if strip_zero_width:
        s_norm = _ZW_RE.sub("", s_norm)
    # Expand tabs if requested
    if isinstance(expand_tabs, int) and expand_tabs > 0:
        s_norm = s_norm.expandtabs(expand_tabs)
    # Guarantee trailing newline (helps later joins)
    if ensure_final_newline and (not s_norm.endswith("\n")):
        s_norm += "\n"
    return s_norm


def _decode_bytes(b: bytes) -> tuple[str, str, bool]:
    # Try utf-8 with BOM removal first (utf-8-sig)
    try:
        s = b.decode("utf-8-sig")
        # If it decodes under utf-8-sig, BOM is stripped automatically
        return s, "utf-8", True
    except UnicodeDecodeError:
        pass
    # Try strict utf-8 next
    try:
        s = b.decode("utf-8")
        return s, "utf-8", False
    except UnicodeDecodeError:
        # As a last resort, latin-1 (lossless byte mapping)
        s = b.decode("latin-1", errors="strict")
        return s, "latin-1", False


# -------------------------
# Main intake
# -------------------------
def intake_plaintext(
    source: Union[str, Path, bytes],
    *,
    workspace: Optional[Workspace] = None,
    filename: Optional[str] = None,
    unicode_form: Literal["NFC", "NFKC"] = "NFC",
    strip_zero_width: bool = True,
    expand_tabs: Optional[int] = None,
    ensure_final_newline: bool = True,
    max_bytes: int = 8 * 1024 * 1024,  # 8 MB guardrail
) -> PlaintextIntakeResult:
    """
    Ingest plaintext from a string, file path, or raw bytes.
    - Normalizes encoding/line endings/unicode.
    - Splits into lines (preserving blank lines).
    - Optionally stores normalized text in workspace.input_plaintext.
    - Optionally classifies each line using detection heuristics.

    Returns PlaintextIntakeResult with both raw and normalized views,
    plus optional line_patterns classification metadata.
    """
    # 1) Load into bytes if needed
    if isinstance(source, Path):
        if not source.exists():
            raise FileNotFoundError(f"No such file: {source}")
        b = source.read_bytes()
    elif isinstance(source, bytes):
        b = source
    elif isinstance(source, str):
        # Treat as content, not path
        b = source.encode("utf-8")
    else:
        raise TypeError(f"Unsupported source type: {type(source)}")

    if len(b) > max_bytes:
        raise ValueError(f"Plaintext exceeds max_bytes ({max_bytes}). Got {len(b)} bytes.")

    # 2) Decode
    text_decoded, encoding, bom_removed = _decode_bytes(b)

    # 3) Detect original line ending on raw text
    original_le = _detect_line_ending(text_decoded)

    # 4) Normalize
    text_norm = _normalize_text(
        text_decoded,
        unicode_form=unicode_form,
        strip_zero_width=strip_zero_width,
        expand_tabs=expand_tabs,
        ensure_final_newline=ensure_final_newline,
    )
    normalized_le = "LF" if "\n" in text_norm else "UNKNOWN"

    # 5) Lines
    lines = text_norm.splitlines()  # drops trailing newline in split result; that's okay

    # 6) Stats & checksum
    stats = {
        "num_chars_raw": len(text_decoded),
        "num_chars_norm": len(text_norm),
        "num_lines": len(lines),
        "num_blank_lines": sum(1 for ln in lines if ln.strip() == ""),
        "num_tabs_raw": text_decoded.count("\t"),
    }
    checksum = hashlib.sha256(text_norm.encode("utf-8")).hexdigest()

    # 7) Optional storage in Workspace
    stored_path: Optional[Path] = None
    if workspace is not None and hasattr(workspace, "paths") and "input_plaintext" in getattr(workspace, "paths", {}):
        fname = filename or f"plaintext_{uuid.uuid4().hex}.txt"
        stored_dir = Path(workspace.paths["input_plaintext"])
        stored_dir.mkdir(parents=True, exist_ok=True)
        stored_path = stored_dir / fname
        stored_path.write_text(text_norm, encoding="utf-8")

    # 8) Optional pattern detection
    line_patterns = None
    if classify_lines is not None:
        try:
            line_patterns = classify_lines(lines)
        except Exception:
            line_patterns = None

    return PlaintextIntakeResult(
        stored_plaintext_path=stored_path,
        text_raw=text_decoded,
        text_norm=text_norm,
        lines=lines,
        encoding=encoding,
        bom_stripped=bom_removed,
        original_line_ending=original_le,
        normalized_line_ending=normalized_le,
        checksum_sha256=checksum,
        stats=stats,
        line_patterns=line_patterns,
    )
