"""Smoke tests for the synthetic corpus generator + regex-layer baseline recall."""

from collections import Counter

from kakushi import mask
from kakushi.synth import generate


def test_generator_emits_n_cases():
    cases = generate(n=10)
    assert len(cases) == 10
    for case in cases:
        assert case.text
        assert case.entities  # every template injects at least one entity


def test_generator_is_deterministic():
    a = generate(n=20, seed=42)
    b = generate(n=20, seed=42)
    assert [c.text for c in a] == [c.text for c in b]


def test_generator_different_seeds_differ():
    a = generate(n=10, seed=1)
    b = generate(n=10, seed=2)
    assert [c.text for c in a] != [c.text for c in b]


def test_regex_layer_high_recall_on_structured_pii():
    """Regex layer alone should hit ~100% on PHONE/EMAIL/AMOUNT — they are structured."""
    cases = generate(n=30, seed=42)
    total = Counter()
    hit = Counter()
    for case in cases:
        _, mapping = mask(case.text, use_ner=False)
        captured = set(mapping.placeholder_to_original.values())
        for ent in case.entities:
            total[ent.entity_type] += 1
            if ent.text in captured:
                hit[ent.entity_type] += 1

    # Structured entities — regex must be near-perfect.
    for et in ("PHONE", "EMAIL", "AMOUNT"):
        if total[et]:
            recall = hit[et] / total[et]
            assert recall >= 0.95, f"{et} recall {recall:.0%} below 95% (regex layer)"
