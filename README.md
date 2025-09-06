📦 Templify SDK

Templify is a Python SDK for parsing, analyzing, and restructuring Microsoft Word (.docx) files into structured JSON configs. It provides a consistent workspace for managing all artifacts (input DOCX, extracted plaintext, generated configs, and output DOCX).

🚀 Features
Parse WordprocessingML (document.xml) into structured JSON.
Generate titles_config.json and docx_config.json automatically.
Save and organize artifacts in a workspace directory.
Project-aware defaults:
In Git repos → .templify/ (hidden, ignored by Git).
Outside repos → templify_workspace/.
Optional UUID run isolation (no collisions when processing multiple DOCX files).
Fully configurable storage paths.
📂 Workspace Layout
By default, each run gets its own workspace folder:
templify_workspace/               # or .templify/ if inside a Git repo
└── default/                      # or <timestamp_uuid> if use_uuid=True
    ├── input/
    │   ├── docx/                 # original input DOCX files
    │   ├── plaintext/            # extracted plaintext (optional)
    │   └── unzipped/             # exploded Word XML
    └── output/
        ├── configs/              # titles_config.json, docx_config.json
        └── docx/                 # final generated DOCX

⚡ Quickstart
from templify import generate_configs
from templify.core.workspace import Workspace

# Run end-to-end: parse DOCX -> JSON configs
titles_cfg, main_cfg = generate_configs("word/document.xml")

# Use a custom workspace (persist results)
ws = Workspace(root_dir="project_runs", use_uuid=True)

# Save configs to workspace
ws.save_json("output_configs", "titles", titles_cfg)
ws.save_json("output_configs", "main", main_cfg)

# Save original input DOCX (optional)
ws.save_file("input_docx", "my_input.docx")

# Save output DOCX
ws.save_file("output_docx", "templified.docx")
⚙️ Configuration
Workspace options
Workspace(
    root_dir=None,        # default = .templify/ (if git repo) or ./templify_workspace/
    use_uuid=False,       # set True to isolate runs by timestamp+uuid
    custom_paths=None     # dict of key → custom path overrides
)

Available storage keys:
input_docx
input_plaintext
input_unzipped
output_configs
output_docx
