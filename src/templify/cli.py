from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from docx import Document
from templify.core.workspace import Workspace
from templify.core.utils.docx_intake import intake_docx
from templify.core.schema.build_schema import TemplifySchemaBuilder
from templify.core.schema_runner.run_schema import TemplifySchemaRunner


def build_schema(document_xml_path: str, extract_dir: str | None = None, source_docx: str | None = None) -> dict:
    """
    Build a Templify schema from a document.xml and (optionally) its extracted DOCX folder.
    """
    builder = TemplifySchemaBuilder(
        document_xml_path=document_xml_path,
        docx_extract_dir=extract_dir,
        source_docx=source_docx,
    )
    return builder.run()


def main():
    parser = argparse.ArgumentParser(prog="templify", description="Templify SDK CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # --- schema subcommand ---
    sch = sub.add_parser("schema", help="Generate JSON schema from a .docx")
    sch.add_argument("--in", dest="docx", required=True, help="Path to input .docx")
    sch.add_argument("--out", dest="out", help="Optional path to write schema.json")
    sch.add_argument("--workspace", dest="wsroot", help="Optional workspace root (default: .templify or templify_workspace)")

    # --- run subcommand ---
    runp = sub.add_parser("run", help="Generate a DOCX from an existing schema.json")
    runp.add_argument("--schema", dest="schema", required=True, help="Path to schema.json")
    runp.add_argument("--out", dest="out", help="Path to save generated .docx")
    runp.add_argument("--source", dest="source", help="Optional override for source .docx")

    args = parser.parse_args()

    if args.cmd in ("schema", "configs"):
        ws = Workspace(root_dir=args.wsroot) if args.wsroot else Workspace()

        intake = intake_docx(args.docx, ws)

        schema = build_schema(
            document_xml_path=str(intake.key_files["document_xml"]),
            extract_dir=str(intake.unzip_dir),
            source_docx=str(intake.stored_docx_path),
        )

        ws_schema_path = ws.save_json("output_configs", "schema", schema)

        if args.out:
            out_path = Path(args.out)
            out_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
            print(f"Schema saved: {ws_schema_path} (mirrored to {out_path})")
        else:
            print(json.dumps(schema, indent=2))
            print(f"\n[Workspace copy saved at {ws_schema_path}]")

    elif args.cmd == "run":
        run_schema(
            schema_path=args.schema,
            output_path=args.out,
            source_override=args.source,
        )


def run_schema(schema_path: str, output_path: str | None = None, source_override: str | None = None) -> None:
    """
    Run an existing schema JSON through TemplifySchemaRunner to generate a DOCX.

    :param schema_path: Path to schema.json
    :param output_path: Optional output DOCX path
    :param source_override: Optional override for schema["source_docx"]
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
        # Default: print debug trace of results
        json.dump(
            [{"text": t, "type": d.get("type"), "style": s} for t, d, s in results],
            sys.stdout,
            indent=2,
        )

if __name__ == "__main__":
    main()
