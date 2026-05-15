from kakushi import EntityType, Match, resolve_overlaps


def _m(start, end, text, entity_type, source):
    return Match(start=start, end=end, text=text, entity_type=entity_type, source=source)


def test_empty():
    assert resolve_overlaps([]) == []


def test_no_overlap_passthrough():
    a = _m(0, 5, "abcde", EntityType.PERSON, "ner")
    b = _m(10, 15, "fghij", EntityType.ORG, "ner")
    assert resolve_overlaps([a, b]) == [a, b]


def test_dict_beats_regex():
    # Dictionary entry "山田商事" should win over a regex hit on the same range.
    d = _m(0, 4, "山田商事", EntityType.COMPANY_DICT, "dict")
    r = _m(0, 4, "山田商事", EntityType.ORG, "regex")
    assert resolve_overlaps([d, r]) == [d]


def test_regex_beats_ner():
    # GiNZA might tag a phone number as a thing; regex PHONE must win.
    r = _m(5, 17, "090-1234-5678", EntityType.PHONE, "regex")
    n = _m(5, 17, "090-1234-5678", EntityType.ORG, "ner")
    assert resolve_overlaps([n, r]) == [r]


def test_longer_wins_at_same_priority():
    short = _m(0, 3, "abc", EntityType.PERSON, "ner")
    long_ = _m(0, 6, "abcdef", EntityType.PERSON, "ner")
    assert resolve_overlaps([short, long_]) == [long_]


def test_partial_overlap_keeps_higher_priority():
    # Regex PHONE 5..17 should suppress a NER span 10..20 that overlaps.
    phone = _m(5, 17, "090-1234-5678", EntityType.PHONE, "regex")
    ner_span = _m(10, 20, "ner-thing", EntityType.ORG, "ner")
    result = resolve_overlaps([phone, ner_span])
    assert result == [phone]


def test_result_sorted_by_start():
    a = _m(20, 25, "zzz", EntityType.PERSON, "ner")
    b = _m(0, 5, "aaa", EntityType.PERSON, "ner")
    c = _m(10, 15, "mmm", EntityType.PERSON, "ner")
    assert resolve_overlaps([a, b, c]) == [b, c, a]
