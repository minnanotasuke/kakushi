from kakushi import normalize


def test_zenkaku_digits_to_hankaku():
    assert normalize("０９０－１２３４－５６７８") == "090-1234-5678"


def test_chouon_hyphen_folded():
    # Long-vowel mark ー is commonly used as a hyphen by Japanese writers.
    assert normalize("123ー4567") == "123-4567"


def test_fullwidth_minus_folded():
    assert normalize("123−4567") == "123-4567"


def test_em_and_en_dash_folded():
    assert normalize("123–4567") == "123-4567"
    assert normalize("123—4567") == "123-4567"


def test_ascii_passthrough():
    assert normalize("hello world 123") == "hello world 123"


def test_kanji_passthrough():
    assert normalize("田中太郎") == "田中太郎"


def test_zenkaku_yen_to_halfwidth():
    # NFKC folds ￥ (fullwidth) → ¥ (halfwidth).
    assert normalize("￥10,000") == "¥10,000"


def test_chouon_in_japanese_word_preserved():
    # Katakana chouon between Japanese chars must NOT become a hyphen.
    assert normalize("メールアドレス") == "メールアドレス"
    assert normalize("コーヒー") == "コーヒー"
    assert normalize("データセンター") == "データセンター"


def test_hyphen_only_folded_between_alnum():
    # Hyphen-like glyph at start/end or beside Japanese chars stays put.
    assert normalize("ーメール") == "ーメール"
    assert normalize("メールー") == "メールー"
