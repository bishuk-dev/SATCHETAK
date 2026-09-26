"""Optional Qwen narration over immutable verified facts."""
from __future__ import annotations

import json
import re
from typing import Any

import httpx

from .config import Settings


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?", text))


def _deterministic_narrative(interpretation: dict[str, Any]) -> str:
    """Build a useful plain-language answer even when the optional LLM is unavailable."""
    sections = [
        interpretation["direct_answer"],
        interpretation["confidence_reason"],
        *interpretation["decision_relevance"],
        *interpretation["limitations"],
        interpretation["next_action"],
    ]
    return " ".join(str(section).strip() for section in sections if str(section).strip())


def _validated_narrative(content: str, facts: dict[str, Any]) -> str:
    narrative = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    if not 40 <= len(narrative) <= 1_200:
        raise ValueError("Qwen response length is outside the accepted range")
    allowed_numbers = _numbers(json.dumps(facts, ensure_ascii=False))
    invented = _numbers(narrative) - allowed_numbers
    if invented:
        raise ValueError(f"Qwen introduced unverified numbers: {sorted(invented)}")
    expected_action = str(facts["next_action"]).strip().rstrip(".!?").casefold()
    actual_ending = narrative.rstrip().rstrip(".!?").casefold()
    if not actual_ending.endswith(expected_action):
        raise ValueError("Qwen did not preserve the verified next action as its final sentence")
    return narrative


def explain_with_qwen(interpretation: dict[str, Any], settings: Settings) -> dict[str, Any]:
    enriched = dict(interpretation)
    enriched["plain_language_summary"] = _deterministic_narrative(interpretation)
    enriched["language_source"] = "deterministic_fallback"
    if not settings.qwen_base_url:
        enriched["language_status"] = "Qwen is not configured; verified deterministic wording is shown."
        return enriched
    facts = {
        "headline": interpretation["headline"],
        "direct_answer": interpretation["direct_answer"],
        "confidence": interpretation["confidence"],
        "confidence_reason": interpretation["confidence_reason"],
        "evidence_points": interpretation["evidence_points"],
        "decision_relevance": interpretation["decision_relevance"],
        "limitations": interpretation["limitations"],
        "next_action": interpretation["next_action"],
    }
    prompt = (
        "TASK: Turn VERIFIED_FACTS into one clear paragraph for a non-technical land buyer or farmer. "
        "HARD RULES: (1) Only restate VERIFIED_FACTS. (2) Add no possible causes, examples, suitability claims, "
        "risks, benefits, impacts, conclusions, or new advice. (3) Preserve every number exactly; do not round, "
        "calculate, add, or omit measurements. (4) Do not give a buy/no-buy verdict. (5) The paragraph must end "
        f"with this exact action: {facts['next_action']} Before responding, silently verify the final action. "
        "Return only the paragraph.\nVERIFIED_FACTS=" + json.dumps(facts, ensure_ascii=False)
    )
    try:
        messages = [
            {"role": "system", "content": "Follow the hard rules literally. Never infer beyond VERIFIED_FACTS."},
            {"role": "user", "content": prompt},
        ]

        def request_narrative(conversation: list[dict[str, str]]) -> str:
            response = httpx.post(
                settings.qwen_base_url.rstrip("/") + "/chat/completions",
                headers={"Authorization": f"Bearer {settings.qwen_api_key}"},
                json={
                    "model": settings.qwen_model,
                    "messages": conversation,
                    "temperature": 0,
                    "max_tokens": 600,
                },
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

        content = request_narrative(messages)
        try:
            narrative = _validated_narrative(content, facts)
        except ValueError as exc:
            if "verified next action" not in str(exc):
                raise
            correction = (
                "Revise the paragraph once. Keep only VERIFIED_FACTS and finish with the following sentence "
                f"word for word: {facts['next_action']}"
            )
            content = request_narrative([
                *messages,
                {"role": "assistant", "content": content},
                {"role": "user", "content": correction},
            ])
            narrative = _validated_narrative(content, facts)
        enriched["plain_language_summary"] = narrative
        enriched["language_source"] = f"qwen:{settings.qwen_model}"
        enriched["language_status"] = "Qwen paraphrase validated against the verified evidence contract."
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        detail = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        enriched["language_status"] = f"Qwen unavailable or rejected; verified fallback used ({detail})."
    return enriched
