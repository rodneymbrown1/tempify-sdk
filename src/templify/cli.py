# src/templify/cli.py
import argparse
import json
from pathlib import Path

from templify.core.workspace import Workspace
from templify.runner import generate_schemas_from_docx


def main():
    parser = argparse.ArgumentParser(prog="templify", description="Templify SDK CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # --- schema subcommand ---
    sch = sub.add_parser("schema", help="Generate JSON schema from a .docx")
    sch.add_argument("--in", dest="docx", required=True, help="Path to input .docx")
    sch.add_argument("--out", dest="outdir", help="Directory to write JSON schema")
    sch.add_argument("--expected", dest="expected", help="Path to expected titles JSON (optional)")
    sch.add_argument("--workspace", dest="wsroot", help="Workspace root (optional)")

    args = parser.parse_args()

    if args.cmd in ("schema", "configs"):  # accept both for now
        ws = Workspace(root_dir=args.wsroot) if args.wsroot else Workspace()

        expected_titles = None
        if args.expected:
            expected_titles = json.loads(Path(args.expected).read_text())

        schema = generate_schemas_from_docx(
            args.docx, ws=ws, expected_titles=expected_titles, output_dir=args.outdir
        )

        if args.outdir:
            # schema is a Path when --outdir is used
            print(f"Wrote schema: {schema}")
        else:
            # schema is a dict when no --outdir
            print(json.dumps(schema, indent=2))


if __name__ == "__main__":
    main()
