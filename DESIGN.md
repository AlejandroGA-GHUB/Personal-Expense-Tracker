# Design notes

Why this codebase is shaped the way it is. `README.md` covers what the app does and how to
run it; this file covers the decisions, the measurements behind them, and the failures that
motivated them.

Most of the interesting numbers here come from one real 83-row Apple Card statement, which is
referred to throughout as "the test statement".

---

## Architecture

### Request path

The frontend calls `/api/*` (Vite proxies to :8000; CORS is also open to :3000). FastAPI
routers are mounted in `app/main.py` under `/api/{transactions,categories,charts,reports}`.
Routes are thin; business logic lives in `app/crud.py` and `app/utils/`. DB access goes
through the `get_db` dependency — one SQLAlchemy session per request. SQLite runs in WAL mode
with `foreign_keys=ON` (see the pragma hook in `database.py`).

### Expenses only

Positive amounts are dropped during CSV parsing, and `TransactionCreate`/`TransactionUpdate`
constrain `amount` to `lt=0`, so the manual-create and PATCH endpoints reject income with a
422. Stored amounts are always negative.

`TransactionBase`/`TransactionOut` are deliberately left *unconstrained* so that any legacy
positive row still serializes rather than blowing up a list endpoint.

### Database lifecycle

`database.init_database()` is called from the FastAPI lifespan on startup. It creates tables
and — **only if the DB is empty** — seeds the six `DEFAULT_CATEGORIES` from `models.py`.
`reset_database()` drops everything and re-seeds.

`DEFAULT_KEYWORDS` is **not** seeded into the database. It stays a constant in `models.py`,
consulted directly as the cascade's last resort. So `category_keywords` starts empty and only
ever holds real mappings the app learned.

This changed: the keywords used to be copied into the table, which forced an `is_default` flag
to distinguish hardcoded guesses from learned mappings living in the same rows. Keeping the
constant out of the database removed the flag and the ambiguity together.

---

## The categorization cascade

The core of the app, and the part that spans the most files. When a CSV row is parsed
(`utils/csv_parser.py` → `auto_categorize_transaction` in `utils/categorizer.py`), the
category is chosen most-trusted-first:

1. **Stored keyword mappings** — `_match_stored_keywords()`. `extract_keywords()` strips the
   description to meaningful tokens; matching `CategoryKeyword` rows are scored by summed
   `weight`, highest wins if ≥ 1. These come from the user's own corrections.
2. **Bank CSV category** — `utilize_bank_categorization()` maps the CSV's own label onto one
   of our categories (exact match, then substring, then a hardcoded alias table).
3. **Local LLM** (optional, off by default) — `utils/llm_categorizer.py`.
4. **Hardcoded `DEFAULT_KEYWORDS`** — `_match_hardcoded_keywords()` scores the tokens against
   the dict in `models.py` and resolves the winning *category name* to an id. Read-only:
   never written to the DB, never learned from.
5. **"Other"**.

### Why stage 4 sits below the LLM

It's a generic built-in guess and shouldn't override a model that actually read the
description. It stays in the cascade at all so an install with no Ollama still categorizes
something — a Bank of America file carries no category column, so without it every row would
import as "Other". On the test statement with the LLM off, stage 4 places 74 rows in 0.04s.

Worth knowing: **stage 4 skews toward Food & Dining.** It's the largest keyword list (75
entries) and contains generic words like `market`, `bar`, `food` and `deli`, and it's first in
dict order so it wins every tie in `max()`. This only shows up on files with no category
column of their own.

### Every stage reports itself

`auto_categorize_transaction` returns a 4-tuple ending in one of the `SOURCE_*` constants
(`learned_keywords`, `bank_category`, `llm`, `builtin_keywords`, `none`), which rides to the
preview as `categorization_source`.

The upload UI's *Auto-Category* column labels only the three that represent a real guess —
"Learned Mapping", "AI Mapping", "Educated System Mapping" — and shows plain `N/A` for
`bank_category` (the bank labelled it, and that label is already visible in the CSV Original
column) and for `none`.

Without this the column credited every row to the AI, including rows the LLM was never called
for. The gating was correct; only the display was lying.

### `_bank_labelled()` gates stage 3

