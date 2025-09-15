# src/templify/runner.py
from pathlib import Path
from typing import Optional, Union

from templify.core.workspace import Workspace
from templify.core.utils.docx_intake import intake_docx
from templify.core.schema.templify_schema_builder import TemplifySchemaBuilder
from templify.core.schema.utils.schema_saver import SchemaSaver


def _generate_schemas_core(
    docx_path: Union[str, Path],
    extract_dir: Optional[Union[str, Path]] = None,
    expected_titles=None,
    output_dir: Optional[Union[str, Path]] = None,
) -> dict | Path:
    """
    LOW-LEVEL CORE: expects path to word/document.xml (already unzipped).
    Returns a schema dict (in-memory) or Path (if saved).
    """
    parser = TemplifySchemaBuilder(str(docx_path), str(extract_dir) if extract_dir else None)
    schema = parser.run()

    if output_dir:
        saver = SchemaSaver(schema)
        return saver.save_to_file(output_dir)

    return schema


def generate_schemas_from_docx(
    docx_file: Union[str, Path],
    *,
    ws: Optional[Workspace] = None,
    expected_titles=None,
    output_dir: Optional[Union[str, Path]] = None,
) -> dict | Path:
    """
    PIPELINE WRAPPER: accepts a .docx, unzips into workspace, then calls the core.
    """
    ws = ws or Workspace()
    intake = intake_docx(docx_file, ws)  # IntakeResult dataclass

    document_xml = intake.key_files.get("document_xml")
    if document_xml is None:
        raise RuntimeError("intake_docx did not produce a word/document.xml path")

    return _generate_schemas_core(
        docx_path=document_xml,
        extract_dir=intake.unzip_dir,
        expected_titles=expected_titles,
        output_dir=output_dir,
    )


def generate_schemas_from_xml(
    document_xml_path: Union[str, Path],
    extract_dir: Optional[Union[str, Path]] = None,
    expected_titles=None,
    output_dir: Optional[Union[str, Path]] = None,
) -> dict | Path:
    """
    Low-level entrypoint: parse WordprocessingML (word/document.xml) into a Templify schema.

    Returns:
        - dict if output_dir is None
        - Path if output_dir is provided
    """
    parser = TemplifySchemaBuilder(str(document_xml_path), str(extract_dir) if extract_dir else None, expected_titles)
    schema = parser.run()

    if output_dir:
        saver = SchemaSaver(schema)
        return saver.save_to_file(output_dir)

    return schema


# Back-compat alias (old name)
generate_schemas = generate_schemas_from_xml
