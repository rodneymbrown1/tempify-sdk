# src/templify/core/schema/utils/schema_saver.py
import os
import json
from pathlib import Path


class SchemaSaver:
    """
    Save a single Templify schema to disk as JSON.

    Usage:
        saver = SchemaSaver(schema)
        path = saver.save_to_file("output/")
    """

    def __init__(self, schema: dict):
        if not isinstance(schema, dict):
            raise ValueError("schema must be a dict")
        self.schema = schema

    def save_to_file(self, output_dir: str | Path, filename: str = "templify_schema.json") -> Path:
        """
        Write the schema JSON to the output directory.

        :param output_dir: Directory to write the file into.
        :param filename: Optional override for schema filename.
        :return: Path to the written JSON file.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        path = output_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.schema, f, indent=2)

        return path
