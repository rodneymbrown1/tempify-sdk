# src/templify/cli.py
import argparse
import json
from pathlib import Path

from templify.core.workspace import Workspace
from templify.core.utils.docx_intake import intake_docx
from templify.runner import build_schema


def main():
    parser = argparse.ArgumentParser(prog="templify", description="Templify SDK CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # --- schema subcommand ---
    sch = sub.add_parser("schema", help="Generate JSON schema from a .docx")
    sch.add_argument("--in", dest="docx", required=True, help="Path to input .docx")
    sch.add_argument("--out", dest="out", help="Optional path to write schema.json")
    sch.add_argument("--workspace", dest="wsroot", help="Optional workspace root (default: .templify or templify_workspace)")

    args = parser.parse_args()

    if args.cmd in ("schema", "configs"):  # accept both for now
        # Create workspace (default .templify if in git repo, otherwise templify_workspace)
        ws = Workspace(root_dir=args.wsroot) if args.wsroot else Workspace()

        # Intake the .docx into workspace (copy + unzip)
        intake = intake_docx(args.docx, ws)

        # Build schema
        schema = build_schema(
            document_xml_path=str(intake.key_files["document_xml"]),
            extract_dir=str(intake.unzip_dir),
        )

        # Always save schema into workspace
        ws_schema_path = ws.save_json("output_configs", "schema", schema)

        # Mirror to --out if provided
        if args.out:
            out_path = Path(args.out)
            out_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
            print(f"Schema saved: {ws_schema_path} (mirrored to {out_path})")
        else:
            # Show schema in terminal (pretty JSON)
            print(json.dumps(schema, indent=2))
            print(f"\n[Workspace copy saved at {ws_schema_path}]")


if __name__ == "__main__":
    main()
