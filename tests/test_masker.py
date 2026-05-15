"""mask() / unmask() tests. NER-free cases use use_ner=False so they run
without the [ner] extra."""

import pytest

from kakushi import EntityType, Mapping, mask, unmask


# -- regex-only cases (NER off for speed and determinism) -----------------


def test_phone_masked_with_default_placeholder():
    masked, mapping = mask("電話は090-1234-5678です", use_ner=False)
    assert "<PHONE_1>" in masked
    assert mapping.placeholder_to_original["<PHONE_1>"] == "090-1234-5678"


def test_unmask_round_trip():
    text = "電話は090-1234-5678、メールは tanaka@example.jp です"
    masked, mapping = mask(text, use_ner=False)
    assert unmask(masked, mapping) == text


def test_same_value_same_placeholder():
    text = "tanaka@example.jp に送って、tanaka@example.jp に確認"
    masked, mapping = mask(text, use_ner=False)
    assert masked.count("<EMAIL_1>") == 2
    assert "<EMAIL_2>" not in masked
    assert len(mapping) == 1


def test_distinct_values_get_distinct_placeholders():
    text = "tanaka@example.jp と sato@example.jp を確認"
    masked, mapping = mask(text, use_ner=False)
    assert "<EMAIL_1>" in masked
    assert "<EMAIL_2>" in masked
    assert len(mapping) == 2


def test_empty_text():
    masked, mapping = mask("", use_ner=False)
    assert masked == ""
    assert len(mapping) == 0


def test_no_pii_passthrough():
    text = "今日は良い天気ですね、桜が綺麗です"
    masked, mapping = mask(text, use_ner=False)
    assert masked == text
    assert len(mapping) == 0


def test_zenkaku_normalized_in_output():
    # Input has zenkaku digits; masked output is on the normalized form.
    masked, mapping = mask("電話は０９０－１２３４－５６７８です", use_ner=False)
    assert "<PHONE_1>" in masked
    # The mapping carries the *normalized* original so unmask is self-consistent.
    assert mapping.placeholder_to_original["<PHONE_1>"] == "090-1234-5678"


def test_unmask_handles_llm_reply():
    """The LLM reply quotes the placeholder; unmask should restore it."""
    text = "tanaka@example.jp に¥10,000の請求書を送ってください"
    masked, mapping = mask(text, use_ner=False)
    reply = f"承知しました。{masked} の処理を進めます。"
    restored = unmask(reply, mapping)
    assert "tanaka@example.jp" in restored
    assert "¥10,000" in restored


def test_multiple_entity_types():
    text = "03-1234-5678 から tanaka@example.jp へ¥50,000の請求"
    masked, mapping = mask(text, use_ner=False)
    assert "<PHONE_1>" in masked
    assert "<EMAIL_1>" in masked
    assert "<AMOUNT_1>" in masked
    assert len(mapping) == 3


# -- company dictionary cases ---------------------------------------------


def test_company_dict_custom_placeholder():
    text = "株式会社山田商事と契約します"
    masked, mapping = mask(text, dictionary={"株式会社山田商事": "取引先A"}, use_ner=False)
    assert "取引先A" in masked
    assert mapping.placeholder_to_original["取引先A"] == "株式会社山田商事"


def test_company_dict_default_placeholder_when_value_is_none():
    text = "株式会社山田商事と契約"
    masked, mapping = mask(text, dictionary={"株式会社山田商事": None}, use_ner=False)
    assert "<COMPANY_DICT_1>" in masked


def test_company_dict_longest_match_wins():
    text = "株式会社山田商事の山田さん"
    dictionary = {"株式会社山田商事": "取引先A", "山田": "顧客X"}
    masked, mapping = mask(text, dictionary=dictionary, use_ner=False)
    # 株式会社山田商事 wins because it is longer
    assert "取引先A" in masked
    # The bare 山田 (the person) is still caught by the dict on its second occurrence
    assert "顧客X" in masked


def test_company_dict_unmask_round_trip():
    text = "株式会社山田商事の田中太郎様、¥10,000の件"
    dictionary = {"株式会社山田商事": "取引先A"}
    masked, mapping = mask(text, dictionary=dictionary, use_ner=False)
    restored = unmask(masked, mapping)
    assert restored == text


def test_mapping_never_default_serializable_to_disk():
    """Sanity: Mapping is a plain dataclass — callers must avoid pickling.

    This test documents intent rather than enforcing it (there's no clean way
    to *prevent* serialization). If we ever add a `__getstate__` that refuses
    to pickle, that goes here.
    """
    _, mapping = mask("電話は090-1234-5678です", use_ner=False)
    assert isinstance(mapping, Mapping)
    assert len(mapping) >= 1


# -- placeholder collision guards -----------------------------------------


def test_placeholder_10_unmasked_before_1():
    """If both <PHONE_1> and <PHONE_10> exist, unmask must restore <PHONE_10>
    correctly even though "PHONE_1" is a prefix of "PHONE_10"."""
    # Build a mapping by hand to exercise the sort-by-length path.
    mapping = Mapping()
    mapping.placeholder_to_original = {
        "<PHONE_1>": "A",
        "<PHONE_10>": "B",
    }
    mapping.original_to_placeholder = {v: k for k, v in mapping.placeholder_to_original.items()}
    restored = unmask("<PHONE_10> と <PHONE_1>", mapping)
    assert restored == "B と A"
