"""Glue: extraction (AI) -> matching (database + rules) -> saved Analysis record."""
from core.models import Analysis

from .extraction import extract_medicines
from .matching import DISCLAIMER, load_catalog, match_medicine, summarize


def analyze(text="", image_bytes=None, mime_type=None, save=True):
    items = extract_medicines(text=text, image_bytes=image_bytes, mime_type=mime_type)
    catalog = load_catalog()
    results = [match_medicine(item, catalog) for item in items]
    payload = {"results": results, "summary": summarize(results), "disclaimer": DISCLAIMER}
    if save:
        Analysis.objects.create(input_text=text or "[image upload]",
                                extracted_json=items, result_json=payload)
    return payload