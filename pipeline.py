import logging
import re
import sqlite3
from pathlib import Path

import pandas as pd
from prefect import flow, task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOURCE_DB = Path(__file__).parent / "shopdata.db"
ANALYTICS_DB = Path(__file__).parent / "analytics.db"
DEFAULT_EMAIL = "unknown@domain.com"


@task(name="extract_customers")
def extract_customers(db_path: Path = SOURCE_DB) -> pd.DataFrame:
    logger.info("Extracting customers from %s", db_path)
    try:
        if not db_path.exists():
            raise FileNotFoundError(f"Source database not found: {db_path}")
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql("SELECT * FROM vw_raw_customers", conn)
        logger.info("Extracted %s customer rows", len(df))
        return df
    except Exception:
        logger.exception("Failed to extract customers")
        raise


@task(name="extract_orders")
def extract_orders(db_path: Path = SOURCE_DB) -> pd.DataFrame:
    logger.info("Extracting orders from %s", db_path)
    try:
        if not db_path.exists():
            raise FileNotFoundError(f"Source database not found: {db_path}")
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql("SELECT * FROM vw_raw_orders", conn)
        logger.info("Extracted %s order rows", len(df))
        return df
    except Exception:
        logger.exception("Failed to extract orders")
        raise


@task(name="extract_exchange_rates")
def extract_exchange_rates(db_path: Path = SOURCE_DB) -> pd.DataFrame:
    logger.info("Extracting exchange rates from %s", db_path)
    try:
        if not db_path.exists():
            raise FileNotFoundError(f"Source database not found: {db_path}")
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql("SELECT * FROM vw_exchange_rates", conn)
        logger.info("Extracted %s exchange rate rows", len(df))
        return df
    except Exception:
        logger.exception("Failed to extract exchange rates")
        raise


def standardize_phone(phone) -> str | None:
    if phone is None or (isinstance(phone, float) and pd.isna(phone)):
        return None
    digits = re.sub(r"\D", "", str(phone).strip())
    return digits or None


def standardize_email(email) -> str:
    if email is None or (isinstance(email, float) and pd.isna(email)):
        return DEFAULT_EMAIL
    value = str(email).strip()
    return value if value else DEFAULT_EMAIL


def clean_customers(customers: pd.DataFrame) -> pd.DataFrame:
    df = customers.copy()
    df["signup_date"] = pd.to_datetime(df["signup_date"])
    df = df.sort_values("signup_date", ascending=False)
    df = df.drop_duplicates(subset="customer_id", keep="first")
    df["phone"] = df["phone"].apply(standardize_phone)
    df["email"] = df["email"].apply(standardize_email)
    df["signup_date"] = df["signup_date"].dt.strftime("%Y-%m-%d")
    return df.reset_index(drop=True)


def convert_to_usd(
    total_amount: float,
    currency: str | None,
    order_date: str,
    rates: pd.DataFrame,
) -> float:
    if currency is None or (isinstance(currency, float) and pd.isna(currency)):
        return float(total_amount)
    currency = str(currency).strip().upper()
    if not currency or currency == "USD":
        return float(total_amount)

    match = rates[
        (rates["currency"] == currency) & (rates["date"] == order_date)
    ]
    if match.empty:
        return float(total_amount)

    rate = float(match.iloc[0]["rate_to_usd"])
    return round(float(total_amount) * rate, 2)


def clean_orders(orders: pd.DataFrame, rates: pd.DataFrame) -> pd.DataFrame:
    df = orders.copy()
    df = df[df["total_amount"] > 0].copy()
    df["usd_amount"] = df.apply(
        lambda row: convert_to_usd(
            row["total_amount"],
            row["currency"],
            row["order_date"],
            rates,
        ),
        axis=1,
    )
    return df.reset_index(drop=True)


@task(name="transform_customers")
def transform_customers(customers: pd.DataFrame) -> pd.DataFrame:
    logger.info("Transforming %s customer rows", len(customers))
    try:
        df = clean_customers(customers)
        logger.info("Transformed to %s customer rows", len(df))
        return df
    except Exception:
        logger.exception("Failed to transform customers")
        raise


@task(name="transform_orders")
def transform_orders(orders: pd.DataFrame, rates: pd.DataFrame) -> pd.DataFrame:
    logger.info("Transforming %s order rows", len(orders))
    try:
        df = clean_orders(orders, rates)
        logger.info("Transformed to %s order rows", len(df))
        return df
    except Exception:
        logger.exception("Failed to transform orders")
        raise


@task(name="load_customers")
def load_customers(customers: pd.DataFrame, db_path: Path = ANALYTICS_DB) -> None:
    logger.info("Loading %s rows into dim_customers at %s", len(customers), db_path)
    try:
        with sqlite3.connect(db_path) as conn:
            customers.to_sql("dim_customers", conn, if_exists="replace", index=False)
        logger.info("Loaded dim_customers successfully")
    except Exception:
        logger.exception("Failed to load dim_customers")
        raise


@task(name="load_orders")
def load_orders(orders: pd.DataFrame, db_path: Path = ANALYTICS_DB) -> None:
    logger.info("Loading %s rows into fct_orders at %s", len(orders), db_path)
    try:
        with sqlite3.connect(db_path) as conn:
            orders.to_sql("fct_orders", conn, if_exists="replace", index=False)
        logger.info("Loaded fct_orders successfully")
    except Exception:
        logger.exception("Failed to load fct_orders")
        raise


@flow(name="shopdata_etl_flow")
def shopdata_etl_flow(
    source_db: Path = SOURCE_DB,
    analytics_db: Path = ANALYTICS_DB,
) -> None:
    logger.info("Starting ETL flow: %s -> %s", source_db, analytics_db)
    rates = extract_exchange_rates(source_db)
    customers = transform_customers(extract_customers(source_db))
    orders = transform_orders(extract_orders(source_db), rates)
    load_customers(customers, analytics_db)
    load_orders(orders, analytics_db)
    logger.info("ETL flow completed successfully")


if __name__ == "__main__":
    shopdata_etl_flow()
