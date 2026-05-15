"""Span overlap resolution.

When regex and NER both fire on overlapping spans, we must pick one.

Priority (lower number wins):
    0 = company dictionary  (most precise, customer-owned truth)
    1 = regex               (structured, high precision)
    2 = NER                 (statistical, lower precision)

Within the same priority, longer span wins. Within same length, earlier start wins.
"""

from typing import List

from .types import Match


_SOURCE_PRIORITY = {"dict": 0, "regex": 1, "ner": 2}


def _priority(m: Match) -> int:
    return _SOURCE_PRIORITY.get(m.source, 99)


def _overlaps(a: Match, b: Match) -> bool:
    return not (a.end <= b.start or a.start >= b.end)


def resolve_overlaps(matches: List[Match]) -> List[Match]:
    """Greedy overlap resolver. Highest priority + longest span wins.

    Returns the kept matches sorted by start offset.
    """
    if not matches:
        return []

    ordered = sorted(
        matches,
        key=lambda m: (_priority(m), -(m.end - m.start), m.start),
    )

    accepted: List[Match] = []
    for m in ordered:
        if any(_overlaps(m, a) for a in accepted):
            continue
        accepted.append(m)

    accepted.sort(key=lambda m: m.start)
    return accepted
