# GenericGuide

Paste a prescription or upload a photo. GenericGuide reads the medicines, finds the generic equivalent of each brand, and shows how much you would save, with safety rules and a disclaimer.

Live app: https://generic-guide-medicine.vercel.app
API: https://genericguide-api.onrender.com/api/analyze/


> The API runs on a free server that sleeps when idle. The first request after a quiet period can take up to a minute. The page shows a "server may be waking up" message while it waits.

---

## The problem

Doctors often prescribe branded medicines even when an equivalent generic (same salt, same strength, same form) costs a fraction of the price. Patients rarely know a generic exists, and comparing prices by hand is slow and error-prone.

This project addresses the question: *Why do branded drugs dominate prescriptions despite equivalent, cheaper generic alternatives?* One reason is that the information is hard to access at the moment of purchase. GenericGuide makes the comparison take a few seconds.

## What it does

1. You paste prescription text or upload a photo.
2. An AI model (Gemini) reads the prescription and returns the medicines as structured data.
3. The app matches each brand against a database and finds the generic with the same salt, strength and form.
4. It shows the brand price, generic price and saving for the same quantity, with a total.
5. Medicines that need care are flagged instead of substituted.

### Result statuses

| Status | Meaning |
|---|---|
| Generic found | A matching generic exists. Prices and saving are shown. |
| Review | Likely match, but the name, strength or AI confidence needs the user to verify. |
| Ask your doctor | Restricted medicine (narrow therapeutic index). No substitution is suggested. |
| Different form | The brand exists only in another form (for example syrup vs tablet). No substitute is suggested. |
| Generic prescribed | The prescription already uses the generic (salt) name. |
| Not found | The brand is not in the database. The app says so and does not guess. |

---

## How it works

```
User input (text or photo)
        |
        v
React frontend --POST /api/analyze/--> Django REST API
                                         | validates input, rate limit
                                         v
                       1. EXTRACTION (Gemini)
                          messy text / photo -> JSON list of medicines
                                         |
                                         v
                       2. MATCHING (no AI)
                          fuzzy brand match -> salt + strength + form
                                         |
                                         v
                       3. SAFETY RULES (no AI)
                          restricted salts, form mismatch, low confidence
                                         |
                                         v
                       4. PRICING (no AI)
                          price per unit, saving, totals
                                         |
                                         v
                          JSON response -> React shows results
```

### Where the AI is used, and where it is not

The AI does one job: it reads the prescription.** Prescriptions contain abbreviations (Tab, OD, BD), typos, extra text (diagnosis, advice) and sometimes handwriting or tilted photos. An LLM handles that well, and Gemini reads images directly, so no separate OCR step is needed.

The AI never decides anything about medicine.** Salts, generic equivalents, prices and safety rules all come from a database and fixed code. This is deliberate:

- A wrong substitution is a medical risk. An LLM can invent a salt or a price, so it is kept away from that decision.
- Matching and pricing can be tested on their own. Any error can be traced to either extraction or database logic.
- Every price is traceable to its source.

### Matching details

- Brands are matched by fuzzy text similarity (`rapidfuzz`). A score of 85 or more is an automatic match, 70 to 84 is flagged for review, and below 70 is "not found".
- Medicines are compared on (salt, strength, form). Combination salts are written `a + b` and SR (sustained release) forms are kept separate from normal tablets.
- Prices are compared **per unit** using each pack's size, so a 15-tablet brand strip and a 10-tablet generic strip compare fairly.
- Extraction confidence below 0.75 puts the item into "review".
- Generic names written with a strength or small spelling mistakes (for example "clopidogrel 75 mg") are recognised.

### Safety rules

- **Restricted salts** (levothyroxine, warfarin, levetiracetam, phenytoin): no substitution is suggested. The app tells the user to ask their doctor.
- **Form mismatch:** a syrup is never matched to a tablet.
- **No guessing:** unknown brands return "Not found".
- Every result page carries a medical disclaimer.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React (Vite), plain CSS |
| Backend | Django, Django REST Framework |
| AI | Google Gemini API (`google-genai`), model set by environment variable, with a fallback model |
| Matching | `rapidfuzz` |
| Database | SQLite locally, Postgres (Neon) in production |
| Hosting | Vercel (frontend), Render (backend), Neon (database), all on free plans |

---

## Evaluation

An evaluation script runs 28 test prescriptions (71 medicine lines) covering clean prescriptions, misspellings, compact names (`dolo650`), combinations, SR forms, restricted salts, form mismatches, unknown brands, noisy text and non-prescription text.

```bash
python eval/run_eval.py --dry-run     # database logic only, with perfect extraction
python eval/run_eval.py               # real Gemini calls, compares prompt versions
```

| Version | Extraction | End-to-end match | Safety rules | Unsafe substitutions |
|---|---|---|---|---|
| Perfect extraction (database logic only) | 71/71 | 71/71 | 9/9 | 0 |
| Prompt v2 | 61/71 | FILL IN | FILL IN | FILL IN |
| Prompt v3 (current) | 71/71 | FILL IN | FILL IN | FILL IN |

