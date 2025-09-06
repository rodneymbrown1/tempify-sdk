from dataclasses import dataclass
from pathlib import Path
import shutil
import zipfile
import uuid
from typing import Dict, Optional, Union

from templify.core.workspace import Workspace

# ---- Return type expected by runner/tests ----
@dataclass(frozen=True)
class IntakeResult:
    stored_docx_path: Path
    unzip_dir: Path
    key_files: Dict[str, Optional[Path]]  # {"document_xml": Path | None, ...}

_REQUIRED_DOCX_MEMBERS = {
    "[Content_Types].xml",
    "word/document.xml",
}

# Simple guards (tune if you want stricter limits)
_MAX_TOTAL_UNCOMPRESSED = 200 * 1024 * 1024  # 200 MB
_MAX_MEMBER_COUNT = 5000


def _validate_docx_archive(docx_path: Path) -> None:
    if not docx_path.exists():
        raise FileNotFoundError(f"No such file: {docx_path}")
    if docx_path.suffix.lower() != ".docx":
        raise ValueError(f"Expected a .docx file, got: {docx_path.name}")
    try:
        with zipfile.ZipFile(docx_path, "r") as zf:
            names = set(zf.namelist())
            if len(names) > _MAX_MEMBER_COUNT:
                raise ValueError(f"DOCX contains too many members ({len(names)} > {_MAX_MEMBER_COUNT})")
            missing = [m for m in _REQUIRED_DOCX_MEMBERS if m not in names]
            if missing:
                raise ValueError(f"DOCX missing required members {missing}.")
            total_uncompressed = sum(i.file_size for i in zf.infolist())
            if total_uncompressed > _MAX_TOTAL_UNCOMPRESSED:
                raise ValueError(f"DOCX uncompressed size too large ({total_uncompressed} bytes)")
    except zipfile.BadZipFile as e:
        raise ValueError(f"Invalid DOCX (not a valid zip): {docx_path}") from e


def _safe_extractall(zf: zipfile.ZipFile, dest_dir: Path) -> None:
    """Prevent zip-slip by ensuring each member stays under dest_dir."""
    base = dest_dir.resolve()
    for info in zf.infolist():
        member = Path(info.filename)
        if member.is_absolute():
            raise ValueError(f"Archive contains absolute path: {info.filename}")
        out_path = (base / member).resolve()
        if not str(out_path).startswith(str(base)):
            raise ValueError(f"Archive contains unsafe path: {info.filename}")
        if info.is_dir():
            out_path.mkdir(parents=True, exist_ok=True)
            continue
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(info, "r") as src, open(out_path, "wb") as dst:
            shutil.copyfileobj(src, dst)


def _extract_docx(docx_path: Path, dest_dir: Path) -> Dict[str, Optional[Path]]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(docx_path, "r") as zf:
            _safe_extractall(zf, dest_dir)
    except Exception:
        shutil.rmtree(dest_dir, ignore_errors=True)
        raise

    def opt(rel: str) -> Optional[Path]:
        p = dest_dir / rel
        return p if p.exists() else None

    return {
        "content_types_xml": opt("[Content_Types].xml"),
        "document_xml": opt("word/document.xml"),
        "styles_xml": opt("word/styles.xml"),
        "numbering_xml": opt("word/numbering.xml"),
        "rels_dir": opt("_rels"),
        "word_dir": opt("word"),
        "word_rels_dir": opt("word/_rels"),
    }


def intake_docx(
    src_docx: Union[str, Path],
    ws: Workspace,
    *,
    unzip_subdir: Optional[str] = None
) -> IntakeResult:
    """
    Copy a .docx into the workspace and unzip it for parsing.
    Returns: IntakeResult(stored_docx_path, unzip_dir, key_files)
    """
    # Ensure workspace has paths
    for key in ("input_docx", "input_unzipped"):
        if key not in ws.paths:
            raise KeyError(f"Workspace missing required path: {key}")

    src = Path(src_docx).expanduser().resolve()
    _validate_docx_archive(src)

    # 1) Copy original .docx
    input_docx_dir = Path(ws.paths["input_docx"])
    input_docx_dir.mkdir(parents=True, exist_ok=True)
    base = src.name
    dest = input_docx_dir / base
    if dest.exists():
        dest = input_docx_dir / f"{src.stem}__{uuid.uuid4().hex[:8]}{src.suffix}"
    shutil.copy2(src, dest)

    # 2) Unzip into dedicated subdir
    unzip_root = Path(ws.paths["input_unzipped"])
    unzip_root.mkdir(parents=True, exist_ok=True)
    unzip_subdir = unzip_subdir or f"{src.stem}__{uuid.uuid4().hex[:8]}"
    unzip_dir = (unzip_root / unzip_subdir).resolve()

    key_files = _extract_docx(dest, unzip_dir)
    if not key_files.get("document_xml"):
        shutil.rmtree(unzip_dir, ignore_errors=True)
        raise RuntimeError("Extraction succeeded but word/document.xml not found.")

    return IntakeResult(stored_docx_path=dest, unzip_dir=unzip_dir, key_files=key_files)

# Optional alias so both names work:
unzip_docx_to_workspace = intake_docx
