# Personal Finance Tracker

A privacy-first expense tracker that runs entirely on your own machine. Upload a bank or
credit-card CSV, and it parses the file, works out what each purchase was for, and shows you
where the money went.

No account, no server, no sync. The database is a single SQLite file in `backend/`. Nothing
you import ever leaves your computer — including the optional AI categorization, which runs
against a local model.

**Stack:** React (Vite) → FastAPI → SQLite

📐 **[DESIGN.md](DESIGN.md)** — why the code is shaped this way: the categorization cascade,
the learning guards, and the measured failures that motivated them.

---

## Why this exists

Bank CSVs are inconsistent. Some carry a category column, some don't. Bank of America gives
you nothing but a description; Apple Card gives you a category, but also glues the merchant's
full postal address onto the description. Sign conventions disagree — some banks write
purchases as negative, some as positive with a separate Debit/Credit column.

Most of the work in this project is in the layer that turns those messy rows into something
you can actually chart, and in doing it well enough that you rarely have to correct it twice.

## Features

- **Multi-bank CSV import** with automatic format detection (Bank of America, Apple Card)
- **Five-stage auto-categorization** that explains its own reasoning per row
- **Adaptive learning** — correct a transaction once and that merchant stays corrected
- **Optional local LLM** categorization via [Ollama](https://ollama.com); off by default
- **Upload preview** — see every row and its proposed category *before* anything is saved
- **Charts & reports** — spending by category, month, and year
- **Category management** — create and delete categories; deleting one re-files its
  transactions into "Other" rather than destroying them

> **Expenses only.** Positive amounts (income, refunds, payments) are dropped at parse time,
> and the API rejects them with a 422. Every stored amount is negative. This keeps the charts
> answering one question — *where did the money go* — instead of two.

---

## Architecture

```
┌──────────────────────── YOUR COMPUTER ────────────────────────┐
│                                                               │
│   PRESENTATION            BUSINESS LOGIC            DATA      │
│   ┌───────────┐           ┌───────────┐        ┌───────────┐  │
│   │ React     │  /api/*   │ FastAPI   │        │ SQLite    │  │
│   │ (Vite)    │◄─────────►│           │◄──────►│finance.db │  │
│   │  :3000    │           │  :8000    │        │  (file)   │  │
│   └───────────┘           └─────┬─────┘        └───────────┘  │
│                                 │                             │
│                                 │ optional, local             │
│                           ┌─────▼─────┐                       │
│                           │  Ollama   │                       │
│                           │  :11434   │                       │
│                           └───────────┘                       │
└───────────────────────────────────────────────────────────────┘
```

Routes are thin — they validate and delegate. Business logic lives in `app/crud.py` and
`app/utils/`. Each request gets one SQLAlchemy session via a `get_db` dependency. SQLite runs
in WAL mode with `foreign_keys=ON`.

---

## The categorization cascade

This is the core of the app. When a row is parsed, its category is chosen by the most
trustworthy source available, in order:

| # | Stage | Source | Notes |
|---|-------|--------|-------|
| 1 | **Learned mappings** | Your own past corrections | Weighted keyword matches, highest score wins |
| 2 | **Bank's CSV category** | The file itself | Mapped onto your categories via exact/substring/alias match |
| 3 | **Local LLM** | Ollama, if enabled | Only sees rows the bank left unlabelled |
| 4 | **Built-in keywords** | Hardcoded dictionary | Generic fallback so a no-LLM install still works |
| 5 | **"Other"** | — | Nothing matched |

Stage 4 sits *below* the LLM deliberately: it's a generic built-in guess and shouldn't
override a model that actually read the description. It stays in the cascade because a Bank
of America file has no category column at all — without it, every row would import as "Other".
With the LLM off, it places 74 of 83 rows on a real statement in 0.04s.

**Every stage reports itself.** The upload preview shows *how* each row got its category —
"Learned Mapping", "AI Mapping", "Educated System Mapping" — so you can see when the model was
involved and when it wasn't.

### Learning from corrections

Change a transaction's category and the app records the merchant's keywords against the new
category. Because stage 1 outranks everything below it, one correction permanently overrides
both the bank and the model for that merchant.

The same thing happens automatically for rows the LLM categorized during an import. The
practical effect: **re-importing the same file costs zero model calls.** Measured on an 83-row
statement — first pass, 18 LLM calls in ~26s; second pass, 0 calls in 0.0s, with identical
categories on all 83 rows.

### What keeps learning from poisoning itself

A token is only learned if **every** transaction containing it shares one category. Merchant
names concentrate in a single category; street and city names scatter, because people buy all
kinds of things on the same street.

This guard is not decorative. Apple Card descriptions embed the full postal address, so
`usa` appeared in 82 of 83 rows across all six categories. Without the filter, correcting a
single transaction re-filed 82 of the other 83 — and correcting it *back* didn't undo the
damage, it just moved it. Descriptions are also trimmed to the merchant before any of this
runs (fake data: `NORTHWIND MKT* ZQ4KP7VX8800 1420 MAPLE AVENUE RIVERTON ZZ` →
`NORTHWIND MKT* ZQ`), which
removes most address tokens before they can be learned at all.

Notably the rule is **not** frequency-based. Frequency collapses on small files, where 3
Globex rows out of 5 is 60% of the file yet still exactly the mapping worth keeping.

---

## Quick start

**Requirements:** Python 3.11+, Node 18+

### Backend

```bash
cd backend
python -m venv venv
./venv/Scripts/activate          # Windows;  source venv/bin/activate on macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The database is created and seeded with six default categories on first startup.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

| | |
|---|---|
| App | http://localhost:3000 |
| API docs | http://localhost:8000/api/docs |
| Health | http://localhost:8000/api/health |

### Single-server mode (optional)

Build the frontend once and FastAPI will serve it alongside the API, so you only run one
process:

```bash
cd frontend && npm run build
cd ../backend && uvicorn app.main:app       # everything on http://localhost:8000
```

---

## Optional: local AI categorization

Off by default — the app is fully functional without it. When enabled, transactions that
keyword matching can't place are sent to a local Ollama model, which either picks one of your
existing categories or proposes a new one.

```bash
# 1. Install Ollama from https://ollama.com, then pull any instruction-tuned chat model
ollama pull qwen2.5:7b-instruct

# 2. Configure
cp backend/.env.example backend/.env      # then set LLM_ENABLED=true and LLM_MODEL
```

Design constraints worth calling out:

- **Nothing is auto-created.** A category the model invents shows up in the upload preview as
  a suggestion with an Apply button. Ignore it and the row imports as "Other". This is the
  guard against ending up with forty categories.
- **It can never break an import.** Every failure path — disabled, no model, server down, bad
  model name, malformed reply, timeout — returns nothing and falls through to "Other". The
  first failure short-circuits the rest of the file so you don't pay the timeout per merchant.
- **One call per merchant per file**, cached on the extracted keywords, so `NORTHWIND #123`
  and `NORTHWIND #456` share a single call.
- **No model name is hardcoded.** A fresh clone runs keyword-only until you pick one.

---

## Supported banks

| Bank | Category column | Amount convention |
|------|-----------------|-------------------|
| Bank of America | No | Negative = purchase |
| Apple Card | Yes | Positive + separate Debit/Credit column |

Adding a bank means adding one `BankFormatConfig` entry to `BANK_FORMATS` in
`app/utils/csv_parser.py` — header columns for auto-detection, column indices, date format,
and sign handling. No parsing code changes.

---

## API

Interactive docs at `/api/docs`.

**Transactions**
```
GET    /api/transactions/                    list (paginated)
GET    /api/transactions/filter              filter by category ids
GET    /api/transactions/category/{id}       list by category
POST   /api/transactions/                    create manually
PATCH  /api/transactions/{id}                update (triggers learning)
POST   /api/transactions/preview-csv         parse + categorize, save nothing
POST   /api/transactions/upload-csv          parse + categorize + save
GET    /api/transactions/supported-banks     detected formats
```

**Categories**
```
GET    /api/categories/                      list
POST   /api/categories/                      create
DELETE /api/categories/{id}                  delete, re-filing rows into "Other"
```

**Charts** — `/api/charts/`
`category_spending_monthly`, `category_spending_yearly`, `spending_by_year`,
`categories_by_month`, `category_year_comparison`

**Reports** — `/api/reports/`
`daily_and_total_expenses`, `monthly`, `yearly`, `category_spending`

---

## Project structure

```
backend/
├── app/
│   ├── main.py            FastAPI app, startup, router mounting
│   ├── database.py        engine, session, init/reset, SQLite pragmas
│   ├── models.py          SQLAlchemy models, default categories & keywords
│   ├── schemas.py         Pydantic request/response models
│   ├── crud.py            database operations
│   ├── config.py          env-driven settings (LLM)
│   ├── routes/            transactions, categories, charts, reports
│   └── utils/
│       ├── csv_parser.py       bank formats, parsing, merchant trimming
│       ├── categorizer.py      the cascade + adaptive learning
│       ├── llm_categorizer.py  optional Ollama client
│       └── reports_util.py
├── tests/
└── requirements.txt

frontend/
├── src/
│   ├── App.jsx
│   └── components/        CSVUpload, ManualTransactionForm, Dashboard, ChartsReports
└── vite.config.js         dev server + /api proxy
```

---

## Known limitations

[DESIGN.md](DESIGN.md#known-limitations) has the detail:

- **The LLM stage runs twice per import.** `preview-csv` and `upload-csv` each parse the file
  from scratch, so an unmatched merchant is sent to the model once for the preview and again
  on upload. Answers agree at temperature 0. The fix is for the frontend to post the preview's
  decisions back instead of re-deriving them.
- **A bank label the app can't map skips the LLM.** A row labelled `Tolls` or `Airlines` lands
  in "Other" rather than getting a suggestion — you apply the CSV's own label from the preview
  instead. This is what stops a row from showing two competing Apply buttons.
- **Merchant trimming needs a structural boundary.** It cuts at the first token containing a
  digit, or a street suffix. `NORTHWIND RIVERTON` has neither, so the city would survive as a
  keyword; the single-category learning rule is the backstop. Neither supported bank produces
  that shape, but a future format might.
- **The built-in keyword dictionary skews toward Food & Dining** — it's the largest list and
  contains generic words like `market` and `bar`, so it wins ties. Only matters on files with
  no category column of their own.
- **No test framework.** `backend/tests/` holds standalone scripts, not a pytest suite.

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

60 tests covering the categorization cascade, adaptive-learning guards, CSV parsing and
sign handling, and the HTTP API. Every test runs against a throwaway SQLite file — the
suite sets `DATABASE_URL` before the app is imported and asserts it is not the real
database, so `pytest` can never touch `finance.db`.

`backend/scripts/` holds two utilities that *do* write to the real database:
`reset_db.py` (drops and re-seeds it) and `seed_sample_transactions.py`. They live
outside `tests/` so pytest never collects them.

## License

MIT — see [LICENSE](LICENSE).
