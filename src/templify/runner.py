# src/templify/runner.py
from pathlib import Path
from typing import Optional, Union, Tuple

from templify.core.workspace import Workspace
from templify.core.utils.docx_intake import intake_docx
from templify.core.schema.templify_schema_builder import TemplifySchemaBuilder
from templify.core.schema.utils.schema_saver import SchemaSaver


def _generate_configs_core(
    docx_path: Union[str, Path],
    extract_dir: Optional[Union[str, Path]] = None,
    expected_titles=None,
    output_dir: Optional[Union[str, Path]] = None,
) -> Tuple[dict, dict] | Tuple[Path, Path]:
    """
    LOW-LEVEL CORE: expects path to word/document.xml (already unzipped).
    """
    parser = TemplifySchemaBuilder(str(docx_path), str(extract_dir) if extract_dir else None, expected_titles)
    parser.run()

    if output_dir:
        exporter = SchemaSaver(parser.titles_config, parser.docx_config)
        titles_path_str, main_path_str = exporter.save_to_files(str(output_dir))
        # Return Path objects (clean, test-friendly API)
        return Path(titles_path_str), Path(main_path_str)

    return parser.titles_config, parser.docx_config


def generate_configs_from_docx(
    docx_file: Union[str, Path],
    *,
    ws: Optional[Workspace] = None,
    expected_titles=None,
    output_dir: Optional[Union[str, Path]] = None,
) -> Tuple[dict, dict] | Tuple[Path, Path]:
    """
    PIPELINE WRAPPER: accepts a .docx, unzips into workspace, then calls the core.
    """
    ws = ws or Workspace()
    intake = intake_docx(docx_file, ws)  # IntakeResult dataclass

    document_xml = intake.key_files.get("document_xml")
    if document_xml is None:
        raise RuntimeError("intake_docx did not produce a word/document.xml path")

    return _generate_configs_core(
        docx_path=document_xml,
        extract_dir=intake.unzip_dir,
        expected_titles=expected_titles,
        output_dir=output_dir,
    )


def generate_configs_from_xml(
    document_xml_path: Union[str, Path],
    extract_dir: Optional[Union[str, Path]] = None,
    expected_titles=None,
    output_dir: Optional[Union[str, Path]] = None,
) -> Tuple[dict, dict] | Tuple[Path, Path]:
    """
    Low-level entrypoint: parse WordprocessingML (word/document.xml) into Templify configs.

    Args:
        document_xml_path: Path to word/document.xml (already unzipped).
        extract_dir: Root of the unzipped .docx (needed for styles/numbering/etc.).
        expected_titles: Optional list/dict of titles to validate/guide parsing.
        output_dir: If provided, writes JSON files and returns their Paths;
                    otherwise returns config dicts.

    Returns:
        If output_dir is None -> (titles_config: dict, docx_config: dict)
        Else                  -> (titles_path: Path, main_path: Path)
    """
    parser = TemplifySchemaBuilder(str(document_xml_path), str(extract_dir) if extract_dir else None, expected_titles)
    parser.run()

    if output_dir:
        exporter = SchemaSaver(parser.titles_config, parser.docx_config)
        titles_path_str, main_path_str = exporter.save_to_files(str(output_dir))
        return Path(titles_path_str), Path(main_path_str)

    return parser.titles_config, parser.docx_config


# Back-compat alias (old name)
generate_configs = generate_configs_from_xml
