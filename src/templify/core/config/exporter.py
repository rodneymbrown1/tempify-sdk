# src/templify/core/config/exporter.py

import os
import json


class ConfigExporter:
    """
    Exports Templify configs (titles_config and docx_config) to disk as JSON files.

    Usage:
        exporter = ConfigExporter(titles_config, docx_config)
        exporter.save_to_files("output/")
    """

    def __init__(self, titles_config, docx_config):
        if not isinstance(titles_config, dict):
            raise ValueError("titles_config must be a dict")
        if not isinstance(docx_config, dict):
            raise ValueError("docx_config must be a dict")

        self.titles_config = titles_config
        self.docx_config = docx_config

    def save_to_files(self, output_dir, titles_filename="titles_config.json", main_filename="docx_config.json"):
        """
        Write both configs to disk as JSON files in the specified directory.

        :param output_dir: Directory to write the files into.
        :param titles_filename: Optional override for titles config filename.
        :param main_filename: Optional override for main config filename.
        :return: (titles_path, main_path)
        """
        os.makedirs(output_dir, exist_ok=True)

        titles_path = os.path.join(output_dir, titles_filename)
        main_path = os.path.join(output_dir, main_filename)

        with open(titles_path, "w", encoding="utf-8") as f:
            json.dump(self.titles_config, f, indent=2)

        with open(main_path, "w", encoding="utf-8") as f:
            json.dump(self.docx_config, f, indent=2)

        return titles_path, main_path
