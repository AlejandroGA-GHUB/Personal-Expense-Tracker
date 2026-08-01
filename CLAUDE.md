# CLAUDE.md

Guidance for Claude Code (claude.ai/code) working in this repository.

**Read `DESIGN.md` before changing the categorization cascade, the learning logic, or the CSV
parser.** It holds the rationale and the measurements behind every non-obvious decision in
those files; this file is only the operating manual.

## What this is

A privacy-first, fully-local 3-tier personal finance tracker: React (Vite) → FastAPI → SQLite.
Uploads bank/credit-card CSVs, auto-categorizes each expense, visualizes spending. No auth, no
remote server — each install owns its own `backend/finance.db`.

**Expenses only.** Positive amounts are dropped at parse time and rejected with a 422 by the
create/PATCH endpoints. Stored amounts are always negative.

## Commands

The venv lives at `backend/venv`. Run all backend commands **from `backend/`**.

```bash
cd backend
./venv/Scripts/uvicorn app.main:app --reload   # Windows venv path; calling the exe == activating it

cd frontend
npm install        # first time only
npm run dev        # :3000, proxies /api to :8000
npm run build      # -> frontend/dist; also the de-facto syntax check
```

Frontend http://localhost:3000 · API docs http://localhost:8000/api/docs · health `/api/health`.

**There is no linter, front or back.** ESLint was installed with no config file, so
`npm run lint` only ever errored; the script and its four packages were removed rather than
configured. `npm run build` is the syntax check.

**Single-server mode:** `npm run build`, then `uvicorn app.main:app` serves the built frontend
and the API together on :8000. `main.py` resolves `frontend/dist` from `__file__`, not the cwd.

Optional local-LLM categorization is configured in `backend/.env` (gitignored) — copy
`backend/.env.example` and set `LLM_ENABLED` + `LLM_MODEL`. Off by default.

## Do not do these things

- **Never run `backend/tests/test_init_flow.py` as a check.** It calls `reset_database()` →
  `drop_all()` and will destroy the user's real data. It is a reset tool, not a test. To verify
  anything, build a throwaway DB instead: a separate engine on a temp file,
  `Base.metadata.create_all`, seed `DEFAULT_CATEGORIES`, pass that session in — every
  categorizer/parser entry point takes `db` as a parameter.
- **Never put emoji in `print`/log output.** Windows' cp1252 console raises `UnicodeEncodeError`.
  Strip emoji rather than reconfiguring stdout. (Markdown files are fine.)
- **Never insert a `Category` without `crud.get_category_by_name()` first.** `Category.name` is
  UNIQUE and `crud.create_category()` does no dedup, so a raw insert becomes a 500.

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest                      # 60 tests, ~20s
```

`tests/conftest.py` sets `DATABASE_URL` to a temp file **before** importing the app, and
`pytest_configure` asserts the URL is not the real database. That is what makes the suite
safe; the old scripts were not.

Fixtures: `db` (clean DB, default categories seeded, dropped per test), `client`
(TestClient sharing that session), `categories`, `make_transaction`, `csv_row`,
`keyword_for`.

`backend/scripts/` holds `reset_db.py` and `seed_sample_transactions.py`, which write to
the real DB. They were `tests/test_*.py` files whose functions pytest would have collected
and run - `reset_db.py` drops every table. `pytest.ini` also pins `testpaths = tests`.

## Architecture

Routes are thin; logic lives in `app/crud.py` and `app/utils/`. One SQLAlchemy session per
request via the `get_db` dependency. SQLite in WAL mode with `foreign_keys=ON`.

`init_database()` runs from the FastAPI lifespan: creates tables, and **only if the DB is
empty** seeds the 6 `DEFAULT_CATEGORIES`. `DEFAULT_KEYWORDS` is deliberately *not* seeded — it
stays a constant in `models.py`, so `category_keywords` only ever holds mappings actually
learned.

### The categorization cascade

Chosen most-trusted-first in `auto_categorize_transaction` (`utils/categorizer.py`):

1. **Stored keyword mappings** — learned from the user's own corrections
2. **Bank CSV category** — the file's own label, mapped via exact/substring/alias
3. **Local LLM** — optional, off by default; only ever sees rows the bank left unlabelled
4. **Hardcoded `DEFAULT_KEYWORDS`** — generic fallback, read-only, never learned from
5. **"Other"**

Returns a 4-tuple ending in a `SOURCE_*` constant that rides to the preview UI as
`categorization_source`. Every stage must keep reporting itself — without it the UI credits
every row to the AI, including rows the LLM was never called for.

**Invariants that are load-bearing** (all explained in `DESIGN.md` — don't "simplify" them
away):

- Stage 4 sits *below* the LLM, and stays in the cascade for no-Ollama installs.
- `_is_learnable()` filters both learning paths: a token is learned only if every transaction
  carrying it shares one category. Not frequency-based. Without it, one correction re-filed 82
  of 83 rows.
- `strip_merchant_address()` trims descriptions to the merchant before keyword extraction and
  before the LLM sees them. Full description is still stored and displayed.
- `create_csv_categories()` must run **after** `parse_csv_auto_detect()` in the upload route.
- The LLM never auto-creates a category; suggestions go to the preview for the user to apply.
- Deleting a category reassigns its transactions to "Other" *before* the delete
  (`foreign_keys=ON`), and "Other" itself is undeletable.

## Repository hygiene

Public repo (portfolio project), prepared 2026-07-31.

- **No `.db`, `.env`, or `.csv` has ever been committed** — verified across all history.
  Re-check before any future publish. The root `.gitignore` blocks `*.csv` and `*.db` outright
  as a safety net, so a genuine sample CSV would need an explicit `!` override.
- **`frontend/node_modules` was committed** and is now untracked, but remains in the *history*
  — nothing has rewritten it. `git filter-repo` or a squash is the fix if it ever matters.
- **One `.gitignore`, at the root** — deliberate. There used to be three (root, `backend/`,
  `frontend/`) repeating `.env`, `.DS_Store`, `.vscode`, `.idea` and the Python block in each,
  plus packaging boilerplate that could never match. Add new rules to the root file; only
  create a nested one if a rule genuinely needs directory anchoring.
- `README.md` and `DESIGN.md` are maintained by hand. Re-check them when the cascade or the API
  surface changes.
