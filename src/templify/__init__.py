from .runner import generate_configs_from_docx
from .runner import generate_configs  # core (expects document.xml)
from .core.utils.docx_intake import unzip_docx_to_workspace, IntakeResult

__all__ = [
    "generate_configs_from_docx",
    "generate_configs",
    "unzip_docx_to_workspace",
    "IntakeResult",
]
