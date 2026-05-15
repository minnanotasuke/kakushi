from kakushi import EntityType, find_regex_matches


def _types(matches):
    return {m.entity_type for m in matches}


def _texts(matches, entity_type):
    return [m.text for m in matches if m.entity_type == entity_type]


def test_phone_mobile():
    matches = find_regex_matches("連絡先は090-1234-5678です")
    assert "090-1234-5678" in _texts(matches, EntityType.PHONE)


def test_phone_landline_tokyo():
    matches = find_regex_matches("TEL: 03-1234-5678")
    assert "03-1234-5678" in _texts(matches, EntityType.PHONE)


def test_phone_zenkaku_normalized():
    matches = find_regex_matches("０９０－１２３４－５６７８")
    assert "090-1234-5678" in _texts(matches, EntityType.PHONE)


def test_phone_international():
    matches = find_regex_matches("国際電話は+81-90-1234-5678まで")
    assert any("+81" in t for t in _texts(matches, EntityType.PHONE))


def test_postal_with_mark():
    matches = find_regex_matches("〒100-0001 東京都")
    assert "〒100-0001" in _texts(matches, EntityType.POSTAL) or "100-0001" in _texts(
        matches, EntityType.POSTAL
    )


def test_postal_bare():
    matches = find_regex_matches("住所 100-0001 千代田区")
    assert any("100-0001" in t for t in _texts(matches, EntityType.POSTAL))


def test_email():
    matches = find_regex_matches("お問い合わせは tanaka@example.co.jp まで")
    assert "tanaka@example.co.jp" in _texts(matches, EntityType.EMAIL)


def test_amount_yen_symbol():
    matches = find_regex_matches("料金は¥10,000です")
    assert any("10,000" in t for t in _texts(matches, EntityType.AMOUNT))


def test_amount_yen_suffix():
    matches = find_regex_matches("10,000円のお支払い")
    assert any("10,000" in t for t in _texts(matches, EntityType.AMOUNT))


def test_amount_fullwidth_yen():
    matches = find_regex_matches("料金は￥10,000です")
    assert any("10,000" in t for t in _texts(matches, EntityType.AMOUNT))


def test_my_number():
    matches = find_regex_matches("マイナンバー 1234-5678-9012 を登録")
    # Both MY_NUMBER and CARD could plausibly match a 12-digit string;
    # MY_NUMBER must be present.
    assert EntityType.MY_NUMBER in _types(matches)


def test_ip():
    matches = find_regex_matches("サーバーは192.168.10.1にあります")
    assert "192.168.10.1" in _texts(matches, EntityType.IP)


def test_ip_invalid_rejected():
    matches = find_regex_matches("999.999.999.999 は不正")
    assert _texts(matches, EntityType.IP) == []


def test_license_with_keyword():
    matches = find_regex_matches("免許番号 123456789012 を提示")
    assert _texts(matches, EntityType.LICENSE)


def test_card_16_digits():
    matches = find_regex_matches("カード 4111-1111-1111-1111 で支払い")
    assert "4111-1111-1111-1111" in _texts(matches, EntityType.CARD)


def test_url():
    matches = find_regex_matches("詳細は https://example.co.jp/info を確認")
    assert any("example.co.jp" in t for t in _texts(matches, EntityType.URL))


def test_contract_number():
    matches = find_regex_matches("契約番号: ABC-2024-001 で受付")
    assert any("ABC-2024-001" in t for t in _texts(matches, EntityType.CONTRACT))


def test_order_number():
    matches = find_regex_matches("注文番号 ORD20240315 を確認")
    assert any("ORD20240315" in t for t in _texts(matches, EntityType.CONTRACT))


def test_clean_text_no_pii():
    matches = find_regex_matches("今日は良い天気ですね、桜が綺麗です")
    assert matches == []


def test_org_prefix_kanji_body():
    matches = find_regex_matches("株式会社山田商事の件で打ち合わせ")
    assert "株式会社山田商事" in _texts(matches, EntityType.ORG)


def test_org_suffix_kanji_body():
    matches = find_regex_matches("東京物産株式会社が新サービス開始")
    assert "東京物産株式会社" in _texts(matches, EntityType.ORG)


def test_org_prefix_katakana_body():
    matches = find_regex_matches("株式会社ノースコンサルとの契約")
    assert "株式会社ノースコンサル" in _texts(matches, EntityType.ORG)


def test_org_prefix_alphanumeric_body():
    matches = find_regex_matches("株式会社ABCの新サービス")
    assert "株式会社ABC" in _texts(matches, EntityType.ORG)


def test_org_kabu_in_parens_from_zenkaku_marker():
    # NFKC turns ㈱ into "(株)".
    matches = find_regex_matches("㈱山田商事と契約")
    assert any("山田商事" in t for t in _texts(matches, EntityType.ORG))


def test_org_stops_at_hiragana_boundary():
    # The の particle must NOT be eaten into the org name.
    matches = find_regex_matches("株式会社山田商事の山田さん")
    orgs = _texts(matches, EntityType.ORG)
    assert "株式会社山田商事" in orgs
    # The 山田 of 山田さん should not be appended.
    assert not any(o.endswith("の山田") for o in orgs)
    assert not any(o.endswith("山田さん") for o in orgs)


def test_org_stops_at_honorific_sama():
    matches = find_regex_matches("株式会社ノースコンサル様、お問い合わせ")
    orgs = _texts(matches, EntityType.ORG)
    assert "株式会社ノースコンサル" in orgs
    assert not any("様" in t for t in orgs)


def test_org_stops_at_honorific_onchu():
    matches = find_regex_matches("株式会社ABC御中")
    orgs = _texts(matches, EntityType.ORG)
    assert "株式会社ABC" in orgs
    assert not any("御中" in t for t in orgs)


def test_multiple_entities_in_one_text():
    text = "田中様より03-1234-5678にて、tanaka@example.jpへ¥50,000のご請求"
    matches = find_regex_matches(text)
    types = _types(matches)
    assert EntityType.PHONE in types
    assert EntityType.EMAIL in types
    assert EntityType.AMOUNT in types
