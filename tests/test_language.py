from types import SimpleNamespace

from satchetak.config import Settings
from satchetak.language import explain_with_qwen


FACTS = {
    "headline": "12.50 ha needs attention",
    "direct_answer": "The screen found 12.50 ha of repeated surface change.",
    "confidence": "Moderate screening confidence",
    "confidence_reason": "The category repeated across dates.",
    "evidence_points": ["12.50 ha repeated."],
    "decision_relevance": ["Inspect the changed surface."],
    "limitations": ["This does not prove construction."],
    "next_action": "Inspect the region on site.",
    "source": "deterministic_verified_evidence",
}


def test_qwen_is_optional_and_falls_back_to_verified_text(tmp_path):
    result = explain_with_qwen(FACTS, Settings(data_dir=tmp_path, qwen_base_url=None))
    assert result["plain_language_summary"].startswith(FACTS["direct_answer"])
    assert result["plain_language_summary"].endswith(FACTS["next_action"])
    assert result["language_source"] == "deterministic_fallback"


def test_qwen_paraphrase_is_used_when_numbers_are_verified(monkeypatch, tmp_path):
    response = SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {"choices": [{"message": {"content": "The evidence shows 12.50 ha of repeated surface change. This may matter to your land decision, but it does not prove construction. Inspect the region on site."}}]},
    )
    monkeypatch.setattr("satchetak.language.httpx.post", lambda *args, **kwargs: response)
    result = explain_with_qwen(FACTS, Settings(data_dir=tmp_path, qwen_base_url="http://qwen.test/v1"))
    assert result["language_source"].startswith("qwen:")
    assert result["plain_language_summary"].startswith("The evidence")


def test_qwen_paraphrase_with_invented_number_is_rejected(monkeypatch, tmp_path):
    response = SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {"choices": [{"message": {"content": "The evidence shows 99 ha of change, so inspect this land carefully before making any decision about it."}}]},
    )
    monkeypatch.setattr("satchetak.language.httpx.post", lambda *args, **kwargs: response)
    result = explain_with_qwen(FACTS, Settings(data_dir=tmp_path, qwen_base_url="http://qwen.test/v1"))
    assert result["language_source"] == "deterministic_fallback"
    assert result["plain_language_summary"].startswith(FACTS["direct_answer"])
    assert result["plain_language_summary"].endswith(FACTS["next_action"])


def test_qwen_paraphrase_without_verified_final_action_is_rejected(monkeypatch, tmp_path):
    response = SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {"choices": [{"message": {"content": "The evidence shows 12.50 ha of repeated surface change. This does not prove construction, so consider investigating the site."}}]},
    )
    monkeypatch.setattr("satchetak.language.httpx.post", lambda *args, **kwargs: response)
    result = explain_with_qwen(FACTS, Settings(data_dir=tmp_path, qwen_base_url="http://qwen.test/v1"))
    assert result["language_source"] == "deterministic_fallback"
    assert result["plain_language_summary"].startswith(FACTS["direct_answer"])
    assert result["plain_language_summary"].endswith(FACTS["next_action"])
