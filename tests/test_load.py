"""Tests for the load module."""

import json
import os
from unittest.mock import patch

import pandas as pd
import pytest

from pipeline.load import generate_summary, load, write_csv, write_json, write_parquet


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "amount": [100.0, 200.0, 300.0],
            "category": ["food", "transport", "utilities"],
        }
    )


@pytest.fixture
def base_config(tmp_path):
    """Return a config dict pointing at a tmp output path."""
    return {
        "input_path": "data/input.csv",
        "output_path": str(tmp_path / "output.csv"),
        "columns": {
            "required": ["id", "date", "amount", "category"],
            "optional": ["description", "tags"],
        },
        "date_format": "%Y-%m-%d",
        "dedup_columns": ["id"],
        "output_format": "csv",
    }


class TestWriteCsv:
    def test_writes_csv_file(self, sample_df, tmp_path):
        filepath = str(tmp_path / "out.csv")
        write_csv(sample_df, filepath)
        assert os.path.exists(filepath)
        result = pd.read_csv(filepath)
        assert len(result) == 3

    def test_creates_directories(self, sample_df, tmp_path):
        filepath = str(tmp_path / "subdir" / "out.csv")
        write_csv(sample_df, filepath)
        assert os.path.exists(filepath)


class TestWriteJson:
    def test_writes_json_lines(self, sample_df, tmp_path):
        filepath = str(tmp_path / "out.json")
        write_json(sample_df, filepath)
        assert os.path.exists(filepath)
        with open(filepath) as f:
            lines = f.read().strip().split("\n")
        assert len(lines) == 3
        # Each line should be valid JSON
        for line in lines:
            record = json.loads(line)
            assert "id" in record
            assert "amount" in record


class TestWriteParquet:
    def test_writes_parquet_file(self, sample_df, tmp_path):
        pytest.importorskip("pyarrow")
        filepath = str(tmp_path / "out.parquet")
        write_parquet(sample_df, filepath)
        assert os.path.exists(filepath)
        result = pd.read_parquet(filepath)
        assert len(result) == 3

    def test_raises_without_pyarrow(self, sample_df, tmp_path):
        filepath = str(tmp_path / "out.parquet")
        with patch.dict("sys.modules", {"pyarrow": None}):
            with pytest.raises(ImportError, match="pyarrow is required"):
                write_parquet(sample_df, filepath)


class TestGenerateSummary:
    def test_summary_keys(self, sample_df):
        summary = generate_summary(sample_df)
        assert summary["total_rows"] == 3
        assert "date_range" in summary
        assert "total_amount" in summary
        assert "category_counts" in summary

    def test_total_amount(self, sample_df):
        summary = generate_summary(sample_df)
        assert summary["total_amount"] == 600.0


class TestLoad:
    def test_default_csv_output(self, sample_df, base_config):
        summary = load(sample_df, base_config)
        output_path = base_config["output_path"]
        assert os.path.exists(output_path)
        assert summary["total_rows"] == 3

    def test_json_output(self, sample_df, base_config):
        base_config["output_format"] = "json"
        summary = load(sample_df, base_config)
        json_path = base_config["output_path"].replace(".csv", ".json")
        assert os.path.exists(json_path)
        assert summary["total_rows"] == 3
        with open(json_path) as f:
            lines = f.read().strip().split("\n")
        assert len(lines) == 3

    def test_parquet_output(self, sample_df, base_config):
        pytest.importorskip("pyarrow")
        base_config["output_format"] = "parquet"
        summary = load(sample_df, base_config)
        parquet_path = base_config["output_path"].replace(".csv", ".parquet")
        assert os.path.exists(parquet_path)
        assert summary["total_rows"] == 3

    def test_csv_is_default_when_format_missing(self, sample_df, base_config):
        del base_config["output_format"]
        summary = load(sample_df, base_config)
        assert os.path.exists(base_config["output_path"])
        assert summary["total_rows"] == 3
