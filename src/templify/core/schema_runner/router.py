from .writers import (
    ParagraphWriter, ListWriter, TableWriter, HeaderFooterWriter, ImageWriter, ThemeWriter
)

class SchemaRouter:
    def __init__(self, document):
        self.doc = document
        self.writers = {
            "P": ParagraphWriter(document),
            "H": ParagraphWriter(document),
            "L": ListWriter(document),
            "T": TableWriter(document),
            "IMG": ImageWriter(document),
        }

    def dispatch(self, descriptor, style):
        t = descriptor["type"]
        if t.startswith("H"):
            return self.writers["H"].write(descriptor, style)
        if t.startswith("P"):
            return self.writers["P"].write(descriptor, style)
        if t.startswith("L"):
            return self.writers["L"].write(descriptor, style)
        if t.startswith("T"):
            return self.writers["T"].write(descriptor, style)
        if t.startswith("IMG"):
            return self.writers["IMG"].write(descriptor, style)
