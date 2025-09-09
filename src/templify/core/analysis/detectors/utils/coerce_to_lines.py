from typing import Any

def coerce_to_lines(source: Any) -> list[str]:
    if isinstance(source, (list, tuple)):
        return list(source)
    text = getattr(source, "text", None)
    if text is not None:
        return [str(text)]
    lines = getattr(source, "lines", None)
    return list(lines) if lines is not None else []


