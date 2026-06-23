import pandas as pd
import pytest

from pipeline import convert_to_usd, standardize_phone


class TestStandardizePhone:
    def test_strips_non_numeric_characters(self):
        assert standardize_phone("+1 (555) 123-4567") == "15551234567"

    def test_already_clean_phone_unchanged(self):
        assert standardize_phone("15551234567") == "15551234567"

    def test_none_returns_none(self):
        assert standardize_phone(None) is None


@pytest.fixture
def sample_rates() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "currency": ["EUR", "GBP"],
            "rate_to_usd": [1.1, 1.25],
            "date": ["2023-05-01", "2023-05-01"],
        }
    )


class TestConvertToUsd:
    def test_converts_foreign_currency(self, sample_rates):
        assert convert_to_usd(200, "EUR", "2023-05-01", sample_rates) == 220.0

    def test_missing_currency_treated_as_usd(self, sample_rates):
        assert convert_to_usd(100, None, "2023-05-01", sample_rates) == 100.0

    def test_missing_rate_treated_as_usd(self, sample_rates):
        assert convert_to_usd(100, "EUR", "2023-05-99", sample_rates) == 100.0
