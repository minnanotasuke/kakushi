__version__ = "0.1.0"

from typing import List

from .masker import CompanyDict, Mapping, mask, unmask
from .ner import NERUnavailableError, find_ner_matches, is_ner_available
from .normalizer import normalize
from .patterns import PATTERNS, find_regex_matches
from .resolver import resolve_overlaps
from .types import EntityType, Match

__all__ = [
    "__version__",
    "CompanyDict",
    "EntityType",
    "Mapping",
    "Match",
    "NERUnavailableError",
    "PATTERNS",
    "find_all",
    "find_ner_matches",
    "find_regex_matches",
    "is_ner_available",
    "mask",
    "normalize",
    "resolve_overlaps",
    "unmask",
]


def find_all(text: str, *, use_ner: bool = True) -> List[Match]:
    """Find every PII span in *text*, merging regex and NER layers.

    Always runs the regex layer. Runs NER too if ``use_ner`` is True and the
    ``[ner]`` extra is installed; silently falls back to regex-only otherwise.
    Overlapping spans are resolved via :func:`resolve_overlaps`.

    The returned spans are offsets into the *NFKC-normalized* form of *text*.
    """
    normalized = normalize(text)
    matches = find_regex_matches(normalized, normalize_first=False)
    if use_ner:
        try:
            matches.extend(find_ner_matches(normalized, normalize_first=False))
        except NERUnavailableError:
            pass
    return resolve_overlaps(matches)
