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
    """Write DataFrame as newline-delimited JSON (JSON Lines)."""
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    df.to_json(filepath, orient="records", lines=True)
    logger.info(f"Wrote {len(df)} rows to {filepath}")


def write_parquet(df, filepath):
    """Write DataFrame to a Parquet file. Requires pyarrow."""
    try:
        import pyarrow  # noqa: F401
    except ImportError:
        raise ImportError(
            "pyarrow is required for Parquet output. "
            "Install it with: pip install 'devin-etl-pipeline[parquet]'"
        )
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    df.to_parquet(filepath, index=False, engine="pyarrow")
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
    output_format = config.get("output_format", "csv").lower()

    # Adjust file extension to match the chosen format
    base, _ = os.path.splitext(output_path)
    ext_map = {"csv": ".csv", "json": ".json", "parquet": ".parquet"}
    output_path = base + ext_map.get(output_format, ".csv")

    if output_format == "json":
        write_json(df, output_path)
    elif output_format == "parquet":
        write_parquet(df, output_path)
    else:
        write_csv(df, output_path)

    summary = generate_summary(df)
    logger.info(f"Pipeline summary: {summary}")

    return summary
