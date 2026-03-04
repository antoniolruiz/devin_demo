"""Load module — writes transformed data to output destinations."""

import logging
import os

logger = logging.getLogger(__name__)


def write_csv(df, filepath):
    """Write DataFrame to a CSV file."""
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

    df.to_csv(filepath, index=False)
    logger.info(f"Wrote {len(df)} rows to {filepath}")


def write_json(df, filepath):
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    df.to_json(filepath, orient="records", indent=2)
    logger.info(f"Wrote {len(df)} rows to {filepath}")


def generate_summary(df):
    """Generate a summary dict of the pipeline output."""
    summary = {
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


def load(df, config=None):
    from pipeline.config import load_config

    if config is None:
        config = load_config()

    output_path = config["output_path"]
    write_csv(df, output_path)

    summary = generate_summary(df)
    logger.info(f"Pipeline summary: {summary}")

    return summary
