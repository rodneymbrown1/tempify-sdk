# templify/core/analysis/domain_scoring.py
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

try:
    # Optional: only used for type hints
    from .features import LineFeatures  # type: ignore
except Exception:  # pragma: no cover - keep import optional
    LineFeatures = object  # type: ignore


__all__ = [
    "DomainPack",
    "DomainScores",
    "load_domain_packs_from_dir",
    "score_line_domain",
    "ema_prior_update",
    "domain_boost",
]

# ---------------------------
# Utilities
# ---------------------------

_WORD_BOUNDARY = r"(?:^|[^A-Za-z0-9_])"
_PUNCT_STRIP_RE = re.compile(r"[^\w\s]")
_WS_RE = re.compile(r"\s+")
# Very light token-ish split just for keyword counting fallback
_TOKEN_SPLIT = re.compile(r"[^\w]+")


def _normalize_heading_key(s: str) -> str:
    # Uppercase, strip punctuation, collapse whitespace
    s = s.strip()
    s = _PUNCT_STRIP_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s)
    return s.upper()


def _normalize_for_scan(s: str) -> str:
    # Uppercase + collapse whitespace; keep punctuation for regex scans
    return _WS_RE.sub(" ", s.strip()).upper()


def _best_fuzzy_ratio(source_norm: str, candidates_norm: Sequence[str]) -> float:
    """
    Cheap fuzzy score using difflib-like ratio without importing extra deps.
    Returns best ratio in [0,1].
    """
    try:
        from difflib import SequenceMatcher
    except Exception:
        return 0.0

    best = 0.0
    for cand in candidates_norm:
        r = SequenceMatcher(None, source_norm, cand).ratio()
        if r > best:
            best = r
            if best >= 0.98:
                break
    return best


def _softmax(scores: Mapping[str, float], temperature: float = 1.0) -> Dict[str, float]:
    if not scores:
        return {}
    if temperature <= 0:
        temperature = 1.0
    vals = list(scores.values())
    m = max(vals)
    exps = {k: math.exp((v - m) / temperature) for k, v in scores.items()}
    z = sum(exps.values()) or 1.0
    return {k: v / z for k, v in exps.items()}


# ---------------------------
# Data structures
# ---------------------------

@dataclass(frozen=True)
class DomainPack:
    name: str
    headings_exact: Tuple[str, ...]        # normalized keys
    headings_fuzzy: Tuple[str, ...]        # normalized keys
    keywords: Tuple[re.Pattern, ...]       # compiled regex per keyword (word-boundary)
    regexes: Tuple[re.Pattern, ...]        # compiled regex patterns
    stopwords: Tuple[re.Pattern, ...]      # compiled regex stopwords

    @staticmethod
    def from_json(name: str, data: Mapping[str, Any]) -> "DomainPack":
        # Normalize headings to uppercase/punct-less keys
        hx = tuple(_normalize_heading_key(h) for h in data.get("headings_exact", []))
        hf = tuple(_normalize_heading_key(h) for h in data.get("headings_fuzzy", []))

        def _kw_compile(items: Iterable[str]) -> Tuple[re.Pattern, ...]:
            out: List[re.Pattern] = []
            for raw in items:
                s = raw.strip()
                if not s:
                    continue
                # Word-boundary-ish match; allow spaces inside keywords
                # (?i) case-insensitive; we match against original text variant too.
                pattern = re.compile(rf"(?i){_WORD_BOUNDARY}{re.escape(s)}{_WORD_BOUNDARY}")
                out.append(pattern)
            return tuple(out)

        regexes = tuple(re.compile(r, re.IGNORECASE) for r in data.get("regexes", []))
        stopwords = _kw_compile(data.get("stopwords", []))
        keywords = _kw_compile(data.get("keywords", []))

        return DomainPack(
            name=name,
            headings_exact=hx,
            headings_fuzzy=hf,
            keywords=keywords,
            regexes=regexes,
            stopwords=stopwords,
        )


@dataclass(frozen=True)
class DomainScores:
    scores: Dict[str, float]              # normalized (softmax) per-domain
    raw: Dict[str, float]                 # pre-softmax raw scores (for debugging)
    top: List[Tuple[str, float]]          # sorted by normalized score desc

    def get(self, domain: str, default: float = 0.0) -> float:
        return self.scores.get(domain, default)


# ---------------------------
# Pack loading
# ---------------------------

def load_domain_packs_from_dir(path: str | Path) -> Dict[str, DomainPack]:
    """
    Load *.json domain packs from a directory. Each file should be a JSON object
    with keys: name (optional), headings_exact, headings_fuzzy, keywords, regexes, stopwords.
    The filename (without .json) is used as fallback domain name.
    """
    path = Path(path)
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Domain packs directory not found: {path}")

    packs: Dict[str, DomainPack] = {}
    for fp in path.glob("*.json"):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in {fp}: {e.msg}", e.doc, e.pos)
        name = (data.get("name") or fp.stem).strip().upper()
        packs[name] = DomainPack.from_json(name, data)
    if not packs:
        raise ValueError(f"No domain packs found in {path}")
    return packs


# ---------------------------
# Scoring
# ---------------------------

