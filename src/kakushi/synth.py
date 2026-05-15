"""Synthetic Japanese business-text generator.

Used by :mod:`kakushi.scripts.eval` to measure regex-layer + NER-layer recall
on a known-truth corpus. Useful as a fixture for downstream users too.

The generator is fully deterministic given a seed.
"""

import random
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class GoldEntity:
    """A PII span that the masker is expected to detect."""

    text: str
    entity_type: str  # mirrors EntityType.value


@dataclass
class GoldCase:
    """One synthetic business-text sample plus its expected entities."""

    text: str
    entities: List[GoldEntity] = field(default_factory=list)


# ---- entity pools --------------------------------------------------------

_PERSONS = [
    "田中太郎", "佐藤花子", "鈴木一郎", "高橋美咲", "渡辺健",
    "伊藤さやか", "山本大輔", "中村真奈美", "小林翔", "加藤理恵",
    "吉田直樹", "山田優子", "斎藤拓也", "松本葵", "井上博之",
]

_COMPANIES = [
    "株式会社山田商事", "株式会社青山テック", "合同会社みどり",
    "株式会社ABC", "東京物産株式会社", "株式会社さくら通信",
    "株式会社オフィスワン", "株式会社グリーンウィング",
    "株式会社ノースコンサル", "株式会社サンライズ",
]

_EMAILS = [
    "tanaka@example.co.jp", "sato@example.jp", "info@aoyama-tech.co.jp",
    "contact@midori.jp", "support@abc.co.jp", "sales@tokyobussan.co.jp",
    "office@sakura-tsushin.jp", "ceo@officeone.jp",
]

_PHONES = [
    "090-1234-5678", "080-9876-5432", "03-1234-5678",
    "06-9876-1234", "045-123-4567", "0120-123-456",
    "+81-90-1111-2222",
]

_AMOUNTS = [
    "¥10,000", "¥50,000", "¥100,000", "¥1,500,000",
    "10,000円", "50,000円", "1,500,000円", "300,000円",
]

_LOCATIONS = [
    "東京都港区", "大阪府大阪市", "神奈川県横浜市",
    "愛知県名古屋市", "福岡県福岡市", "京都府京都市",
]


# ---- text templates ------------------------------------------------------
#
# Each template lists the placeholders it consumes. The generator fills them
# and emits a GoldCase whose entities reflect what was actually injected.

_TEMPLATES = [
    # business email
    "{person}様、いつもお世話になっております。{company}の件で、{amount}のご請求書を {email} にお送りしました。ご確認のほどよろしくお願いします。",
    "{company}様、お問い合わせありがとうございます。担当の{person}よりご連絡差し上げます。電話番号は{phone}です。",
    # meeting notes
    "本日の議事録: {company}との打ち合わせで{amount}の発注が決定。{person}が窓口担当となり、連絡先は{email}。",
    # invoice
    "請求書送付のお知らせ: {company}様、{amount}の請求書を{email}までお送りしました。お問い合わせは{phone}まで。",
    # customer support
    "お客様の{person}様から「{company}の{amount}の支払いについて」とのお問い合わせがありました。電話番号は{phone}、メールは{email}です。",
    # internal announcement
    "社内のお知らせ: {location}支店の{person}が、{company}との新規契約{amount}を獲得しました。",
    # FAQ draft
    "Q: {company}の請求書はどこに送ればよいですか。A: {email}までお送りください。担当{person}が対応します。",
    # follow-up
    "{person}様、先日は{location}にてお打ち合わせをありがとうございました。{company}との契約{amount}の件、{phone}までお気軽にご連絡ください。",
]


_PLACEHOLDER_TO_ENTITY_TYPE = {
    "person": "PERSON",
    "company": "ORG",
    "email": "EMAIL",
    "phone": "PHONE",
    "amount": "AMOUNT",
    "location": "LOCATION",
}


def _generate_one(rng: random.Random) -> GoldCase:
    template = rng.choice(_TEMPLATES)
    fill = {
        "person": rng.choice(_PERSONS),
        "company": rng.choice(_COMPANIES),
        "email": rng.choice(_EMAILS),
        "phone": rng.choice(_PHONES),
        "amount": rng.choice(_AMOUNTS),
        "location": rng.choice(_LOCATIONS),
    }
    text = template.format(**fill)

    entities: List[GoldEntity] = []
    for key, et in _PLACEHOLDER_TO_ENTITY_TYPE.items():
        token = "{" + key + "}"
        if token in template:
            entities.append(GoldEntity(text=fill[key], entity_type=et))
    return GoldCase(text=text, entities=entities)


def generate(n: int = 100, seed: int = 42) -> List[GoldCase]:
    """Produce *n* synthetic business-text cases with gold entity labels."""
    rng = random.Random(seed)
    return [_generate_one(rng) for _ in range(n)]
