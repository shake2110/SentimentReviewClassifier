from app.nlp.pipeline import ReviewAnalyzer
from app.nlp.sentiment import LexiconScorer, label_for
from app.nlp.text import normalize, split_review

ASPECTS = [{"id": "lth", "name": "Leather"}, {"id": "lc", "name": "Lace"},
           {"id": "sl", "name": "Sole"}, {"id": "ins", "name": "Insole"},
           {"id": "bq", "name": "Build quality"}]


def lite():
    return ReviewAnalyzer(None, LexiconScorer())


def by_name(result):
    return {m["aspect_name"]: m for m in result["mentions"]}


def test_normalize_plurals():
    assert normalize("laces") == "lace"
    assert normalize("batteries") == "battery"
    assert normalize("glass") == "glass"
    assert normalize("leather's") == "leather"


def test_split_levels_and_spans():
    text = "Leather is great, laces are weak. However the sole is fine"
    sentences = split_review(text)
    assert len(sentences) == 2
    assert [f.text for f in sentences[0][0]] == ["Leather is great", "laces are weak"]
    frag = sentences[1][0][0]
    assert text[frag.start:frag.end] == "the sole is fine"


def test_example_from_the_brief():
    r = lite().analyze("The shoe leather quality is very good but lace quality is not so good", ASPECTS)
    m = by_name(r)
    assert m["Leather"]["label"] == "positive"
    assert m["Lace"]["label"] == "negative"
    assert m["Lace"]["snippet"] == "lace quality is not so good"


def test_compound_word_matches_part():
    m = by_name(lite().analyze("The shoelaces frayed after a week", ASPECTS))
    assert m["Lace"]["evidence"][0]["term"] == "shoelaces"


def test_exact_match_wins_over_suffix():
    m = by_name(lite().analyze("The insole is soft and comfortable", ASPECTS))
    assert "Insole" in m and "Sole" not in m


def test_shared_predicate_goes_to_both_parts():
    m = by_name(lite().analyze("The leather and the laces both feel cheap", ASPECTS))
    assert m["Leather"]["snippet"] == m["Lace"]["snippet"] == "The leather and the laces both feel cheap"
    assert m["Leather"]["label"] == "negative"


def test_trailing_opinions_stay_with_their_part():
    m = by_name(lite().analyze("The sole is sturdy, durable and comfortable", ASPECTS))
    assert m["Sole"]["snippet"] == "The sole is sturdy, durable and comfortable"
    assert set(m) == {"Sole"}


def test_pronoun_attaches_to_previous_part():
    r = lite().analyze("The laces are thin. They snapped after a week.", ASPECTS)
    lace = by_name(r)["Lace"]
    assert "They snapped after a week" in lace["snippet"]
    assert any(e["method"] == "pronoun" for e in lace["evidence"])


def test_general_comment_is_not_pinned():
    r = lite().analyze("Great shoes, the leather is lovely", ASPECTS)
    assert [g["snippet"] for g in r["general"]] == ["Great shoes"]
    assert set(by_name(r)) == {"Leather"}


def test_multiword_part_requires_full_phrase():
    r = lite().analyze("The lace quality is poor but build quality is excellent", ASPECTS)
    m = by_name(r)
    assert m["Build quality"]["label"] == "positive"
    assert m["Lace"]["label"] == "negative"


def test_no_parts_defined():
    r = lite().analyze("Lovely shoes overall", [])
    assert r["mentions"] == [] and r["general"]


def test_labels():
    assert label_for(4.2) == "positive"
    assert label_for(3.0) == "neutral"
    assert label_for(1.9) == "negative"


def test_discourse_words_do_not_split_off_a_part():
    r = lite().analyze("The tongue is awful. Otherwise the leather and sole are solid.",
                       ASPECTS + [{"id": "tg", "name": "Tongue"}])
    m = by_name(r)
    assert m["Leather"]["snippet"] == m["Sole"]["snippet"] == "Otherwise the leather and sole are solid"
