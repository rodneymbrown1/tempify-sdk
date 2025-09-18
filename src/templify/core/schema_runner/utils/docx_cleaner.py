from docx import Document

def strip_body_content(doc_path: str) -> Document:
    """
    Open a .docx but strip all paragraphs, tables, and runs,
    leaving a 'blank' body while preserving styles, numbering,
    headers/footers, and theme.
    """
    doc = Document(doc_path)

    body = doc.element.body
    for child in list(body):
        body.remove(child)

    return doc