A row whose CSV category is empty, `"N/A"` or `"Other"` counts as *unlabelled*, and that is
the only kind the LLM ever sees. `"Other"` deliberately does not count as a label — that's the
bank saying it didn't know either.

A row the bank *did* label but we can't map (`Tolls`, `Airlines`) skips the LLM and lands in
"Other", where the user applies the CSV's own category from the preview. This is also what
stops a single row from showing two competing Apply buttons.

---

## The local LLM stage

Opt-in, fully local, never required. `categorize_with_llm()` POSTs one JSON completion to an
Ollama-compatible endpoint using stdlib `urllib` — no HTTP dependency was added for it. The
model is given the current category list and must either pick one, propose a new one, or
answer `"Other"`.

- **Nothing is auto-created.** A proposed-but-nonexistent category comes back as
  `llm_suggested_category` on the parsed row and rides through to the preview UI, where the
  user applies it via the *same* `applied_categories` form field the bank-CSV categories
  already use. Unapplied suggestions import as "Other". This is the guard against category
  sprawl.
- **Never breaks an import.** Every failure path — disabled, no model set, server down, bad
  model name, malformed reply, timeout — returns `None` and falls through to "Other". The
  first failure writes an `UNAVAILABLE` sentinel into the per-file cache so the rest of the
  import skips the LLM instead of re-paying the timeout per merchant.
- **One call per merchant per file.** `parse_csv_with_format()` creates an `llm_cache` dict
  and threads it through every row; the key is the sorted extracted keywords, so
  `NORTHWIND #123` and `NORTHWIND #456` share a call.
- **Configured only via env** (`app/config.py`, loaded from `backend/.env`): `LLM_ENABLED`,
  `LLM_MODEL`, `LLM_BASE_URL`, `LLM_TIMEOUT_SECONDS`. **No model name is hardcoded** —
  `LLM_MODEL` defaults to empty and `llm_is_configured()` returns False unless it's set, so a
  fresh clone runs keyword-only.

**Prompt tuning is load-bearing.** The rules deliberately tell the model that a *recognizable*
merchant is never "Other". An earlier phrasing that merely said "prefer existing categories"
made it answer "Other" for obvious cases like `LA FITNESS` instead of proposing a category.

---

## Adaptive learning

Two paths write `CategoryKeyword` rows that stage 1 later reads:

1. **User corrections** — `crud.update_transaction` → `learn_from_category_change`. Keywords
   are decremented on the old category and incremented/created on the new one. Because stage 1
   outranks the LLM, one correction permanently overrides the model for that merchant.
2. **LLM decisions at import** — `crud.create_transactions_from_csv` → `learn_from_import`,
   for rows whose `categorization_source` is `llm`.

Path 2 is what makes a **second import of the same file cost zero model calls**. Measured on
the test statement: pass 1 answers 18 rows via the LLM in 25.9s; pass 2 answers the same rows
via stage 1 in 0.0s, with identical categories on all 83 rows. Only LLM rows are learned — the
other stages never call the model, so recording them would save nothing.

### Descriptions are trimmed to the merchant first

`strip_merchant_address()` in `csv_parser.py` cuts at the first token containing a digit, or
failing that the first street suffix. It starts searching from the *second* token so merchants
that lead with a number survive: `599 LEXINGTON, LLC`, `7-ELEVEN`, `24 HOUR FITNESS`.

The full description is still stored and displayed; only the keyword/LLM view is trimmed. It
runs for every bank rather than per-format, because both real formats share the numeric
boundary:

All example descriptions in this file are **fake data** - invented merchants,
reference numbers and addresses that only reproduce the shape of a real statement row.

```
NORTHWIND MKT* ZQ4KP7VX8800 1420 MAPLE AVENUE RIVERTON 55555 ZZ USA   (Apple Card)
|---- kept -----||--------------------- cut ----------------------|

GLOBEX SHOP*RB6T 02/14 PURCHASE XXXXX00000 ZZ   (Bank of America)
|--- kept ---||------------ cut ------------|
```

A token that *starts* with letters keeps that prefix rather than being dropped whole —
`AIRLINE800` → `AIRLINE` — because banks glue reference numbers onto merchant names. This is
not hypothetical: dropping it whole cost the LLM the word identifying a flight
booking, and the model answered `Entertainment` for the resulting
`TRAVELCO*BLUEJET`, where the untrimmed description had produced `Transportation`. With the
prefix kept it proposes `Travel`.

