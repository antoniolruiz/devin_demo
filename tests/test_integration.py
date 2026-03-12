"""Integration test — runs the full ETL pipeline end-to-end."""

import os
import shutil

import pandas as pd
import pytest

from pipeline.extract import extract
from pipeline.load import load
from pipeline.transform import transform

# Path to the committed sample data shipped with the repo.
SAMPLE_INPUT = os.path.join(os.path.dirname(__file__), "..", "data", "input.csv")


@pytest.fixture
def pipeline_config(tmp_path):
    """Build a config dict that reads from a copy of the sample data
    and writes output into the pytest tmp_path directory."""
    input_copy = tmp_path / "input.csv"
    shutil.copy(SAMPLE_INPUT, input_copy)

    return {
        "input_path": str(input_copy),
        "output_path": str(tmp_path / "output.csv"),
        "columns": {
            "required": ["id", "date", "amount", "category"],
            "optional": ["description", "tags"],
        },
        "date_format": "%Y-%m-%d",
        "dedup_columns": ["id"],
        "output_format": "csv",
    }


class TestFullPipelineRun:
    """Happy-path integration test for the extract → transform → load pipeline."""

    def test_full_pipeline_run(self, tmp_path, pipeline_config):
        # --- Extract ----------------------------------------------------------
        df_raw = extract(pipeline_config)
        assert len(df_raw) == 50, "Sample input should contain 50 rows"

        # --- Transform --------------------------------------------------------
        df = transform(df_raw, pipeline_config)

        # 3 rows have missing amounts → dropped by clean_amounts
        # 1 row has "invalid-date" → kept as NaT (parse_dates does not drop)
        # No rows removed by dedup (all ids are unique)
        assert len(df) == 47, (
            "Expected 47 rows after transform (50 minus 3 rows with missing amounts)"
        )

        # --- Load -------------------------------------------------------------
        summary = load(df, pipeline_config)

        # Output file must exist
        output_path = pipeline_config["output_path"]
        assert os.path.exists(output_path), "Output CSV was not created"

        # Re-read output to verify what was actually persisted
        df_out = pd.read_csv(output_path)
        assert len(df_out) == 47, "Output CSV row count should match transform output"

        # --- Verify summary ---------------------------------------------------
        assert summary["total_rows"] == 47
        assert summary["total_amount"] == pytest.approx(13418.47, abs=0.01)

        # --- No NaN in required columns (except date which has 1 unparseable) -
        for col in ["id", "amount", "category"]:
            assert df[col].isna().sum() == 0, f"Column '{col}' should have no NaN values"

        # --- Categories are normalized (lowercase, stripped) ------------------
        expected_categories = {
            "entertainment",
            "food",
            "healthcare",
            "housing",
            "transport",
            "utilities",
        }
        assert set(df["category"].unique()) == expected_categories
        # Verify no leading/trailing whitespace
        assert (df["category"] == df["category"].str.strip()).all()
        # Verify all lowercase
        assert (df["category"] == df["category"].str.lower()).all()

        # --- Dates are parsed correctly ---------------------------------------
        assert pd.api.types.is_datetime64_any_dtype(df["date"]), (
            "date column should be datetime64 after parsing"
        )

        # --- Computed columns exist -------------------------------------------
        assert "amount_usd" in df.columns, "amount_usd column should be added"
        assert "quarter" in df.columns, "quarter column should be added"
        assert "is_high_value" in df.columns, "is_high_value column should be added"
