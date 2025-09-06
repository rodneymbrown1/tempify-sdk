import json
from importlib.resources import files
from typing import Any

def load_default() -> dict[str, Any]:
    p = files("templify.data").joinpath("default_config.json")
    return json.loads(p.read_text(encoding="utf-8"))

def load(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def dump(cfg: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
