"""Tests for the transform module."""

import pandas as pd

from pipeline.transform import clean_amounts, normalize_categories, parse_dates


class TestCleanAmounts:
    def test_removes_nan_amounts(self):
        df = pd.DataFrame({"amount": [100.0, None, 300.0]})
        result = clean_amounts(df)
        assert len(result) == 2

    def test_converts_to_float(self):
        df = pd.DataFrame({"amount": ["100", "200"]})
        result = clean_amounts(df)
        assert result["amount"].dtype == float


class TestNormalizeCategories:
    def test_lowercases_categories(self):
        df = pd.DataFrame({"category": ["Food", "TRANSPORT", "Utilities"]})
        result = normalize_categories(df)
        assert list(result["category"]) == ["food", "transport", "utilities"]

    def test_strips_whitespace(self):
        df = pd.DataFrame({"category": [" food ", "transport  "]})
        result = normalize_categories(df)
        assert list(result["category"]) == ["food", "transport"]


class TestParseDates:
    def test_parses_standard_format(self):
        df = pd.DataFrame({"date": ["2024-01-01", "2024-06-15"]})
        result = parse_dates(df)
        assert pd.api.types.is_datetime64_any_dtype(result["date"])

    def test_handles_multiple_formats(self):
        df = pd.DataFrame({"date": ["2024-01-01", "01/15/2024"]})
        result = parse_dates(df)
        assert result["date"].notna().all()
