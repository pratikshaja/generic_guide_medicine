"""Step 1 of the pipeline: ask Gemini to turn prescription text/photo into structured JSON.

The model only EXTRACTS. Salts, prices and substitutions never come from the model.
"""
import json
import re
import time

from django.conf import settings

from .prompts import DEFAULT_PROMPT_VERSION, PROMPTS


class ExtractionError(Exception):
    """Raised when the AI step fails or returns something unusable."""


def _strip_fences(text):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    return re.sub(r"\s*```$", "", text).strip()


def _clean_value(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _medicine_list(data):
    """Find the list of medicines in the AI's JSON, tolerating common shape mistakes."""
    if isinstance(data, list):                      # bare list: [{...}, {...}]
        return data
    if isinstance(data, dict):
        if isinstance(data.get("medicines"), list):
            return data["medicines"]
        if "medicines" in data and data["medicines"] is None:
            return []                              
        lists = [v for v in data.values() if isinstance(v, list)]
        if len(lists) == 1:                         
            return lists[0]
        if "name" in data:                         
            return [data]
    return None


def validate_extraction(data):
    """Check the JSON shape and return a clean list of medicine dicts."""
    medicines = _medicine_list(data)
    if medicines is None:
        raise ValueError(f"unexpected JSON shape: {json.dumps(data)[:120]}")
    cleaned = []
    for m in medicines:
        if not isinstance(m, dict) or not _clean_value(m.get("name")):
            continue
        try:
            confidence = max(0.0, min(1.0, float(m.get("confidence"))))
        except (TypeError, ValueError):
            confidence = 0.0
        cleaned.append({
            "raw_text": _clean_value(m.get("raw_text")) or "",
            "name": _clean_value(m.get("name")),
            "strength": _clean_value(m.get("strength")),
            "strength_source": _clean_value(m.get("strength_source")),
            "form": (_clean_value(m.get("form")) or "").lower() or None,
            "frequency": _clean_value(m.get("frequency")),
            "confidence": confidence,
        })
    return cleaned


RETRYABLE = ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "500", "INTERNAL", "DEADLINE")


def _call_model(contents):
    if not settings.GEMINI_API_KEY:
        raise ExtractionError("GEMINI_API_KEY is not set in backend/.env")
    if not settings.GEMINI_MODEL:
        raise ExtractionError("GEMINI_MODEL is not set in backend/.env")
    from google import genai
    from google.genai import types

    config = {"response_mime_type": "application/json", "temperature": 0}
    if settings.GEMINI_THINKING_BUDGET not in (None, ""):
        config["thinking_config"] = types.ThinkingConfig(
            thinking_budget=int(settings.GEMINI_THINKING_BUDGET)
        )

    models = [settings.GEMINI_MODEL]
    if getattr(settings, "GEMINI_FALLBACK_MODEL", None):
        models.append(settings.GEMINI_FALLBACK_MODEL)

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    last_error = None
    for model in models:                      # main model first, then the fallback
        for attempt in range(3):              # temporary overload: wait a little and retry
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(**config),
                )
                return response.text
            except Exception as exc:
                last_error = exc
                if not any(code in str(exc) for code in RETRYABLE):
                    raise ExtractionError(f"AI service error: {exc}") from exc
                time.sleep(2 * (attempt + 1))
    raise ExtractionError(f"The AI service is busy right now. Please try again in a minute. ({last_error})")


def extract_medicines(text="", image_bytes=None, mime_type=None,
                      prompt_version=DEFAULT_PROMPT_VERSION):
    """Return a list of extracted medicines. Retries once if the JSON is malformed."""
    if not text and not image_bytes:
        raise ExtractionError("Nothing to analyse: send prescription text or an image")
    prompt = PROMPTS[prompt_version].replace(
        "{prescription}", text if text else "(see the attached image)"
    )
    contents = [prompt]
    if image_bytes:
        from google.genai import types
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

    last_error = None
    for _attempt in range(2):
        raw = _call_model(contents)
        try:
            return validate_extraction(json.loads(_strip_fences(raw)))
        except (ValueError, TypeError) as exc:  # JSONDecodeError is a ValueError
            last_error = f"{exc} (response started: {(raw or '')[:100]!r})"
    raise ExtractionError(f"AI returned malformed JSON twice: {last_error}")