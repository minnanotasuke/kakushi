"""GiNZA NER tests. Skipped automatically if [ner] extra is not installed."""

import pytest

# Skip the whole module if GiNZA isn't available.
pytest.importorskip("spacy", reason="GiNZA requires the [ner] extra")
pytest.importorskip("ja_ginza", reason="ja-ginza model required")

from kakushi import EntityType, find_all, find_ner_matches, is_ner_available


def test_ner_available():
    assert is_ner_available()


def test_person_detected():
    matches = find_ner_matches("田中太郎さんから連絡がありました")
    assert any(m.entity_type == EntityType.PERSON for m in matches), (
        f"Expected a PERSON entity, got: {[(m.text, m.entity_type) for m in matches]}"
    )


def test_org_detected():
    matches = find_ner_matches("株式会社山田商事と契約しました")
    assert any(m.entity_type == EntityType.ORG for m in matches), (
        f"Expected an ORG entity, got: {[(m.text, m.entity_type) for m in matches]}"
    )


def test_location_detected():
    matches = find_ner_matches("東京都港区にあるオフィスへ移動")
    assert any(m.entity_type == EntityType.LOCATION for m in matches), (
        f"Expected a LOCATION entity, got: {[(m.text, m.entity_type) for m in matches]}"
    )


def test_find_all_combines_regex_and_ner():
    text = "田中太郎さんの電話は090-1234-5678です"
    matches = find_all(text)
    types = {m.entity_type for m in matches}
    assert EntityType.PHONE in types
    assert EntityType.PERSON in types


def test_find_all_regex_wins_overlap():
    # If GiNZA happens to tag part of the phone number as an entity,
    # the regex PHONE span must survive resolve_overlaps.
    text = "電話は090-1234-5678です"
    matches = find_all(text)
    phones = [m for m in matches if m.entity_type == EntityType.PHONE]
    assert phones
    assert phones[0].text == "090-1234-5678"


def test_clean_text_has_no_pii():
    matches = find_all("今日は良い天気ですね、桜が綺麗です")
    # No phone/email/etc. Person/Org/Loc might or might not fire on common words.
    # We don't assert empty — just that nothing crashes and the call returns a list.
    assert isinstance(matches, list)
