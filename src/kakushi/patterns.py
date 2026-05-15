"""Regex patterns for Japanese PII.

All patterns are written against NFKC-normalized text. Run normalize() first.
"""

import re
from typing import List, Pattern, Tuple

from .normalizer import normalize
from .types import EntityType, Match


# Characters that can appear inside a Japanese company name's "body":
# Latin letters, digits, katakana, kanji, the chouon ー, and a handful of
# punctuation marks (・ & . -). Deliberately excludes hiragana, brackets,
# and whitespace so that "株式会社山田商事の件で" stops cleanly at the
# hiragana の.
_ORG_BODY = r"[A-Za-z0-9゠-ヿ一-鿿ー・&\.\-]"

# Legal-entity tokens that mark the start or end of a company name.
# NFKC normalizes ㈱ → "(株)", so we match the parenthesized form too.
_ORG_PREFIX = (
    r"(?:株式会社|合同会社|有限会社|一般社団法人|公益社団法人|"
    r"公益財団法人|学校法人|医療法人|宗教法人|"
    r"\(株\)|\(有\))"
)
_ORG_SUFFIX = r"(?:株式会社|合同会社|有限会社|\(株\)|\(有\))"

# Where a company name legitimately *ends*. Hiragana (の/が/は/を/に/と/で…),
# Japanese punctuation, whitespace, and honorific suffixes such as 様/殿/御中
# all signal "stop here, don't pull this into the name."
_ORG_BOUNDARY = r"(?=[぀-ゟ、。「」『』（）()\s]|様|殿|御中|$)"


PATTERNS: List[Tuple[EntityType, Pattern[str]]] = [
    # Phone: landline (固定電話) + mobile (携帯) + フリーダイヤル + +81 international.
    (
        EntityType.PHONE,
        re.compile(r"(?:\+81-?|0)\d{1,4}-?\d{1,4}-?\d{3,4}"),
    ),
    # Japanese postal code: optional 〒, then 3-4 digits.
    (
        EntityType.POSTAL,
        re.compile(r"〒?\s?\d{3}-\d{4}"),
    ),
    # My Number (マイナンバー): exactly 12 digits, often 4-4-4 grouped.
    (
        EntityType.MY_NUMBER,
        re.compile(r"(?<!\d)\d{4}[-\s]?\d{4}[-\s]?\d{4}(?!\d)"),
    ),
    # Email.
    (
        EntityType.EMAIL,
        re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"),
    ),
    # Yen amount: ¥10,000 or 10,000円.
    (
        EntityType.AMOUNT,
        re.compile(r"¥\s?\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d{1,3}(?:,\d{3})*\s?円"),
    ),
    # IPv4 address.
    (
        EntityType.IP,
        re.compile(
            r"(?<!\d)(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}"
            r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?!\d)"
        ),
    ),
    # Driver's license number: 12 digits, anchored to "免許番号" keyword
    # to avoid colliding with my-number.
    (
        EntityType.LICENSE,
        re.compile(r"免許(?:証)?番号[:：\s]*\d{4}[-\s]?\d{4}[-\s]?\d{4}"),
    ),
    # Credit card: 16 digits in 4-4-4-4 grouping.
    (
        EntityType.CARD,
        re.compile(r"(?<!\d)\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}(?!\d)"),
    ),
    # URL.
    (
        EntityType.URL,
        re.compile(r"https?://[^\s　、。「」『』（）]+"),
    ),
    # Contract / order / invoice number: keyword + alphanumeric code (4+ chars).
    (
        EntityType.CONTRACT,
        re.compile(r"(?:契約|注文|発注|請求|見積)番号[:：\s]*[A-Z0-9][A-Z0-9\-]{3,}"),
    ),
    # Company name — prefix form: "株式会社XXX", "(株)XXX", "合同会社XXX", etc.
    # Body chars exclude hiragana, so a particle like の/が/は naturally
    # ends the match. Lazy + lookahead also stops at the 様/殿 honorific
    # so "株式会社ノースコンサル様" yields "株式会社ノースコンサル".
    (
        EntityType.ORG,
        re.compile(rf"{_ORG_PREFIX}{_ORG_BODY}+?{_ORG_BOUNDARY}"),
    ),
    # Company name — suffix form: "東京物産株式会社", "オフィスワン株式会社", …
    (
        EntityType.ORG,
        re.compile(rf"{_ORG_BODY}+{_ORG_SUFFIX}"),
    ),
]


def find_regex_matches(text: str, *, normalize_first: bool = True) -> List[Match]:
    """Find all regex PII matches.

    When normalize_first is True (the default), input is NFKC-normalized before
    matching so zenkaku digits and hyphen variants are caught. The returned
    spans are offsets into the *normalized* text. Downstream masking is expected
    to operate on normalized text as well.
    """
    target = normalize(text) if normalize_first else text
    matches: List[Match] = []
    for entity_type, pattern in PATTERNS:
        for m in pattern.finditer(target):
            matches.append(
                Match(
                    start=m.start(),
                    end=m.end(),
                    text=m.group(),
                    entity_type=entity_type,
                    source="regex",
                )
            )
    matches.sort(key=lambda x: (x.start, -(x.end - x.start)))
    return matches