The dry run shows the database and safety logic is correct on its own. The v2 to v3 improvement comes from the prompt changes documented in [docs/prompts.md].

Notes on how to read these numbers:

- Test cases 1 to 4 were used while tuning the prompts, so they are not fully unseen. Results on the other 24 cases are the fairer measure.
- The test set is typed text. Photo extraction is not part of the evaluation.

---

## Run it locally

### Requirements

Python 3.12 or later, Node.js 18 or later, and a free Gemini API key from Google AI Studio.

### Backend

```bash
cd backend
python -m venv venv
source venv/Scripts/activate        # Windows Git Bash. On macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env` (this file is git-ignored and must never be committed):

```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=models/your-model-id
GEMINI_FALLBACK_MODEL=models/another-model-id
DEBUG=True
```

Then:

```bash
python manage.py migrate
python manage.py import_data        # loads the brand and generic CSV files
python manage.py runserver
```

The API is now at http://127.0.0.1:8000/api/analyze/.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. With no `VITE_API_URL` set, the frontend calls `http://127.0.0.1:8000`.

---

## API

`POST /api/analyze/`

Send JSON:
```json
{ "text": "Tab Amlokind 5 OD" }
```
or a multipart form with an `image` field (JPEG, PNG or WebP, up to 5 MB). Text is limited to 4,000 characters. The API is rate limited to 60 requests per hour per visitor.

Response (shortened):
```json
{
  "results": [
    {
      "input": { "raw_text": "Tab Amlokind 5 OD", "name": "Amlokind", "strength": "5mg", "form": "tablet", "confidence": 0.9 },
      "status": "matched",
      "match": { "brand_name": "Amlokind 5", "salt": "amlodipine", "brand_price": 28.0 },
      "generic": { "generic_name": "Amlodipine Tablets IP 5mg", "generic_price": 5.68 },
      "savings": { "saving": 22.32, "saving_percent": 80 }
    }
  ],
  "summary": { "medicines_found": 1, "total_saving": 22.32, "saving_percent": 80 },
  "disclaimer": "Not medical advice. ..."
}
```

Error responses: `400` for invalid input, `429` when rate limited, `502` when the AI call fails after retries.

---

## Deployment

| Part | Service | Notes |
|---|---|---|
| Frontend | Vercel | Root directory `frontend`, environment variable `VITE_API_URL` set to the API address |
| Backend | Render (free) | Root directory `backend`. Build: `pip install -r requirements.txt && python manage.py collectstatic --noinput`. Start: `gunicorn config.wsgi:application --timeout 120 --workers 1` |
| Database | Neon (free Postgres) | Connection string in `DATABASE_URL` |

Backend environment variables: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_FALLBACK_MODEL`, `CORS_ALLOWED_ORIGINS`, `PYTHON_VERSION`.

Design choices for production:

- Secrets exist only as environment variables on the host. Nothing secret is in the repository or the frontend.
- CORS uses an explicit allow-list of origins, not "allow all".
- Submitted prescriptions are **not stored** by default (`SAVE_ANALYSES` is off).
- The Gemini call retries on temporary errors (503, 429, 500), falls back to a second model, and retries once on invalid JSON.

---

## Project structure

```
backend/
  config/                  Django settings and URLs
  core/
    models.py              Medicine, GenericEquivalent, RestrictedSalt, Analysis
    views.py               AnalyzeView (POST /api/analyze/)
    services/
      prompts.py           Extraction prompts (v2, v3)
      extraction.py        Gemini call, retries, JSON validation
      matching.py          Brand matching, safety rules, pricing
      pipeline.py          Extraction -> matching -> response
    management/commands/import_data.py
data/                      medicines.csv, generics.csv
eval/                      cases.json, run_eval.py, results/
docs/prompts.md            Prompt history and iterations
frontend/src/              React app and components
```

---

## Data sources

- Generic prices: the Jan Aushadhi (PMBJP) product list, downloaded 25 October 2026. 50 generic entries are included.
- Brands: 100 common brands, with composition, strength, form and pack size.
- Brand prices are approximate sample data**, compiled for this demo. They are not live pharmacy prices and should not be used for real purchasing decisions.

---

## Limitations

- Small database. The demo covers 100 brands and 50 generics. A brand outside it returns "Not found" rather than a guess. This is a data-coverage limit, not an AI limit: adding rows to the CSV files and running `import_data` extends it with no code change. A real product would load a full national drug price list.
- rices are indicative. Generic prices are Jan Aushadhi store prices. Brand prices are approximate.
- Photo extraction is lightly tested. The evaluation uses typed text. Photos of handwriting, poor lighting or unusual angles may be misread. The UI shows how each line was read so the user can check it.
- Substitution is information, not advice.** The tool does not check allergies, interactions, patient age, or other conditions.
- Free hosting. The server sleeps when idle and the first request can be slow. The Gemini free tier has usage limits, which the retry and fallback logic only partly hides.

## Disclaimer

GenericGuide is an educational project. It is not medical advice. Prices are sample data. Always confirm with your doctor or pharmacist before changing any medicine.
