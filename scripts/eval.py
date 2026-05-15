"""Measure kakushi recall on the synthetic corpus.

Usage:
    .venv/bin/python scripts/eval.py [--n 100] [--regex-only]
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

# Run from a source checkout: make src/ importable even if editable install
# didn't wire the .pth file (works regardless of pip install state).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from kakushi import mask  # noqa: E402
from kakushi.synth import generate  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100, help="Number of synthetic cases")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--regex-only",
        action="store_true",
        help="Disable GiNZA NER (regex layer only)",
    )
    args = parser.parse_args()

    cases = generate(n=args.n, seed=args.seed)
    use_ner = not args.regex_only

    total_by_type = defaultdict(int)
    hit_by_type = defaultdict(int)
    miss_examples = defaultdict(list)

    for case in cases:
        _, mapping = mask(case.text, use_ner=use_ner)
        captured_originals = set(mapping.placeholder_to_original.values())
        for ent in case.entities:
            total_by_type[ent.entity_type] += 1
            if ent.text in captured_originals:
                hit_by_type[ent.entity_type] += 1
            else:
                miss_examples[ent.entity_type].append(ent.text)

    print(f"Corpus size: {len(cases)} cases")
    print(f"NER: {'on' if use_ner else 'OFF (regex-only)'}")
    print()
    print(f"{'TYPE':<12} {'TOTAL':>6} {'HIT':>6} {'RECALL':>8}")
    print("-" * 36)
    total_total = total_hit = 0
    for et in sorted(total_by_type.keys()):
        t = total_by_type[et]
        h = hit_by_type[et]
        recall = h / t if t else 0.0
        total_total += t
        total_hit += h
        print(f"{et:<12} {t:>6} {h:>6} {recall:>7.1%}")
    print("-" * 36)
    overall = total_hit / total_total if total_total else 0.0
    print(f"{'OVERALL':<12} {total_total:>6} {total_hit:>6} {overall:>7.1%}")

    misses = sum(len(v) for v in miss_examples.values())
    if misses:
        print(f"\nMisses ({misses} total):")
        for et, vals in miss_examples.items():
            print(f"  {et}: {len(vals)}")
            for v in vals[:3]:
                print(f"    - {v}")
            if len(vals) > 3:
                print(f"    ... and {len(vals) - 3} more")


if __name__ == "__main__":
    main()
