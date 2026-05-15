"""GiNZA-based Japanese NER layer.

Detects person, organization, and location entities that regex cannot catch.
Optional: requires the [ner] extra (ginza + ja-ginza).
"""

from typing import List, Optional

from .normalizer import normalize
from .types import EntityType, Match


_NLP = None  # lazy-loaded spaCy pipeline

# GiNZA / OntoNotes entity labels we care about.
# Japanese GiNZA emits a richer set; we collapse to our three masking buckets.
_LABEL_MAP = {
    "PERSON": EntityType.PERSON,
    "Person": EntityType.PERSON,
    "ORG": EntityType.ORG,
    "Organization": EntityType.ORG,
    "Company": EntityType.ORG,
    "Government": EntityType.ORG,
    "Political_Organization_Other": EntityType.ORG,
    "LOC": EntityType.LOCATION,
    "Location": EntityType.LOCATION,
    "GPE": EntityType.LOCATION,
    "City": EntityType.LOCATION,
    "Country": EntityType.LOCATION,
    "Province": EntityType.LOCATION,
}


class NERUnavailableError(RuntimeError):
    """Raised when GiNZA cannot be loaded."""


def _load_nlp():
    global _NLP
    if _NLP is not None:
        return _NLP
    try:
        import spacy  # type: ignore
    except ImportError as e:
        raise NERUnavailableError(
            "GiNZA NER requires the [ner] extra. Install with: pip install kakushi[ner]"
        ) from e
    # ja_ginza ships a `compound_splitter` factory that breaks under newer
    # spaCy/confection because `split_mode` is left as None at config time.
    # We don't need it for NER, so exclude it from the pipeline at load.
    try:
        _NLP = spacy.load("ja_ginza", exclude=["compound_splitter"])
    except OSError as e:
        raise NERUnavailableError(
            "ja_ginza model not found. Install with: pip install ja-ginza"
        ) from e
    return _NLP


def is_ner_available() -> bool:
    """Check whether NER can be used without raising."""
    try:
        _load_nlp()
        return True
    except NERUnavailableError:
        return False


def find_ner_matches(
    text: str, *, normalize_first: bool = True
) -> List[Match]:
    """Find PERSON / ORG / LOCATION entities in Japanese text via GiNZA.

    Raises NERUnavailableError if the [ner] extra is not installed.
    Returns spans relative to the (normalized) text.
    """
    target = normalize(text) if normalize_first else text
    nlp = _load_nlp()
    doc = nlp(target)
    matches: List[Match] = []
    for ent in doc.ents:
        et = _LABEL_MAP.get(ent.label_)
        if et is None:
            continue
        matches.append(
            Match(
                start=ent.start_char,
                end=ent.end_char,
                text=ent.text,
                entity_type=et,
                source="ner",
            )
        )
    return matches
