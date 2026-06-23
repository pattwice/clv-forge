# Data Engineer Technical Assignment — Implementation Plan

Step-by-step approach from scratch to submission. Each phase ends with a verifiable checkpoint before moving on.

---

## Phase 0: Project Setup

**Goal:** A runnable Python project with version control from day one.

| Step | Action | Checkpoint |
|------|--------|------------|
| 0.1 | Initialize git repo (`main` branch) | `git status` works |
| 0.2 | Create project structure (see below) | Folders exist |
| 0.3 | Add `requirements.txt`: `prefect>=3`, `pandas`, `pytest` | `pip install -r requirements.txt` succeeds |
| 0.4 | Place `shopdata.db` in project root (provided by employer) | Can open DB with any SQLite client |
| 0.5 | Add `.gitignore` (venv, `__pycache__`, `.pytest_cache`, `analytics.db`) | Secrets/artifacts not committed |
| 0.6 | Initial commit: scaffold only | Clean commit history starts |

**Target structure:**

```
.
├── shopdata.db              # source (read-only)
├── analytics.db             # output (generated, gitignored)
├── exploration.sql
├── clv_report.sql
├── pipeline.py
├── tests/
│   └── test_pipeline.py
├── requirements.txt
├── README.md
└── plan.md
```

---

## Phase 1: Data Exploration (Part 1)

**Goal:** Understand raw data quality before writing Python. No pipeline code yet.

| Step | Action | Checkpoint |
|------|--------|------------|
| 1.1 | Connect to `shopdata.db` and inspect schemas for `vw_raw_customers`, `vw_raw_orders`, `vw_exchange_rates` | Know column names and types |
| 1.2 | Write `exploration.sql` with focused anomaly queries | Script runs end-to-end |
| 1.3 | Document findings in README (≥ 3 distinct issues) | Issues are specific, with examples |

**Queries to include in `exploration.sql`:**

1. **Customers — duplicates:** Same `customer_id` (or natural key) with multiple rows; compare `signup_date` to confirm “most recent wins” rule matters.
2. **Customers — nulls / blanks:** Missing `email`, `phone`, `full_name`, or other key fields.
3. **Customers — phone format:** Non-numeric characters, inconsistent lengths, invalid patterns.
4. **Orders — invalid amounts:** `total_amount <= 0` (system errors to filter).
5. **Orders — nulls / orphans:** Missing `customer_id`, `order_date`, `currency`, or amounts.
6. **Orders — currency gaps:** Distinct currencies in orders vs. currencies in `vw_exchange_rates`; orders with dates missing from rates table.
7. **Referential integrity:** Orders referencing customer IDs not in customers view.

**README exploration section (draft outline):**

- Issue 1: … (query used, count, example)
- Issue 2: …
- Issue 3: …

**Commit:** `Add exploration.sql and document data quality findings`

---

## Phase 2: Design Transformations (before Prefect)

**Goal:** Pure, testable functions — no DB coupling in business logic.

| Step | Action | Checkpoint |
|------|--------|------------|
| 2.1 | Define transformation functions in `pipeline.py` (or a `transforms.py` module) | Functions accept DataFrames/values, return cleaned data |
| 2.2 | Implement **customer** rules | See rules below |
| 2.3 | Implement **order** rules | See rules below |

**Customer cleaning rules:**

| Rule | Logic |
|------|--------|
| Deduplicate | Group by `customer_id`; keep row with max `signup_date` |
| Phone | Strip all non-digits → e.g. `+1 (555) 123-4567` → `15551234567` |
| Email | Null/empty → `unknown@domain.com` |

**Order cleaning rules:**

| Rule | Logic |
|------|--------|
| Filter | Drop rows where `total_amount <= 0` |
| USD conversion | Join `vw_exchange_rates` on `order_date` + `currency`; `usd_amount = total_amount / rate` (confirm rate direction from data); missing currency or no rate → treat as USD (`usd_amount = total_amount`) |

**Commit:** `Add transformation functions for customers and orders`

---

## Phase 3: Prefect ETL Pipeline (Part 2)

**Goal:** Orchestrated flow: extract → transform → load with logging and error handling.

| Step | Action | Checkpoint |
|------|--------|------------|
| 3.1 | `@task extract_*` — read each view from `shopdata.db` into DataFrames | Tasks log row counts |
| 3.2 | `@task transform_customers` / `transform_orders` — call Phase 2 functions | Clean DataFrames returned |
| 3.3 | `@task load_*` — write `dim_customers` and `fct_orders` to `analytics.db` | Tables exist with expected columns |
| 3.4 | `@flow shopdata_etl_flow` — wire tasks in order | `python pipeline.py` runs successfully |
| 3.5 | Add try/except + `logging` in tasks; fail loudly on missing source DB | Errors are readable in logs |

**Load schema (minimum):**

- `dim_customers`: cleaned customer columns (include standardized `phone`, filled `email`, deduplicated rows).
- `fct_orders`: order columns + `usd_amount`; only valid orders (`total_amount > 0`).