_DEFAULT_WEIGHTS = {
    "exact": 1.00,   # literal heading match (after normalization)
    "fuzzy": 0.60,   # scaled by best fuzzy ratio
    "regex": 0.50,   # if any domain regex matches
    "kw": 0.10,      # per keyword hit (capped by kw_cap)
    "kw_cap": 0.40,  # max keyword contribution
    "stop": 0.30,    # penalty if any stopword hits
}

@lru_cache(maxsize=64)
def _pack_index(pack: DomainPack) -> Dict[str, Any]:
    """
    Build a small index per pack to speed lookups:
    - set of exact headings
    - list of fuzzy heading strings (normalized)
    """
    return {
        "hx": set(pack.headings_exact),
        "hf": list(pack.headings_fuzzy),
    }


def _score_against_pack(
    text: str,
    lf: Optional[LineFeatures],
    pack: DomainPack,
    *,
    weights: Mapping[str, float],
) -> float:
    """
    Compute a raw (pre-softmax) score for one domain pack.
    """
    if not text:
        return 0.0

    scan_upper = _normalize_for_scan(text)
    heading_key = _normalize_heading_key(text)  # for exact/fuzzy

    idx = _pack_index(pack)

    score = 0.0

    # 1) Exact heading hit (dominant, deterministic)
    if heading_key in idx["hx"]:
        score += weights["exact"]
        # Early return still allows other small contributions if you want;
        # but exact is usually decisive. We'll continue to add tiny signal.

    # 2) Fuzzy heading (scaled by ratio)
    if idx["hf"]:
        best = _best_fuzzy_ratio(heading_key, idx["hf"])
        # Only count meaningful similarity
        if best >= 0.82:
            score += weights["fuzzy"] * best

    # 3) Domain regexes (e.g., WHEREAS, Table \d+, etc.)
    regex_hit = any(r.search(text) for r in pack.regexes)
    if regex_hit:
        score += weights["regex"]

    # 4) Keyword hits (cap contribution)
    kw_hits = 0
    for kw in pack.keywords:
        if kw.search(text):
            kw_hits += 1
            # Small optimization: stop once we reach cap contribution
            if (kw_hits * weights["kw"]) >= weights["kw_cap"]:
                break
    kw_contrib = min(weights["kw_cap"], kw_hits * weights["kw"])
    score += kw_contrib

    # 5) Stopwords penalty (any hit → subtract)
    if any(sw.search(text) for sw in pack.stopwords):
        score -= weights["stop"]

    # 6) Optional: tiny bonus if lf hints align (keep very small)
    # Example: a lot of ALLCAPS might indicate section-like (domain-dependent).
    # We keep it generic and minimal here.
    if lf is not None:
        if lf.has_allcaps_word and lf.titlecase_rate < 0.5:
            score += 0.02

    return max(score, 0.0)


def score_line_domain(
    text: str,
    packs: Mapping[str, DomainPack],
    *,
    lf: Optional[LineFeatures] = None,
    weights: Mapping[str, float] = _DEFAULT_WEIGHTS,
    temperature: float = 1.0,
) -> DomainScores:
    """
    Score a line of text against all domain packs.
    Returns normalized per-domain probabilities and raw scores.
    - `weights` tunes contributions of exact/fuzzy/regex/keywords/stopwords.
    - `temperature` controls softmax sharpness (lower = peakier).
    """
    if not packs:
        return DomainScores(scores={}, raw={}, top=[])

    raw: Dict[str, float] = {}
    for name, pack in packs.items():
        raw[name] = _score_against_pack(text, lf, pack, weights=weights)

    norm = _softmax(raw, temperature=temperature)
    top = sorted(norm.items(), key=lambda kv: kv[1], reverse=True)
    return DomainScores(scores=norm, raw=raw, top=top)


# ---------------------------
# Document-level prior & matcher nudge
# ---------------------------

def ema_prior_update(
    prev_prior: Mapping[str, float] | None,
    current_line_scores: Mapping[str, float],
    *,
    alpha: float = 0.2,
) -> Dict[str, float]:
    """
    Exponential moving average over per-line normalized domain scores.
    Keeps distribution normalized.
    """
    keys = set(current_line_scores.keys()) | set((prev_prior or {}).keys())
    out: Dict[str, float] = {}
    for k in keys:
        prev = (prev_prior or {}).get(k, 0.0)
        now = current_line_scores.get(k, 0.0)
        out[k] = (1 - alpha) * prev + alpha * now
    # re-normalize
    s = sum(out.values()) or 1.0
    return {k: v / s for k, v in out.items()}


def domain_boost(
    line_scores: DomainScores,
    prior: Optional[Mapping[str, float]],
    pattern_domain: Optional[str],
    *,
    generic_name: str = "GENERIC",
) -> float:
    """
    Convert domain evidence into a small matcher nudge in [0,1].
    Common usage inside matcher: score += w_domain * domain_boost(...)
    Strategy:
     - Start from line-level probability for the pattern's domain.
     - Blend with doc-level prior if available (50/50).
     - If pattern has no domain or is GENERIC, return 0.5 (neutral).
    """
    if not pattern_domain:
        return 0.5
    pd = pattern_domain.upper()
    if pd == generic_name.upper():
        return 0.5

    p_line = line_scores.get(pd, 0.0)
    if prior is None or not prior:
        return p_line

    p_doc = prior.get(pd, 0.0)
    # Simple blend; you can make this a setting later
    return 0.5 * p_line + 0.5 * p_doc
