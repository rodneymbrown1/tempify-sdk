from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from templify.core.schema.templify_schema_builder import TemplifySchemaBuilder


def build_schema(document_xml_path: str, extract_dir: str | None = None) -> dict:
    """
    Build a Templify schema from a document.xml and (optionally) its extracted DOCX folder.

    Parameters
    ----------
    document_xml_path : str
        Path to the `document.xml` file.
    extract_dir : str | None
        Path to the extracted DOCX directory (unzipped). Required for some features.

    Returns
    -------
    dict
        The generated Templify schema.
    """
    builder = TemplifySchemaBuilder(document_xml_path=document_xml_path, docx_extract_dir=extract_dir)
    return builder.run()


def main(argv: list[str] | None = None) -> None:
    """
    CLI entrypoint for running schema extraction.

    Example:
        python -m templify.runner --document path/to/document.xml --extract path/to/unzipped --output out.json
    """
    parser = argparse.ArgumentParser(description="Templify schema runner")
    parser.add_argument("--document", "-d", required=True, help="Path to document.xml")
    parser.add_argument("--extract", "-e", required=False, help="Path to extracted DOCX folder")
    parser.add_argument("--output", "-o", required=False, help="Output JSON file (default: stdout)")

    args = parser.parse_args(argv)

    schema = build_schema(args.document, args.extract)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    else:
        json.dump(schema, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
