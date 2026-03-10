from __future__ import annotations


def test_normalize_low_evidence_friendliness_rewrites_unknown_russian():
    from src.layers.pro.reasoning.response_style import normalize_low_evidence_friendliness

    out = normalize_low_evidence_friendliness(
        query="Ты готова помогать?",
        language="ru",
        answer="Извините, я не знаю.",
    )
    assert "Да, конечно" in out


def test_normalize_low_evidence_friendliness_preserves_valid_answer():
    from src.layers.pro.reasoning.response_style import normalize_low_evidence_friendliness

    out = normalize_low_evidence_friendliness(
        query="Hi there",
        language="en",
        answer="Absolutely, I can help you with that.",
    )
    assert out == "Absolutely, I can help you with that."
