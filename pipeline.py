import re

import pandas as pd

DEFAULT_EMAIL = "unknown@domain.com"


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