Trimming also fixed a real LLM misread:
`GLOBEX SHOP*RB6T CEDAR AVE N GLBX.COM/BILL55555 ZZ USA` used to come back as
Bills & Utilities because the model saw "BILL". Trimmed to `GLOBEX` it returns Shopping like
the other ten Globex rows. Two knock-on wins: `globex` became consistent enough to be learned
at all (that one outlier previously made `_is_learnable` reject it), and `llm_cache` keys no
longer carry location, so the same merchant in two cities is one model call.

### `_is_learnable()` — the concentration guard

Both learning paths filter tokens through it, and it is load-bearing.

A token is learned only if **every** transaction carrying it shares one category; a token seen
nowhere else is trivially kept. The rationale: a merchant token concentrates in one category,
while address and geography tokens scatter, because people buy all kinds of things on the same
street. `_keyword_category_map()` builds `token → {category ids}` in one pass over
`Transaction.extracted_keywords` — that column exists to be this corpus.

It is deliberately **not** frequency-based. Frequency collapses on small files, where 3 Globex
rows out of 5 is 60% of the file yet still exactly the mapping worth learning.

**The failure it prevents**, measured on the test statement, whose descriptions embed the full
postal address:

| Token | Rows | Distinct categories |
|-------|-----:|--------------------:|
| `usa` | 82 | 6 |
| `fairview` | 28 | 4 |
| `globex` | 11 | 1 |
| `northwind` | — | 1 |

Learning `usa` let a single correction re-file **82 of 83 rows**. Worse,
`learn_from_category_change` is not an inverse — decrementing a weight-1 keyword deletes the
row while the return trip creates one, so changing the category *back* relocated the poison
rather than undoing it. And auto-learning at import would have taken `usa` from weight 1 to
**51**, against a best real merchant token of 11.

STEP 1 of `learn_from_category_change` (the decrement) is deliberately left *unfiltered*, so
junk learned before this guard existed still gets cleaned up as the user corrects rows.

---

## CSV parsing (Strategy pattern)

`utils/csv_parser.py` supports multiple banks via `BankFormatConfig` dataclasses in the
`BANK_FORMATS` dict. To add a bank, add a config entry — no parsing-code changes needed. The
config captures header columns (used for auto-detection), column indices, date format, and
amount-sign handling.

Sign handling is the subtle part. `invert_amount_sign` (a whole-file flip) and the
`type_col`/`debit_indicators`/`credit_indicators` mechanism (for banks with all-positive
amounts plus a Debit/Credit column) are applied first, and then any `amount >= 0` row is
skipped as income.

### Upload flow

`POST /api/transactions/preview-csv` parses and auto-categorizes without persisting.
`POST /api/transactions/upload-csv` does the same but persists, and accepts an
`applied_categories` form field — a JSON list of category names the user chose to create from
the preview. `create_csv_categories()` get-or-creates those, then their IDs override the
auto-detected category for rows whose `csv_category_name` **or** `llm_suggested_category`
matches. The bank's own category wins when both are present, since it came from the data
rather than from a model's guess.

**Ordering here is load-bearing:** `create_csv_categories()` must run *after*
`parse_csv_auto_detect()`. See Known limitations below.

---

## Categories

**Uniqueness.** `Category.name` is UNIQUE. Always go through `crud.get_category_by_name()`
before inserting to avoid IntegrityError → 500s. `crud.create_category()` is a raw insert with
no dedup; the POST `/api/categories` endpoint and `create_csv_categories()` both guard with
`get_category_by_name` first.

**Deletion.** `DELETE /api/categories/{id}` → `crud.delete_category()`. Transactions in the
category are **reassigned to "Other"**, never deleted — which also has to happen before the
delete, since `foreign_keys=ON` would otherwise reject it. The category's `CategoryKeyword`
rows go with it via the relationship's `cascade="all, delete-orphan"`; that's intentional,
since those mappings only ever meant "file this merchant under the category you just removed".

**"Other" itself is undeletable** (400). It's both the reassignment target and the cascade's
last resort. Everything else is fair game, including the seeded defaults.

---

## Tests

`backend/tests/` is a pytest suite: 60 tests over the parser, the cascade and the API. Run it
from `backend/` with `pytest`.