**Fallback:** If SQLite load fails, write `clean_customers.csv` and `clean_orders.csv` instead.

**Commit:** `Add Prefect ETL flow with extract, transform, and load tasks`

---

## Phase 4: Unit Tests (Part 3)

**Goal:** Test business logic in isolation — no live database.

| Step | Action | Checkpoint |
|------|--------|------------|
| 4.1 | Create `tests/test_pipeline.py` | pytest discovers tests |
| 4.2 | Test **phone standardizer** — input strings → expected digit-only output | ≥ 2 cases (formatted phone, already clean) |
| 4.3 | Test **currency conversion** — dummy rates DataFrame + orders → expected `usd_amount` | Cases: known currency, missing currency, missing rate |
| 4.4 | Optional: dedup test (two rows same ID, different `signup_date`) | Keeps latest signup |
| 4.5 | Run `pytest -v` | All tests pass |

**Commit:** `Add unit tests for phone standardization and currency conversion`

---

## Phase 5: CLV Analytical Query (Part 4)

**Goal:** Single SQL query over cleaned tables in `analytics.db`.

| Step | Action | Checkpoint |
|------|--------|------------|
| 5.1 | Run pipeline so `analytics.db` is populated | Tables have data |
| 5.2 | Write `clv_report.sql` with one query | Query runs without errors |

**Required output columns:**

| Column | Definition |
|--------|------------|
| `customer_id` | From `dim_customers` |
| `full_name` | From `dim_customers` |
| `total_orders_placed` | Count of orders per customer in `fct_orders` |
| `lifetime_value_usd` | `SUM(usd_amount)` per customer |
| `customer_cohort` | Month/year of signup, e.g. `'2023-01'` (`strftime('%Y-%m', signup_date)`) |

**Order:** `ORDER BY lifetime_value_usd DESC`

**Commit:** `Add CLV report SQL query`

---

## Phase 6: README & Final Polish

**Goal:** Reviewer can clone, install, run, and test without guessing.

| Step | Action | Checkpoint |
|------|--------|------------|
| 6.1 | README: project overview, prerequisites, setup | Copy-paste commands work |
| 6.2 | README: how to run pipeline (`python pipeline.py` or `prefect` CLI) | Verified on fresh venv |
| 6.3 | README: how to run tests (`pytest`) | Documented |
| 6.4 | README: data exploration summary (≥ 3 issues from Phase 1) | Complete |
| 6.5 | README: how to run SQL files against `analytics.db` | Example `sqlite3` command |
| 6.6 | Final review against deliverables checklist | All files present |

**Commit:** `Complete README with setup, run instructions, and findings`

---

## Phase 7: Git Hygiene & Submission

**Goal:** Demonstrate iterative, professional git practices (evaluation criterion).

| Step | Action |
|------|--------|
| 7.1 | Use descriptive commit messages (imperative mood: "Add …", "Fix …") |
| 7.2 | One logical change per commit — avoid single mega-commit at the end |
| 7.3 | Optional: feature branch (`feature/etl-pipeline`) merged via PR for cleaner history |
| 7.4 | Push to GitHub/GitLab/Bitbucket |
| 7.5 | Email repo link to contact@storemesh.com within 3 days |

**Suggested commit sequence:**

1. Project scaffold + requirements
2. exploration.sql + README findings
3. Transformation functions
4. Prefect pipeline
5. Unit tests
6. clv_report.sql
7. README polish

---

## Deliverables Checklist

| # | File | Status |
|---|------|--------|
| 1 | `pipeline.py` | ☐ |
| 2 | `tests/test_pipeline.py` | ☐ |
| 3 | `exploration.sql` | ☐ |
| 4 | `clv_report.sql` | ☐ |
| 5 | `requirements.txt` | ☐ |
| 6 | `README.md` | ☐ |

---

## Execution Order (Summary)

```
Phase 0  Setup & git
   ↓
Phase 1  exploration.sql → README findings
   ↓
Phase 2  Transform functions (testable, no Prefect yet)
   ↓
Phase 3  Prefect flow (extract → transform → load)
   ↓
Phase 4  pytest (phone + currency conversion)
   ↓
Phase 5  clv_report.sql
   ↓
Phase 6  README polish
   ↓
Phase 7  Push & submit
```

---

## Risks & Decisions to Confirm Early

| Topic | Action when implementing |
|-------|--------------------------|
| Exchange rate direction | Inspect `vw_exchange_rates` sample rows in Phase 1; document assumption in README |
| `customer_id` dedup key | Confirm primary key column name from schema |
| Date formats | Check `order_date` / `signup_date` types; parse consistently in pandas |
| Empty phone after strip | Decide: keep empty string or NULL (document in README) |
| `shopdata.db` not in repo | Note in README that user must obtain file separately |

---

## Next Step

Start **Phase 0**: initialize the repo, create the folder structure, and confirm `shopdata.db` is available locally.
