import json
import os
import re
from typing import Any, Optional

import logging
import requests

logger = logging.getLogger(__name__)


def _build_messages(prompt: str, hotel_name: str, location: str) -> list[dict[str, str]]:
    system = (
        "You are a luxury hotel copywriter. Return ONLY valid JSON with keys: "
        "headline, description, amenities."
    )
    user = (
        "Rules:\n"
        "- headline: short, premium, 6-12 words\n"
        "- description: 2 short sentences, calm editorial tone\n"
        "- amenities: array of 4-6 items, each 2-5 words\n"
        "- include user-requested features if mentioned\n"
        f"Hotel name: {hotel_name}\n"
        f"Location: {location}\n"
        f"User prompt: {prompt}\n"
        "Return JSON only."
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _extract_json(text: str) -> Optional[dict[str, Any]]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _trim_sentences(text: str, max_sentences: int) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    return " ".join(sentences[:max_sentences])


def _shorten_description(text: str, max_chars: int = 220) -> str:
    trimmed = _trim_sentences(text, 2)
    if len(trimmed) <= max_chars:
        return trimmed
    return trimmed[: max_chars].rsplit(" ", 1)[0] + "."


def _trim_amenity_words(text: str, max_words: int = 5) -> str:
    parts = [w for w in text.split() if w]
    return " ".join(parts[:max_words])


def _normalize_amenities(value: Any) -> list[str]:
    items: list[str] = []
    if isinstance(value, list):
        items = [str(v).strip() for v in value if str(v).strip()]
    elif isinstance(value, str):
        parts = re.split(r"\s*[,|\n]\s*", value)
        items = [p.strip() for p in parts if p.strip()]

    cleaned: list[str] = []
    for item in items:
        trimmed = _trim_amenity_words(item, 5)
        if trimmed:
            cleaned.append(trimmed)
    return cleaned[:5]


def generate_copy(prompt: str, hotel_name: str, location: str) -> Optional[dict[str, Any]]:
    token = os.getenv("HF_API_TOKEN")
    model = os.getenv("HF_T5_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    if not token:
        logger.warning("HF_API_TOKEN missing; skipping T5 generation.")
        return None
    logger.info("T5: using model %s", model)

    url = "https://router.huggingface.co/v1/chat/completions"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "model": model,
        "messages": _build_messages(prompt, hotel_name, location),
        "temperature": 0.8,
        "max_tokens": 240,
        "response_format": {"type": "json_object"},
    }

    for _ in range(3):
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code >= 500:
            logger.warning("T5 server error (status=%s).", resp.status_code)
            continue
        if resp.status_code != 200:
            logger.warning("T5 request failed (status=%s): %s", resp.status_code, resp.text[:200])
            return None
        try:
            data = resp.json()
        except ValueError:
            logger.warning("T5 response not JSON.")
            return None

        if isinstance(data, dict) and data.get("error"):
            logger.warning("T5 error response: %s", str(data.get("error"))[:200])
            return None

        generated = None
        if isinstance(data, dict):
            choices = data.get("choices") or []
            if choices and isinstance(choices[0], dict):
                message = choices[0].get("message") or {}
                generated = message.get("content")

        if not generated:
            logger.warning("T5 response missing generated_text.")
            return None

        parsed = _extract_json(generated)
        if not parsed:
            logger.warning("T5 JSON parse failed. Raw: %s", generated[:200])
            return None

        headline = str(parsed.get("headline", "")).strip()
        description = _shorten_description(str(parsed.get("description", "")).strip())
        amenities = _normalize_amenities(parsed.get("amenities"))

        if not headline or not description or len(amenities) < 4:
            logger.warning("T5 output incomplete. headline=%s amenities=%s", bool(headline), len(amenities))
            return None

        logger.info("T5: generation OK (headline len=%s, amenities=%s)", len(headline), len(amenities))
        return {
            "headline": headline,
            "description": description,
            "amenities": amenities[:5],
        }

    return None
