"""Mask → call LLM → unmask.

Public surface of the library. Combines:
    * customer-owned company dictionary (highest priority)
    * regex layer (phone, postal, email, etc.)
    * GiNZA NER layer (person, org, location)

`mask()` returns a `Mapping` that lives in memory only. Do not persist it.
Pass the same `Mapping` to `unmask()` to restore originals in the LLM reply.
"""

from dataclasses import dataclass, field
from typing import List, Mapping as MappingT, Optional, Tuple

from .ner import NERUnavailableError, find_ner_matches
from .normalizer import normalize
from .patterns import find_regex_matches
from .resolver import resolve_overlaps
from .types import EntityType, Match


CompanyDict = MappingT[str, Optional[str]]
"""Customer dictionary: original literal -> optional placeholder.

If the placeholder is None, kakushi assigns ``<COMPANY_DICT_N>`` automatically.
If the placeholder is a string (e.g. ``"取引先A"``), kakushi uses it verbatim.
"""


@dataclass
class Mapping:
    """Mask placeholder ↔ original text. In-memory only.

    This object holds the sensitive values that were stripped from the text
    before it was sent to the LLM. Never serialize, log, or persist it. It
    is intended to live only for the duration of a single mask → call →
    unmask cycle.
    """

    placeholder_to_original: dict = field(default_factory=dict)
    original_to_placeholder: dict = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.placeholder_to_original)

    def __contains__(self, placeholder: str) -> bool:
        return placeholder in self.placeholder_to_original


def _find_company_dict_matches(
    text: str, dictionary: CompanyDict
) -> List[Match]:
    """Locate every literal occurrence of a company dictionary key.

    Keys are tried longest-first so ``株式会社山田商事`` wins over ``山田``
    when both appear in the same dictionary.
    """
    matches: List[Match] = []
    for original in sorted(dictionary.keys(), key=len, reverse=True):
        if not original:
            continue
        start = 0
        while True:
            idx = text.find(original, start)
            if idx < 0:
                break
            matches.append(
                Match(
                    start=idx,
                    end=idx + len(original),
                    text=original,
                    entity_type=EntityType.COMPANY_DICT,
                    source="dict",
                )
            )
            start = idx + len(original)
    return matches


def mask(
    text: str,
    *,
    dictionary: Optional[CompanyDict] = None,
    use_ner: bool = True,
) -> Tuple[str, Mapping]:
    """Mask PII in *text*. Returns ``(masked_text, mapping)``.

    The returned ``masked_text`` is on the NFKC-normalized form of the input.
    The same literal value always receives the same placeholder within one
    call (so a name appearing three times produces ``<PERSON_1>`` × 3, not
    three different ids).

    Pass the returned ``mapping`` to :func:`unmask` to restore originals.
    """
    normalized = normalize(text)

    # Collect matches from every layer.
    collected: List[Match] = []
    if dictionary:
        collected.extend(_find_company_dict_matches(normalized, dictionary))
    collected.extend(find_regex_matches(normalized, normalize_first=False))
    if use_ner:
        try:
            collected.extend(find_ner_matches(normalized, normalize_first=False))
        except NERUnavailableError:
            pass

    final = resolve_overlaps(collected)

    mapping = Mapping()
    counters: dict = {}
    parts: List[str] = []
    cursor = 0

    for m in final:
        parts.append(normalized[cursor : m.start])
        original = m.text

        if original in mapping.original_to_placeholder:
            placeholder = mapping.original_to_placeholder[original]
        else:
            # Company dictionary may specify a custom placeholder.
            custom = None
            if dictionary and m.source == "dict":
                custom = dictionary.get(original)
            if custom:
                placeholder = custom
            else:
                counters[m.entity_type] = counters.get(m.entity_type, 0) + 1
                placeholder = f"<{m.entity_type.value}_{counters[m.entity_type]}>"
            mapping.original_to_placeholder[original] = placeholder
            mapping.placeholder_to_original[placeholder] = original

        parts.append(placeholder)
        cursor = m.end

    parts.append(normalized[cursor:])
    return "".join(parts), mapping


def unmask(text: str, mapping: Mapping) -> str:
    """Restore originals in *text* using a previously produced ``mapping``.

    Replaces every placeholder in *text* with its original value. Longer
    placeholders are restored first to avoid prefix conflicts (``<PHONE_10>``
    is processed before ``<PHONE_1>``).
    """
    result = text
    for placeholder in sorted(
        mapping.placeholder_to_original.keys(), key=len, reverse=True
    ):
        result = result.replace(placeholder, mapping.placeholder_to_original[placeholder])
    return result
