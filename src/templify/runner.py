from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from templify.core.schema.build_schema import TemplifySchemaBuilder
from templify.core.schema_runner.run_schema import TemplifySchemaRunner


def build_schema(document_xml_path: str, extract_dir: str | None = None) -> dict:
    """
    Build a Templify schema from a document.xml and (optionally) its extracted DOCX folder.
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


def run_schema(schema_path: str, output_path: str | None = None, source_override: str | None = None) -> None:
    """
    Run an existing schema JSON through TemplifySchemaRunner to generate a DOCX.
    """
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))

    if source_override:
        schema["source_docx"] = source_override

    if "source_docx" not in schema:
        raise ValueError("Schema missing 'source_docx'. Provide one via schema or source_override.")

    runner = TemplifySchemaRunner(schema)
    results = runner.run()

    if output_path:
        runner.document.save(output_path)
        print(f"[Templify] DOCX written to {output_path}")
    else:
        # Default: print debug trace
        json.dump(
            [{"text": t, "type": d.get("type"), "style": s} for t, d, s in results],
            sys.stdout,
            indent=2,
        )


if __name__ == "__main__":
    main()
