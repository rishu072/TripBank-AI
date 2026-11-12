import json

import httpx

from ..config import settings
from ..errors import AppError

PROMPT_VERSION = "v1"


def configured():
    return bool(settings.gemini_api_key)


def generate(system, user, schema=None, temperature=0.2):
    if not configured():
        raise AppError("AI_NOT_CONFIGURED", "Gemini API key is not configured", 503)
    cfg = {"temperature": temperature}
    if schema:
        cfg["responseMimeType"] = "application/json"
        cfg["responseSchema"] = schema
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": cfg,
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
    try:
        r = httpx.post(url, headers={"x-goog-api-key": settings.gemini_api_key}, json=body, timeout=40)
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except (httpx.HTTPError, KeyError, IndexError):
        raise AppError("AI_UNAVAILABLE", "The AI service is unavailable right now", 502)
    if schema:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise AppError("AI_INVALID_OUTPUT", "The AI returned an unreadable answer", 502)
    return text.strip()
