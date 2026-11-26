"""End-to-end checks with the real models. Run with:  uv run pytest -m slow"""
import pytest

from app.nlp import build_analyzer

pytestmark = pytest.mark.slow

SHOE = [{"id": "lth", "name": "Leather"}, {"id": "lc", "name": "Lace"},
        {"id": "sl", "name": "Sole"}, {"id": "ins", "name": "Insole", "keywords": ["cushioning"]}]
PHONE = [{"id": "bat", "name": "Battery"}, {"id": "dsp", "name": "Display"},
         {"id": "cam", "name": "Camera"}, {"id": "lk", "name": "Looks"}]


@pytest.fixture(scope="module")
def analyzer():
    return build_analyzer("full")


def labels(result):
    return {m["aspect_name"]: m["label"] for m in result["mentions"]}


def test_brief_example(analyzer):
    r = analyzer.analyze("The shoe leather quality is very good but lace quality is not so good", SHOE)
    assert labels(r) == {"Leather": "positive", "Lace": "negative"}


def test_semantic_synonyms(analyzer):
    r = analyzer.analyze("Battery life is amazing, but the screen is dim outdoors "
                         "and the photos come out blurry.", PHONE)
    got = labels(r)
    assert got["Battery"] == "positive"
    assert got["Display"] == "negative"
    assert "Camera" in got


def test_traction_maps_to_sole(analyzer):
    r = analyzer.analyze("The traction is excellent on wet rocks", SHOE)
    assert labels(r) == {"Sole": "positive"}


def test_opinion_word_does_not_create_part(analyzer):
    r = analyzer.analyze("The sole is sturdy, durable and comfortable", SHOE)
    assert labels(r) == {"Sole": "positive"}


def test_star_scale(analyzer):
    r = analyzer.analyze("Absolutely terrible, the laces broke on day one", SHOE)
    assert 1.0 <= r["overall"]["stars"] <= 2.5


HEADPHONES = [{"id": "snd", "name": "Sound", "keywords": ["audio", "bass"]},
              {"id": "mic", "name": "Microphone", "keywords": ["mic", "calls"]}]


def test_incidental_word_does_not_claim_second_part(analyzer):
    r = analyzer.analyze("The microphone picks up a lot of background noise on calls", HEADPHONES)
    assert set(labels(r)) == {"Microphone"}


def test_coordinated_synonym_still_matches(analyzer):
    r = analyzer.analyze("The battery and the photos are great", PHONE)
    assert labels(r) == {"Battery": "positive", "Camera": "positive"}


def test_feels_phrasing_is_not_neutral(analyzer):
    r = analyzer.analyze("The leather feels premium. The laces feel cheap and fray easily.", SHOE)
    assert labels(r) == {"Leather": "positive", "Lace": "negative"}
