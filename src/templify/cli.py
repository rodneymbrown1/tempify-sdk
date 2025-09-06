import argparse
from pathlib import Path
import json
from templify.core.workspace import Workspace
from templify.runner import generate_configs_from_docx

def main():
    p = argparse.ArgumentParser(prog="templify", description="Templify SDK CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("configs", help="Generate JSON configs from a .docx")
    c.add_argument("--in", dest="docx", required=True, help="Path to input .docx")
    c.add_argument("--out", dest="outdir", help="Directory to write JSON configs")
    c.add_argument("--expected", dest="expected", help="Path to expected titles JSON (optional)")
    c.add_argument("--workspace", dest="wsroot", help="Workspace root (optional)")

    args = p.parse_args()

    if args.cmd == "configs":
        ws = Workspace(root_dir=args.wsroot) if args.wsroot else Workspace()
        expected_titles = None
        if args.expected:
            expected_titles = json.loads(Path(args.expected).read_text())

        result = generate_configs_from_docx(
            args.docx, ws=ws, expected_titles=expected_titles, output_dir=args.outdir
        )

        if args.outdir:
            titles_path, main_path = result
            print(f"Wrote:\n  {titles_path}\n  {main_path}")
        else:
            titles_cfg, main_cfg = result
            print(json.dumps({"titles": titles_cfg, "main": main_cfg}, indent=2)) 
            
