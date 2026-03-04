"""Tests for the extract module."""

import pandas as pd
import pytest

from pipeline.extract import read_csv, validate_schema


@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file for testing."""
    data = {
        "id": [1, 2, 3],
        "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "amount": [100.0, 200.0, 300.0],
        "category": ["food", "transport", "utilities"],
    }
    df = pd.DataFrame(data)
    filepath = tmp_path / "test_input.csv"
    df.to_csv(filepath, index=False)
    return str(filepath)


@pytest.fixture
def sample_config():
    return {
        "input_path": "data/input.csv",
        "output_path": "data/output.csv",
        "columns": {
            "required": ["id", "date", "amount", "category"],
            "optional": ["description", "tags"],
        },
        "date_format": "%Y-%m-%d",
        "dedup_columns": ["id"],
    }


class TestReadCsv:
    def test_reads_valid_csv(self, sample_csv, sample_config):
        df = read_csv(sample_csv, sample_config)
        assert len(df) == 3
        assert list(df.columns) == ["id", "date", "amount", "category"]

    def test_raises_on_missing_file(self, sample_config):
        with pytest.raises(FileNotFoundError):
            read_csv("/nonexistent/path.csv", sample_config)


class TestValidateSchema:
    def test_valid_schema(self, sample_csv, sample_config):
        df = read_csv(sample_csv, sample_config)
        assert validate_schema(df, sample_config) is True

    def test_missing_columns(self, sample_config):
        df = pd.DataFrame({"id": [1], "date": ["2024-01-01"]})
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_schema(df, sample_config)
