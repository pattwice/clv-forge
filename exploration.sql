-- Data exploration: vw_raw_customers & vw_raw_orders
-- Run: sqlite3 shopdata.db < exploration.sql

-- =============================================================================
-- CUSTOMERS
-- =============================================================================

-- 1. Duplicate customer_id — dedup needed, keep latest signup_date
SELECT
    customer_id,
    COUNT(*) AS row_count,
    GROUP_CONCAT(signup_date, ', ') AS signup_dates
FROM vw_raw_customers
GROUP BY customer_id
HAVING COUNT(*) > 1;

-- 2. Missing or blank emails
SELECT customer_id, full_name, email
FROM vw_raw_customers
WHERE email IS NULL OR TRIM(email) = '';

-- 3. Inconsistent phone formats (non-numeric characters present)
SELECT customer_id, phone
FROM vw_raw_customers
WHERE phone IS NOT NULL
  AND phone GLOB '*[^0-9]*';

-- 4. Missing phone numbers
SELECT customer_id, full_name, phone
FROM vw_raw_customers
WHERE phone IS NULL OR TRIM(phone) = '';

-- =============================================================================
-- ORDERS
-- =============================================================================

-- 5. Invalid amounts (system errors: total_amount <= 0)
SELECT order_id, customer_id, total_amount, currency, status
FROM vw_raw_orders
WHERE total_amount <= 0;

-- 6. Missing currency (assume USD per cleaning rules)
SELECT order_id, customer_id, order_date, total_amount, currency
FROM vw_raw_orders
WHERE currency IS NULL OR TRIM(currency) = '';

-- 7. Orphan orders (customer_id not in customers view)
SELECT o.order_id, o.customer_id, o.order_date, o.total_amount
FROM vw_raw_orders o
LEFT JOIN (SELECT DISTINCT customer_id FROM vw_raw_customers) c
    ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

-- 8. Non-USD orders missing exchange rate for order_date
SELECT DISTINCT
    o.order_id,
    o.currency,
    o.order_date,
    o.total_amount
FROM vw_raw_orders o
LEFT JOIN vw_exchange_rates r
    ON o.currency = r.currency
   AND o.order_date = r.date
WHERE o.currency IS NOT NULL
  AND o.currency != 'USD'
  AND r.currency IS NULL;

-- 9. Currencies in orders vs exchange rates coverage
SELECT DISTINCT o.currency AS order_currency
FROM vw_raw_orders o
WHERE o.currency IS NOT NULL
EXCEPT
SELECT DISTINCT currency FROM vw_exchange_rates;

-- 10. Missing order_date
SELECT order_id, customer_id, order_date, total_amount
FROM vw_raw_orders
WHERE order_date IS NULL OR TRIM(order_date) = '';
