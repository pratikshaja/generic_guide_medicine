"""Extraction prompts. Every version is kept so the evaluation script can compare them."""

PROMPT_V2 = """You extract medicines from prescription text.

Return ONLY valid JSON, no explanation, in this exact format:
{"medicines":[{"name":"","strength":"","form":"","frequency":"","confidence":0.0}]}

Rules:
- name is the brand name exactly as written, without the form word (Tab/Cap/Syp)
- strength is e.g. "650mg", or null if not written
- form is one of: tablet, capsule, syrup, injection, or null if unclear
- frequency is the instruction as written (e.g. "OD", "BD", "TDS")
- confidence is 0 to 1 for how sure you are about this item
- if something is not written or unclear, use null. Never guess.

Prescription:
{prescription}
"""

PROMPT_V3 = """You extract medicines from prescription text for a database lookup.

Return ONLY valid JSON in exactly this format:
{"medicines":[{"raw_text":"","name":"","strength":"","strength_source":"","form":"","frequency":"","confidence":0.0}]}

Rules:
- Include only medicines. Ignore diagnosis, advice, patient details and dates.
- raw_text: the exact line as written, so a human can check it.
- name: the brand name as written. Do NOT correct spellings (keep "Cetzin" as "Cetzin").
- strength: e.g. "650mg" or "50mcg". Use only what is written.
  If the strength is only a number inside the brand name (Dolo 650, Omez 20), return that number
  with its likely unit and set strength_source to "inferred_from_name".
  If a unit is written, set strength_source to "written".
  If there is no strength, use null and strength_source null.
- form: tablet, capsule, syrup, injection or other. Use Tab/Cap/Syp/Inj as hints. null if unclear.
- frequency: as written (OD, BD, TDS, HS, prn). null if not written.
- confidence: 0 to 1. Lower it when text is unclear, misspelled or strength is inferred.
- Never guess. Use null for anything not in the text.
- If the prescription is an attached image, read it from the image.

Prescription:
{prescription}
"""

PROMPTS = {"v2": PROMPT_V2, "v3": PROMPT_V3}
DEFAULT_PROMPT_VERSION = "v3"