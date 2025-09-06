# src/templify/template_maker.py

from templify.core.config.docx_to_json import DocxToJsonParser
from templify.core.config.exporter import ConfigExporter


def generate_configs(docx_path, extract_dir=None, expected_titles=None, output_dir=None):
    """
    High-level entrypoint for generating Templify JSON configs from a DOCX file.

    :param docx_path: Path to the Word document XML (document.xml).
    :param extract_dir: Optional path to the extracted DOCX directory (needed for styles, numbering, headers/footers).
    :param expected_titles: Optional rigid list of expected titles (strings or dicts).
    :param output_dir: Optional directory to save JSON configs. If None, configs are only returned in memory.

    :return: If output_dir is None -> (titles_config, main_config)
             If output_dir is provided -> (titles_path, main_path) where files were saved
    """
    parser = DocxToJsonParser(docx_path, extract_dir, expected_titles)
    parser.run()

    if output_dir:
        exporter = ConfigExporter(parser.titles_config, parser.main_config)
        return exporter.save_to_files(output_dir)

    return parser.titles_config, parser.main_config