**Nothing touches the real database.** `conftest.py` sets `DATABASE_URL` to a throwaway SQLite
file in a temp directory *before* `app.database` is imported anywhere, so the engine is bound
to that file from the moment it is created. Overriding the `get_db` dependency alone would not
be enough, since anything reaching the FastAPI lifespan on startup would still open the real
`finance.db`.

`pytest.ini` pins `testpaths = tests` for the same reason from the other direction:
`backend/scripts/` holds `reset_db.py`, which drops every table, so collecting that directory
on a bare `pytest` run would destroy the real database.

| File | Covers |
|------|--------|
| `test_csv_parser.py` (17) | `strip_merchant_address` boundaries, bank-format auto-detection, sign inversion and the income drop, and that every parsed row reports a `categorization_source` |
| `test_categorizer.py` (21) | cascade ordering stage by stage, the `_bank_labelled()` gate on stage 3, keyword extraction, `_is_learnable`, and both learning paths |
| `test_api.py` (22) | routing, category create/delete with the "Other" reassignment and keyword cascade, the `amount < 0` rejection, filtering, and the report endpoints |

The categorizer tests are where this document's claims are held honest. `TestIsLearnable`
encodes the concentration guard, including `test_is_not_frequency_based` for the small-file
case that motivated it, so the `usa` failure above cannot return unnoticed;
`test_second_pass_is_answered_by_stage_one` pins the zero-model-calls-on-reimport property
that `learn_from_import` exists to provide.

## Known limitations

- **The LLM stage runs twice per import.** `preview-csv` and `upload-csv` each parse the file
  from scratch, so an unmatched merchant is sent to the model once during preview and again
  during upload. Answers agree at temperature 0 *provided the category list is identical on
  both passes* — which is why `create_csv_categories()` must run after `parse_csv_auto_detect()`.

  Creating applied categories first put them in the list handed to the model: applying `Travel`
  and `Airlines` together made the upload pass pick the now-existing `Airlines` for a flight
  booking the preview had proposed `Travel` for, and since that's an existing category it
  carried no `llm_suggested_category` for the override to remap.

  With the ordering correct it costs time, not correctness. The intended fix is for upload to
  reuse the preview's decisions rather than re-derive them, which needs the frontend to post
  the per-row decisions back. (`learn_from_import` only helps the *second import*; it can't
  help the preview→upload pair, since preview deliberately writes nothing.)

- **`_is_learnable` measures consistency, not specificity** — and the two come apart. Before
  `strip_merchant_address` existed, `riverton` was learned at weight 10 (every Riverton row was
  an Globex row, so it looked perfectly merchant-like) while `globex` itself was *rejected* for
  spanning two categories. It then filed a Riverton restaurant under Shopping, beating the
  bank's own `Restaurants` label because stage 1 outranks stage 2. Trimming addresses removed
  the cause, but the underlying property remains: a token is only distinguishable as noise once
  it's been seen with more than one category.

- **`strip_merchant_address` can't cut a bare `MERCHANT CITY`.** With no numeric separator
  there's nothing structural distinguishing `NORTHWIND RIVERTON` from `JOES GARAGE`, so the
  city survives as a keyword. A city list would false-positive on real names (*Manhattan
  Bagel*, *Chelsea Market*), so the backstop is `_is_learnable`. Neither supported bank
  produces this shape — both always have a store id, ref, date, or street number in between —
  but a future `BankFormatConfig` might.

- **`APPLE.COM/BILL ONE APPLE PARK WAY CUPERTINO` trims imperfectly.** The cut lands on the
  street suffix `WAY`, leaving `one` and `park` to be learned (both at weight 2, →
  Bills & Utilities). Cutting earlier would need spelled-out street numbers in the suffix list,
  and `one` is too common in real merchant names (*Capital One*, *One Medical*) to blacklist.

- **A bank label the app can't map skips the LLM entirely.** `Tolls` and `Airlines` rows land
  in "Other" with no suggestion. Letting stage 3 run whenever stage 2 *fails to map* would fix
  this; it hasn't been done yet.

## Possible next steps

- Post preview decisions back on upload, removing the double LLM pass.
- Let stage 3 run when stage 2 fails to map a label.
- Extend the alias table so common CSV labels (`Grocery`, `Restaurants`) map to categories
  without the user applying them by hand.
