"""Load module — writes transformed data to output destinations."""

from __future__ import annotations

import logging
import os
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def write_csv(df: pd.DataFrame, filepath: str | os.PathLike[str]) -> None:
    """Write a DataFrame to a CSV file.

    Creates parent directories if they do not already exist.

    Args:
        df: The DataFrame to write.
        filepath: Destination file path for the CSV output.
    """
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

    df.to_csv(filepath, index=False)
    logger.info(f"Wrote {len(df)} rows to {filepath}")


def write_json(df: pd.DataFrame, filepath: str | os.PathLike[str]) -> None:
    """Write a DataFrame to a JSON file using a records orientation.

    Creates parent directories if they do not already exist.

    Args:
        df: The DataFrame to write.
        filepath: Destination file path for the JSON output.
    """
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    df.to_json(filepath, orient="records", indent=2)
    logger.info(f"Wrote {len(df)} rows to {filepath}")


def generate_summary(df: pd.DataFrame) -> dict[str, Any]:
    """Generate a summary dict of the pipeline output.

    The returned dictionary contains row count, column names, date range,
    total amount, and per-category counts.  Fields that cannot be computed
    (e.g. missing columns or empty DataFrame) are set to ``None``.

    Args:
        df: The cleaned pipeline output DataFrame.

    Returns:
        A dictionary with keys ``total_rows``, ``columns``,
        ``date_range``, ``total_amount``, and ``category_counts``.
    """
    summary: dict[str, Any] = {
        "total_rows": len(df),
        "columns": list(df.columns),
        "date_range": None,
        "total_amount": None,
        "category_counts": None,
    }

    if "date" in df.columns and len(df) > 0:
        summary["date_range"] = {
            "min": str(df["date"].min()),
            "max": str(df["date"].max()),
        }

    if "amount" in df.columns and len(df) > 0:
        summary["total_amount"] = float(df["amount"].sum())

    if "category" in df.columns:
        summary["category_counts"] = df["category"].value_counts().to_dict()

    return summary


def load(
    df: pd.DataFrame, config: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Execute the load stage of the ETL pipeline.

    Writes the transformed DataFrame to a CSV file and generates a summary
    of the output data.

    Args:
        df: The transformed DataFrame to persist.
        config: Pipeline configuration dictionary.  If ``None``, the default
            configuration is loaded via :func:`pipeline.config.load_config`.

    Returns:
        A summary dictionary produced by :func:`generate_summary`.
    """
    from pipeline.config import load_config

    if config is None:
        config = load_config()  # type: ignore[no-untyped-call]

    output_path: str = config["output_path"]
    write_csv(df, output_path)

    summary = generate_summary(df)
    logger.info(f"Pipeline summary: {summary}")

    return summary
