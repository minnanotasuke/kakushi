import re
import unicodedata


_HYPHEN_VARIANTS = ["ー", "－", "−", "–", "—", "‐", "‑", "‒"]

# Only fold a hyphen-like character into ASCII '-' when it is sandwiched
# between ASCII letters or digits. This protects in-word ー used as the
# Japanese chouon (long-vowel) mark — e.g. メール, コーヒー, データ.
_HYPHEN_BETWEEN_ALNUM = re.compile(
    "(?<=[A-Za-z0-9])\\s*(" + "|".join(re.escape(c) for c in _HYPHEN_VARIANTS) + ")\\s*(?=[A-Za-z0-9])"
)


def normalize(text: str) -> str:
    """Normalize Japanese text for stable regex matching.

    Two steps:
        1. NFKC — folds zenkaku digits/letters/symbols (０～９, Ａ～Ｚ, ￥…)
           into their hankaku ASCII equivalents.
        2. Context-aware hyphen folding — replaces the many hyphen-like glyphs
           (ー, －, −, –, —, ‐, ‑, ‒) with ASCII '-' **only when they sit
           between two ASCII letters/digits**. This catches things like
           ``090ー1234ー5678`` while leaving Japanese words such as ``メール``
           or ``コーヒー`` untouched.
    """
    text = unicodedata.normalize("NFKC", text)
    return _HYPHEN_BETWEEN_ALNUM.sub("-", text)
