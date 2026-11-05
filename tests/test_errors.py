from inf8239_u02.errors import CATEGORY_DESCRIPTIONS, CATEGORY_NAMES, categorize_error


def test_taxonomy_has_twenty_categories_with_descriptions():
    assert len(CATEGORY_NAMES) == 20
    assert len(set(CATEGORY_NAMES)) == 20
    for name in CATEGORY_NAMES:
        assert CATEGORY_DESCRIPTIONS[name]


def test_negation_with_nearby_sentiment_is_detected():
    category, signals = categorize_error("The headset was not comfortable at all.")
    assert category == "negacion"
    assert any("comfortable" in signal for signal in signals)


def test_irony_is_detected():
    category, _ = categorize_error("Yeah right, the service was great!")
    assert category == "ironia"


def test_contrast_is_detected():
    category, _ = categorize_error("The food was great but the service was slow.")
    assert category == "contraste"


def test_short_text_is_detected():
    category, _ = categorize_error("Excellent product")
    assert category == "texto_corto"


def test_out_of_domain_requires_no_sentiment_and_no_domain():
    category, _ = categorize_error("Quantum chromodynamics describes the strong interaction.")
    assert category == "fuera_de_dominio"


def test_case_insensitive_and_stable():
    first = categorize_error("GREAT service, very nice")
    second = categorize_error("great service, very nice")
    assert first[0] == second[0]
