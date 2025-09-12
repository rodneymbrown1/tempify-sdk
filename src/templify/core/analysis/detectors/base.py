from dataclasses import dataclass
from enum import Enum

class SignalStrength(Enum):
    EXACT = "exact"
    REGEXABLE = "regex"
    HEURISTIC = "heuristic"
    SEMANTIC = "semantic"

class Granularity(Enum):
    LINE = "line"
    PARAGRAPH = "paragraph"
    BLOCK = "block"

@dataclass
class DetectionResult:
    form: str                  # e.g. "H-SHORT"
    signal: SignalStrength      # which axis 2 bucket
    domain: str | None          # optional domain hint
    granularity: Granularity
    confidence: float
    clues: list[str]

class BaseDetector:
    def detect(self, line: str, context=None) -> list[DetectionResult]:
        raise NotImplementedError
