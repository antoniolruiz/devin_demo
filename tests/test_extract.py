"""Tests for the extract module."""

import pandas as pd
import pytest

from pipeline.extract import extract, read_csv, read_multiple_csvs, validate_schema


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


class TestEmptyCsv:
    """Tests for empty CSV handling (Issue #22)."""

    def test_extract_header_only_csv(self, tmp_path, sample_config):
        """Header-only CSV should raise ValueError with descriptive message."""
        filepath = tmp_path / "header_only.csv"
        filepath.write_text("id,date,amount,category\n")
        sample_config["input_path"] = str(filepath)
        with pytest.raises(
            ValueError,
            match=r"Input file contains no data rows \(0 rows loaded from",
        ):
            extract(sample_config)

    def test_extract_completely_empty_file(self, tmp_path, sample_config):
        """Completely empty CSV should raise an error during extract."""
        filepath = tmp_path / "empty.csv"
        filepath.write_text("")
        sample_config["input_path"] = str(filepath)
        with pytest.raises(Exception):
            extract(sample_config)

    def test_read_csv_warns_on_empty(self, tmp_path, sample_config, caplog):
        """read_csv should log a warning when the file has no data rows."""
        filepath = tmp_path / "header_only.csv"
        filepath.write_text("id,date,amount,category\n")
        import logging

        with caplog.at_level(logging.WARNING):
            df = read_csv(str(filepath), sample_config)
        assert len(df) == 0
        assert "No data rows found" in caplog.text


class TestReadMultipleCsvsErrors:
    """Tests for read_multiple_csvs error handling (Issue #22)."""

    def test_all_files_missing(self, sample_config):
        """Should raise ValueError when all input files are missing."""
        with pytest.raises(
            ValueError,
            match="All input files are missing or could not be read",
        ):
            read_multiple_csvs(
                ["/nonexistent/a.csv", "/nonexistent/b.csv"], sample_config
            )

    def test_all_files_empty(self, tmp_path, sample_config):
        """Should raise ValueError when all files have headers but no rows."""
        f1 = tmp_path / "empty1.csv"
        f2 = tmp_path / "empty2.csv"
        f1.write_text("id,date,amount,category\n")
        f2.write_text("id,date,amount,category\n")
        with pytest.raises(
            ValueError,
            match="All input files are empty",
        ):
            read_multiple_csvs([str(f1), str(f2)], sample_config)
