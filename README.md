# clv-forge

ETL pipeline for ShopData Inc. - clean raw SQLite data into analytics.db for Customer Lifetime Value reporting.

## Setup

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Place shopdata.db in the project root (provided separately).

## Run the pipeline

```powershell
python pipeline.py
```

Creates analytics.db with dim_customers and fct_orders.

## Run tests

```powershell
pytest -v
```

## SQL scripts

Exploration (raw data):

```powershell
python run_exploration.py
```

CLV report (requires analytics.db from pipeline):

```powershell
sqlite3 analytics.db < clv_report.sql
```

## Data Exploration Findings

1. **Duplicate customers** - customer_id 1 and 2 each appear twice with different signup_date and contact details. Requires deduplication keeping the latest signup.

2. **Invalid order amounts** - 3 orders have total_amount <= 0 (orders 103, 113, 114).

3. **Inconsistent phone formats** - 8 rows contain non-numeric characters. Requires stripping to digits only.

4. **Missing / incomplete fields** - 2 null emails, 2 null phones, 2 null currencies, and 1 null order_date (order 117).

5. **Exchange rate gaps** - 6 non-USD orders have no matching rate for their order_date; 2 orders reference customer_id 99 which does not exist in customers.