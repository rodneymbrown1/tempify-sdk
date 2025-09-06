import os
import shutil
import json
import uuid
from datetime import datetime
from typing import Optional, Dict


def _default_root_dir() -> str:
    """
    Determine a smart default root directory for the workspace.
    - If inside a Git repo (cwd contains `.git/`), use `.templify/` (hidden).
    - Otherwise, use `templify_workspace/`.
    """
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, ".git")):
        return os.path.join(cwd, ".templify")
    return os.path.join(cwd, "templify_workspace")


class Workspace:
    """
    A unified storage system for managing Templify runs.
    Organizes input/output artifacts under a root directory,
    with optional per-run isolation via UUIDs.
    """

    def __init__(
        self,
        root_dir: Optional[str] = None,
        use_uuid: bool = False,
        custom_paths: Optional[Dict[str, str]] = None,
    ):
        """
        :param root_dir: Base directory for storing all artifacts.
                         Defaults to project-aware (./.templify or ./templify_workspace).
        :param use_uuid: Whether to create a unique run folder (timestamp+uuid).
        :param custom_paths: Optional overrides for default paths (dict of key → path).
        """
        # Root directory (project-aware default if not provided)
        if root_dir is None:
            root_dir = _default_root_dir()

        os.makedirs(root_dir, exist_ok=True)
        self.base_root = root_dir

        # Run isolation
        if use_uuid:
            self.run_id = datetime.now().strftime("%Y%m%dT%H%M%S") + "_" + str(uuid.uuid4())[:8]
        else:
            self.run_id = "default"

        # Full root for this run
        self.root_dir = os.path.join(self.base_root, self.run_id)
        os.makedirs(self.root_dir, exist_ok=True)

        # Default storage paths
        self.paths = {
            "input_docx": os.path.join(self.root_dir, "input", "docx"),
            "input_plaintext": os.path.join(self.root_dir, "input", "plaintext"),
            "input_unzipped": os.path.join(self.root_dir, "input", "unzipped"),
            "output_configs": os.path.join(self.root_dir, "output", "configs"),
            "output_docx": os.path.join(self.root_dir, "output", "docx"),
        }

        # Apply user overrides
        if custom_paths:
            self.paths.update(custom_paths)

        # Ensure directories exist
        for path in self.paths.values():
            if os.path.splitext(path)[1] == "":  # only make directories, not files
                os.makedirs(path, exist_ok=True)

    # -------------------------------------------------------------------------
    # Save/load helpers
    # -------------------------------------------------------------------------

    def save_json(self, key: str, name: str, data: dict) -> str:
        """
        Save JSON data under the given storage key.

        :param key: One of ['output_configs'] or any JSON-friendly directory.
        :param name: File name (without .json extension).
        :param data: Dict to be saved.
        :return: Path to the saved file.
        """
        path = os.path.join(self.paths[key], f"{name}.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

    def load_json(self, key: str, name: str) -> dict:
        """
        Load JSON data from a storage key.

        :param key: Key (e.g., 'output_configs').
        :param name: File name (without .json extension).
        :return: Parsed dict.
        """
        path = os.path.join(self.paths[key], f"{name}.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_file(self, key: str, src_path: str, dest_name: Optional[str] = None) -> str:
        """
        Save a file into the workspace under the given key.

        :param key: One of ['input_docx', 'input_plaintext', 'input_unzipped', 'output_docx'].
        :param src_path: Path to source file.
        :param dest_name: Optional new file name.
        :return: Path to the saved file.
        """
        if dest_name:
            dest_path = os.path.join(self.paths[key], dest_name)
        else:
            dest_path = os.path.join(self.paths[key], os.path.basename(src_path))

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(src_path, dest_path)
        return dest_path

    def directory(self, key: str) -> str:
        """Get the directory path for a given storage key."""
        return self.paths[key]
