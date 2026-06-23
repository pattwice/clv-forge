# Data Engineer Technical Assignment — Implementation Plan

Step-by-step approach from scratch to submission. Each phase ends with a verifiable checkpoint before moving on.

**Status: Phases 0–6 complete. Phase 7 — push done, email submission pending.**

---

## Phase 0: Project Setup — COMPLETE

**Goal:** A runnable Python project with version control from day one.


| Step | Action                              | Status                                    |
| ---- | ----------------------------------- | ----------------------------------------- |
| 0.1  | Initialize git repo (`main` branch) | Done                                      |
| 0.2  | Create project structure            | Done (`tests/` exists)                    |
| 0.3  | Add `requirements.txt`              | Done (`prefect>=3`, `pandas`, `pytest`)   |
| 0.4  | Place `shopdata.db` in project root | Done                                      |
| 0.5  | Add `.gitignore`                    | Done (venv, cache, analytics.db, .cursor) |
| 0.6  | Initial commit                      | Done                                      |


**Current structure:**

```
.
├── shopdata.db
├── analytics.db             # generated, gitignored
├── exploration.sql
├── clv_report.sql
├── pipeline.py
├── run_exploration.py       # extra helper
├── pytest.ini               # extra config
├── tests/
│   └── test_pipeline.py
├── requirements.txt
├── README.md
└── plan.md
```

---

## Phase 1: Data Exploration — COMPLETE


| Step | Action                                 | Status |
| ---- | -------------------------------------- | ------ |
| 1.1  | Inspect schemas                        | Done   |
| 1.2  | Write `exploration.sql` (10 queries)   | Done   |
| 1.3  | Document findings in README (5 issues) | Done   |


**Commit:** `feat(sql): add order_date check and exploration runner`, `docs: fix readme encoding and exploration findings`

---

## Phase 2: Design Transformations — COMPLETE


| Step | Action                                    | Status |
| ---- | ----------------------------------------- | ------ |
| 2.1  | Transformation functions in `pipeline.py` | Done   |
| 2.2  | Customer rules (dedup, phone, email)      | Done   |
| 2.3  | Order rules (filter, USD conversion)      | Done   |


**Customer cleaning rules:**


| Rule        | Logic                                                   |
| ----------- | ------------------------------------------------------- |
| Deduplicate | Group by `customer_id`; keep row with max `signup_date` |
| Phone       | Strip all non-digits                                    |
| Email       | Null/empty → `unknown@domain.com`                       |


**Order cleaning rules:**


| Rule           | Logic                                                                                                                          |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Filter         | Drop rows where `total_amount <= 0`                                                                                            |
| USD conversion | Join rates on `order_date` + `currency`; `usd_amount = total_amount * rate_to_usd`; missing currency or no rate → treat as USD |


**Commit:** `feat(etl): add customer and order transform functions`

---

## Phase 3: Prefect ETL Pipeline — COMPLETE


| Step | Action                                                          | Status |
| ---- | --------------------------------------------------------------- | ------ |
| 3.1  | `extract_customers`, `extract_orders`, `extract_exchange_rates` | Done   |
| 3.2  | `transform_customers`, `transform_orders`                       | Done   |
| 3.3  | `load_customers`, `load_orders` → `analytics.db`                | Done   |
| 3.4  | `shopdata_etl_flow` + `python pipeline.py`                      | Done   |
| 3.5  | Logging and error handling in tasks                             | Done   |


**Output:** `dim_customers` (10 rows), `fct_orders` (17 rows)

**Commit:** `feat(etl): add prefect flow to orchestrate pipeline`

---

## Phase 4: Unit Tests — COMPLETE


| Step | Action                              | Status   |
| ---- | ----------------------------------- | -------- |
| 4.1  | `tests/test_pipeline.py`            | Done     |
| 4.2  | Phone standardizer tests (3 cases)  | Done     |
| 4.3  | Currency conversion tests (3 cases) | Done     |
| 4.4  | `pytest -v`                         | 6 passed |


**Commit:** `test(etl): add unit tests for phone and currency conversion`

---

## Phase 5: CLV Analytical Query — COMPLETE


| Step | Action                            | Status         |
| ---- | --------------------------------- | -------------- |
| 5.1  | Pipeline populates `analytics.db` | Done           |
| 5.2  | `clv_report.sql`                  | Done (10 rows) |


**Commit:** `feat(sql): add customer lifetime value report query`

---

## Phase 6: README & Final Polish — COMPLETE


| Step | Action               | Status |
| ---- | -------------------- | ------ |
| 6.1  | Setup instructions   | Done   |
| 6.2  | Run pipeline         | Done   |
| 6.3  | Run tests            | Done   |
| 6.4  | Exploration findings | Done   |
| 6.5  | Run SQL scripts      | Done   |
| 6.6  | Deliverables review  | Done   |


**Commit:** `docs: add pipeline, test, and sql run instructions`

---

## Phase 7: Git Hygiene & Submission


| Step | Action                                                                   | Status                      |
| ---- | ------------------------------------------------------------------------ | --------------------------- |
| 7.1  | Descriptive commit messages                                              | Done (conventional commits) |
| 7.2  | One logical task per commit                                              | Done (10 commits)           |
| 7.3  | Push to remote                                                           | Done                        |
| 7.4  | Email repo link to [contact@storemesh.com](mailto:contact@storemesh.com) | Done                        |


---

## Deliverables Checklist


| #   | File                     | Status |
| --- | ------------------------ | ------ |
| 1   | `pipeline.py`            | Done   |
| 2   | `tests/test_pipeline.py` | Done   |
| 3   | `exploration.sql`        | Done   |
| 4   | `clv_report.sql`         | Done   |
| 5   | `requirements.txt`       | Done   |
| 6   | `README.md`              | Done   |


---

## Decisions Made


| Topic                   | Decision                                  |
| ----------------------- | ----------------------------------------- |
| Exchange rate           | `usd_amount = total_amount * rate_to_usd` |
| Dedup key               | `customer_id`, keep latest `signup_date`  |
| Empty phone after strip | Returns `None`                            |
| `shopdata.db`           | Committed in repo for reproducibility     |


---

## Final Verification (rechecked)


| Check                              | Result                           |
| ---------------------------------- | -------------------------------- |
| `pytest -q`                        | 6 passed                         |
| `python pipeline.py`               | Flow completed                   |
| `python run_exploration.py`        | Runs (10 queries)                |
| `clv_report.sql` on `analytics.db` | 10 rows                          |
| `README.md` encoding               | UTF-8                            |
| Git working tree                   | Clean, synced with `origin/main` |


