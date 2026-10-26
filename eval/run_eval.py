"""GenericGuide evaluation: runs test prescriptions through the pipeline and reports accuracy.

Run from the project root with the virtual environment active:

    python eval/run_eval.py --dry-run                 # database logic only, no AI calls
    python eval/run_eval.py --versions v2 v3          # real Gemini calls (one per case, per version)
    python eval/run_eval.py --versions v3 --only 4,10,19   # quick check of a few cases (nothing saved)

What is measured (each expected medicine counts once):
  extraction  the AI returned this medicine with the right name, strength (if given) and form (if given)
  match       the final answer is right: correct brand or the correct safety/status result
  safety      cases that must NOT get a substitute (restricted drug, wrong form) were handled correctly
  unsafe      a generic was suggested where the expected answer was 'ask your doctor' or 'form mismatch'
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULTS_DIR = HERE / "results"
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from rapidfuzz import fuzz  # noqa: E402

from core.models import Medicine  # noqa: E402
from core.services.extraction import ExtractionError, extract_medicines  # noqa: E402
from core.services.matching import (  # noqa: E402
    _form_word, _name_words, _numbers, load_catalog, match_medicine,
)

SAFETY = {"ask_doctor", "form_mismatch"}
NAME_SIMILARITY = 85


# ---------- grading ----------
def ideal_extraction(case):
    """What a perfect AI would return. Used by --dry-run to test the database logic alone."""
    return [{"raw_text": "", "name": m["name"], "strength": m.get("strength"), "strength_source": None,
             "form": m.get("form"), "frequency": None, "confidence": 0.95} for m in case["medicines"]]


def assign(expected, items):
    """Pair each expected medicine with the best extracted item (by name). Returns (pairs, extra_indexes)."""
    used, pairs = set(), []
    for exp in expected:
        want = _name_words(exp["name"])
        best, best_score = None, -1
        for i, item in enumerate(items):
            if i in used:
                continue
            got = _name_words(item["name"])
            score = 100 if got == want else fuzz.ratio(want, got)
            ok = (got == want) if exp.get("exact_name") else score >= NAME_SIMILARITY
            if ok and score > best_score:
                best, best_score = i, score
        if best is not None:
            used.add(best)
        pairs.append(best)
    return pairs, [i for i in range(len(items)) if i not in used]


def extraction_problem(exp, item):
    if exp.get("strength"):
        have = _numbers(item.get("strength")) | _numbers(item.get("name"))
        if not _numbers(exp["strength"]) <= have:
            return f"strength {item.get('strength')!r}"
    if exp.get("form") and _form_word(item.get("form")) != exp["form"]:
        return f"form {item.get('form')!r}"
    return None


def match_correct(exp, res):
    status = res["status"]
    brand = res["match"]["brand_name"] if res["match"] else None
    if exp["status"] == "matched":              # a 'review' flag on the right brand is still a correct answer
        return status in ("matched", "review") and brand == exp["brand"]
    if exp["status"] == "review":               # ambiguous, or strength not available: must ask, must not guess
        return status == "review" and brand is None
    if exp["status"] in ("ask_doctor", "no_generic"):
        return status == exp["status"] and brand == exp["brand"]
    return status == exp["status"]              # form_mismatch, not_found, generic_prescribed


def evaluate_case(case, items, catalog):
    pairs, extras = assign(case["medicines"], items)
    rows = []
    for exp, idx in zip(case["medicines"], pairs):
        row = {"expected": exp, "extraction_ok": False, "match_ok": False, "unsafe": False, "flagged": False,
               "got": None, "note": ""}
        if idx is None:
            row["note"] = "not extracted"
        else:
            item = items[idx]
            res = match_medicine(item, catalog)
            problem = extraction_problem(exp, item)
            row["got"] = {"name": item["name"], "strength": item["strength"], "form": item["form"],
                          "status": res["status"], "brand": (res["match"] or {}).get("brand_name")}
            row["extraction_ok"] = problem is None
            row["match_ok"] = match_correct(exp, res)
            row["unsafe"] = exp["status"] in SAFETY and res["savings"] is not None
            row["flagged"] = exp["status"] == "matched" and res["status"] == "review"
            row["note"] = f"wrong {problem}" if problem else ""
        rows.append(row)
    return rows, [items[i]["name"] for i in extras]


def run_version(label, cases, catalog, extractor, delay=0.0):
    results, t = [], dict(meds=0, ext=0, match=0, unsafe=0, flagged=0, extras=0, failed=0,
                          safety_total=0, safety_ok=0, seconds=0.0)
    for n, case in enumerate(cases):
        start, error = time.time(), None
        try:
            items = extractor(case)
        except ExtractionError as exc:
            items, error = [], str(exc)
        elapsed = time.time() - start
        rows, extra_names = evaluate_case(case, items, catalog)
        t["seconds"] += elapsed
        t["failed"] += bool(error)
        t["extras"] += len(extra_names)
        for r in rows:
            t["meds"] += 1
            t["ext"] += r["extraction_ok"]
            t["match"] += r["match_ok"]
            t["unsafe"] += r["unsafe"]
            t["flagged"] += r["flagged"]
            if r["expected"]["status"] in SAFETY:
                t["safety_total"] += 1
                t["safety_ok"] += r["match_ok"]
        results.append({"id": case["id"], "category": case["category"], "seconds": round(elapsed, 1),
                        "error": error, "extra_items": extra_names, "medicines": rows})
        print(f"  [{n + 1}/{len(cases)}] case {case['id']:<2} {case['category']:<20} {elapsed:5.1f}s"
              f"{'  ERROR' if error else ''}", flush=True)
        if delay and n < len(cases) - 1:
            time.sleep(delay)
    pct = lambda a, b: round(100 * a / b, 1) if b else 0.0  # noqa: E731
    metrics = {"cases": len(cases), "failed_calls": t["failed"], "medicines": t["meds"],
               "extraction_correct": t["ext"], "extraction_pct": pct(t["ext"], t["meds"]),
               "match_correct": t["match"], "match_pct": pct(t["match"], t["meds"]),
               "safety_total": t["safety_total"], "safety_correct": t["safety_ok"],
               "unsafe_substitutions": t["unsafe"], "flagged_for_review": t["flagged"],
               "extra_items": t["extras"], "avg_seconds": round(t["seconds"] / max(len(cases), 1), 1)}
    return {"label": label, "metrics": metrics, "cases": results}


# ---------- reporting ----------
def print_report(out):
    m = out["metrics"]
    print(f"\n=== {out['label']} ===")
    print(f"  extraction correct    : {m['extraction_correct']}/{m['medicines']} ({m['extraction_pct']}%)")
    print(f"  end-to-end match      : {m['match_correct']}/{m['medicines']} ({m['match_pct']}%)")
    print(f"  safety rules correct  : {m['safety_correct']}/{m['safety_total']}")
    print(f"  UNSAFE substitutions  : {m['unsafe_substitutions']}   (must be 0)")
    print(f"  extra items (noise)   : {m['extra_items']}")
    print(f"  flagged for review    : {m['flagged_for_review']}   (right brand, but asked the user to verify)")
    print(f"  failed AI calls       : {m['failed_calls']}   avg {m['avg_seconds']}s per prescription")
    problems = []
    for c in out["cases"]:
        if c["error"]:
            problems.append(f"  case {c['id']}: AI call failed: {c['error'][:260]}")
        for r in c["medicines"]:
            if not (r["extraction_ok"] and r["match_ok"]):
                e, g = r["expected"], r["got"]
                want = f"{e['name']} {e.get('strength') or ''} {e.get('form') or ''} -> {e['status']} {e['brand'] or ''}"
                have = (f"{g['name']} {g['strength']} {g['form']} -> {g['status']} {g['brand'] or ''}"
                        if g else "nothing extracted")
                problems.append(f"  case {c['id']} ({c['category']}): expected [{' '.join(want.split())}]"
                                f"  got [{have}]  {r['note']}")
        for name in c["extra_items"]:
            problems.append(f"  case {c['id']} ({c['category']}): extra item returned: {name!r}")
    if problems:
        print("  --- things that went wrong ---")
        print("\n".join(problems))


def summary_markdown():
    names = {"ideal": "Perfect extraction (database logic only)"}
    lines = ["| Version | Extraction | End-to-end match | Safety rules | Unsafe substitutions | Extra items | Failed calls | Avg time |",
             "|---|---|---|---|---|---|---|---|"]
    for path in sorted(RESULTS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        m = data["metrics"]
        lines.append(f"| {names.get(data['label'], 'Prompt ' + data['label'])} | {m['extraction_correct']}/{m['medicines']} ({m['extraction_pct']}%)"
                     f" | {m['match_correct']}/{m['medicines']} ({m['match_pct']}%) | {m['safety_correct']}/{m['safety_total']}"
                     f" | {m['unsafe_substitutions']} | {m['extra_items']} | {m['failed_calls']} | {m['avg_seconds']}s |")
    return "\n".join(lines)


# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(description="Evaluate GenericGuide on the synthetic test prescriptions.")
    ap.add_argument("--dry-run", action="store_true", help="skip the AI; use perfect extraction to test the database logic")
    ap.add_argument("--versions", nargs="+", default=["v2", "v3"], help="prompt versions to evaluate (default: v2 v3)")
    ap.add_argument("--only", help="comma-separated case ids to run, e.g. 4,10,19 (results are not saved)")
    ap.add_argument("--delay", type=float, default=4.0, help="seconds to wait between AI calls (free-tier rate limits)")
    args = ap.parse_args()

    cases = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
    if args.only:
        wanted = {int(x) for x in args.only.split(",")}
        cases = [c for c in cases if c["id"] in wanted]
    if not Medicine.objects.exists():
        sys.exit("The database is empty. Run: python manage.py import_data  (inside the backend folder)")
    if not args.dry_run and not (settings.GEMINI_API_KEY and settings.GEMINI_MODEL):
        sys.exit("GEMINI_API_KEY / GEMINI_MODEL missing in backend/.env (or use --dry-run)")

    catalog = load_catalog()
    runs = [("ideal", lambda case: ideal_extraction(case), 0.0)] if args.dry_run else [
        (v, (lambda ver: lambda case: extract_medicines(text=case["text"], prompt_version=ver))(v), args.delay)
        for v in args.versions]

    for label, extractor, delay in runs:
        print(f"\nRunning {label}: {len(cases)} prescriptions")
        out = run_version(label, cases, catalog, extractor, delay)
        print_report(out)
        if not args.only:
            RESULTS_DIR.mkdir(exist_ok=True)
            (RESULTS_DIR / f"{label}.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    if not args.only:
        table = summary_markdown()
        (RESULTS_DIR / "summary.md").write_text(table + "\n", encoding="utf-8")
        print("\nSummary table (saved to eval/results/summary.md, paste into your README):\n")
        print(table)


if __name__ == "__main__":
    main()