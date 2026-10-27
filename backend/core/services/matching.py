"""Step 2 of the pipeline: match extracted names to the medicine database.

All prices, salts, generics and safety rules come from the DATABASE, never from the AI.
The matching logic is pure Python so it can be tested without Django.
"""
import re

from rapidfuzz import fuzz, process

AUTO_THRESHOLD = 85      # name similarity at/above this = confident match
REVIEW_THRESHOLD = 70    # between REVIEW and AUTO = "please verify"
LOW_CONFIDENCE = 0.75    # AI confidence below this = "please verify"

FORM_WORDS = ("tablet", "capsule", "syrup", "injection")
NOISE_WORDS = {"duo", "forte", "mg", "mcg", "ml", "iu", "gm"}
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
NUMERIC_TOKEN_RE = re.compile(r"\d+(?:\.\d+)?(?:k|mg|mcg|ml|iu|g)?")

DISCLAIMER = (
    "Not medical advice. Prices are sample data. Always confirm with your doctor "
    "or pharmacist before changing any medicine."
)


# ---------- text helpers ----------
def _norm(text):
    text = (text or "").lower().replace("-", " ")
    text = re.sub(r"[^a-z0-9. ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _name_words(text):
    """Brand name without numbers, e.g. 'Dolo 650' -> 'dolo', 'Taxim-O 200' -> 'taxim o'."""
    text = re.sub(r"([a-z]{3,})(\d)", r"\1 \2", _norm(text))   # "dolo650" -> "dolo 650"
    tokens = [t.strip(".") for t in text.split()]
    return " ".join(t for t in tokens if t and not NUMERIC_TOKEN_RE.fullmatch(t) and t not in NOISE_WORDS)


def _numbers(text):
    return {float(n) for n in NUMBER_RE.findall(text or "")}


def _display_base(brand_name):
    """'Augmentin 625 Duo' -> 'Augmentin', 'Glycomet-SR 500' -> 'Glycomet-SR'."""
    return re.sub(r"[\s-]*\d.*$", "", brand_name).strip() or brand_name


def _form_word(form):
    word = _norm(form).split(" ")[0] if form else ""
    return word if word in FORM_WORDS else None


# ---------- catalog ----------
def prepare_catalog(medicines, generics, restricted):
    """medicines/generics: lists of dicts; restricted: {salt: reason}."""
    bases = {}
    for m in medicines:
        m = dict(m)
        m["_base"] = _name_words(m["brand_name"])
        m["_numbers"] = _numbers(m["brand_name"]) | _numbers(m["strength"])
        bases.setdefault(m["_base"], []).append(m)
    return {
        "salts": {m["salt"].lower() for ms in bases.values() for m in ms},
        "bases": bases,
        "generics": {(g["salt"], g["strength"], g["form"]): g for g in generics},
        "restricted": {s.lower(): r for s, r in restricted.items()},
    }


def load_catalog():
    """Read the catalog from the Django database."""
    from core.models import GenericEquivalent, Medicine, RestrictedSalt

    medicines = [
        {"brand_name": m.brand_name, "salt": m.salt, "strength": m.strength, "form": m.form,
         "pack_size": m.pack_size, "brand_price": float(m.brand_price)}
        for m in Medicine.objects.all()
    ]
    generics = [
        {"salt": g.salt, "strength": g.strength, "form": g.form, "generic_name": g.generic_name,
         "pack_size": g.pack_size, "generic_price": float(g.generic_price), "source": g.source}
        for g in GenericEquivalent.objects.all()
    ]
    restricted = {r.salt: r.reason for r in RestrictedSalt.objects.all()}
    return prepare_catalog(medicines, generics, restricted)


# ---------- matching ----------
def _restricted_reason(salt, catalog):
    for part in salt.lower().split("+"):
        reason = catalog["restricted"].get(part.strip())
        if reason:
            return reason
    return None


def _brand_info(m, score):
    return {"brand_name": m["brand_name"], "salt": m["salt"], "strength": m["strength"],
            "form": m["form"], "pack_size": m["pack_size"], "brand_price": m["brand_price"],
            "match_score": round(score)}


def _option(m):
    return {"brand_name": m["brand_name"], "strength": m["strength"], "form": m["form"]}


def _find_salt(query, catalog):
    """'clopidogrel 75 mg' / 'clopidogret' -> 'clopidogrel'. Strength is already stripped from query."""
    by_words = {_name_words(salt): salt for salt in catalog["salts"]}
    if query in by_words:
        return by_words[query]
    hit = process.extractOne(query, list(by_words), scorer=fuzz.ratio)
    return by_words[hit[0]] if hit and hit[1] >= 88 else None


def _match_salt_prescription(item, salt, catalog, result):
    rx_numbers = _numbers(item.get("strength")) | _numbers(item.get("name"))
    rx_form = _form_word(item.get("form"))
    options = [g for (g_salt, _st, _fm), g in catalog["generics"].items()
               if g_salt == salt and (not rx_numbers or _numbers(g["strength"]) & rx_numbers)
               and (not rx_form or _form_word(g["form"]) == rx_form)]
    result["needs_review"] = False
    if len(options) == 1:
        g = options[0]
        result["generic"] = {k: g[k] for k in ("generic_name", "pack_size", "generic_price", "source")}
        result.update(status="generic_prescribed",
                      message="Prescribed by generic (salt) name already. You can ask the pharmacist "
                              "for the lowest-priced version of it.")
    else:
        result.update(status="generic_prescribed", needs_review=True,
                      message="Prescribed by generic (salt) name. Strength or form is missing, "
                              "so please confirm which one was prescribed.")
    return result


def match_medicine(item, catalog):
    result = {"input": item, "status": "not_found", "message": "", "needs_review": True,
              "match": None, "generic": None, "savings": None, "alternatives": []}
    query = _name_words(item.get("name") or "")
    if not query:
        result["message"] = "Could not read a medicine name."
        return result

    bases = list(catalog["bases"].keys())
    best = process.extractOne(query, bases, scorer=fuzz.ratio)

    # Prescribed by salt name (e.g. "Metformin 500mg") instead of a brand name
    if best is None or best[1] < AUTO_THRESHOLD:
        salt_name = _find_salt(query, catalog)
        if salt_name:
            return _match_salt_prescription(item, salt_name, catalog, result)

    if best is None or best[1] < REVIEW_THRESHOLD:
        result["message"] = ("No matching brand in our database. Please check the spelling "
                             "or ask your pharmacist.")
        return result
    base, score, _ = best
    candidates = catalog["bases"][base]

    # strength check
    rx_numbers = _numbers(item.get("strength")) | _numbers(item.get("name"))
    if rx_numbers:
        narrowed = [m for m in candidates if m["_numbers"] & rx_numbers]
        if not narrowed:
            result.update(status="review",
                          message=f"Found {_display_base(candidates[0]['brand_name'])}, but not in the strength written. "
                                  "Please verify the strength.",
                          alternatives=[_option(m) for m in candidates])
            return result
        candidates = narrowed

    # form check
    rx_form = _form_word(item.get("form"))
    if rx_form:
        same_form = [m for m in candidates if _form_word(m["form"]) == rx_form]
        if not same_form:
            have = ", ".join(sorted({m["form"] for m in candidates}))
            result.update(status="form_mismatch",
                          message=f"Our database has this brand only as: {have}. "
                                  f"The prescription says {rx_form}, so no substitute is suggested.",
                          alternatives=[_option(m) for m in candidates])
            return result
        candidates = same_form

    if len(candidates) > 1:
        result.update(status="review",
                      message="Several strengths/forms match. Please confirm which one was prescribed.",
                      alternatives=[_option(m) for m in candidates])
        return result

    med = candidates[0]
    result["match"] = _brand_info(med, score)
    needs_review = score < AUTO_THRESHOLD or (item.get("confidence") or 0) < LOW_CONFIDENCE
    result["needs_review"] = needs_review

    reason = _restricted_reason(med["salt"], catalog)
    if reason:
        result.update(status="ask_doctor",
                      message=f"Do not switch without your doctor: {reason}.")
        return result

    generic = catalog["generics"].get((med["salt"], med["strength"], med["form"]))
    if not generic:
        result.update(status="no_generic",
                      message="No generic equivalent for this exact strength and form in our data.")
        return result

    unit_generic = generic["generic_price"] / generic["pack_size"]
    same_qty_cost = round(unit_generic * med["pack_size"], 2)
    saving = round(med["brand_price"] - same_qty_cost, 2)
    percent = round(saving / med["brand_price"] * 100) if med["brand_price"] else 0
    result["generic"] = {k: generic[k] for k in ("generic_name", "pack_size", "generic_price", "source")}
    result["savings"] = {"units_compared": med["pack_size"], "brand_price": med["brand_price"],
                         "generic_price_same_quantity": same_qty_cost,
                         "saving": saving, "saving_percent": percent}
    if needs_review:
        result.update(status="review", message="Likely match, but please verify before relying on it.")
    else:
        result.update(status="matched", message="Generic equivalent found.")
    return result


def summarize(results):
    priced = [r for r in results if r["savings"]]
    brand = round(sum(r["savings"]["brand_price"] for r in priced), 2)
    generic = round(sum(r["savings"]["generic_price_same_quantity"] for r in priced), 2)
    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return {"medicines_found": len(results), "with_savings": len(priced),
            "total_brand_price": brand, "total_generic_price": generic,
            "total_saving": round(brand - generic, 2),
            "saving_percent": round((brand - generic) / brand * 100) if brand else 0,
            "status_counts": counts}