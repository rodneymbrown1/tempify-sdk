# src/templify/cli.py
import argparse
import json
from pathlib import Path

from templify.core.workspace import Workspace
from templify.runner import generate_configs_from_docx


def main():
    parser = argparse.ArgumentParser(prog="templify", description="Templify SDK CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # --- configs subcommand ---
    cfg = sub.add_parser("configs", help="Generate JSON configs from a .docx")
    cfg.add_argument("--in", dest="docx", required=True, help="Path to input .docx")
    cfg.add_argument("--out", dest="outdir", help="Directory to write JSON configs")
    cfg.add_argument("--expected", dest="expected", help="Path to expected titles JSON (optional)")
    cfg.add_argument("--workspace", dest="wsroot", help="Workspace root (optional)")

    args = parser.parse_args()

    if args.cmd == "configs":
        # Workspace initialization
        ws = Workspace(root_dir=args.wsroot) if args.wsroot else Workspace()

        # Load expected titles if provided
        expected_titles = None
        if args.expected:
            expected_titles = json.loads(Path(args.expected).read_text())

        # Generate configs
        result = generate_configs_from_docx(
            args.docx, ws=ws, expected_titles=expected_titles, output_dir=args.outdir
        )

        # Output handling
        if args.outdir:
            titles_path, main_path = result
            print(f"Wrote configs:\n  Titles: {titles_path}\n  Main:   {main_path}")
        else:
            titles_cfg, main_cfg = result
            print(json.dumps({"titles": titles_cfg, "main": main_cfg}, indent=2))


if __name__ == "__main__":
    main()
