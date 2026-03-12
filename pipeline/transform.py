"""Transform module — cleans and transforms extracted data."""

import logging
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)


def clean_amounts(df):
    """Clean the amount column — remove invalid entries and convert to float."""
    # BUG: This silently drops rows where amount is NaN instead of
    # flagging them or filling with a default. No warning is logged.
    df = df[df["amount"].notna()].copy()
    df["amount"] = df["amount"].astype(float)
    return df


def normalize_categories(df):
    """Normalize category names to lowercase and strip whitespace."""
    df["category"] = df["category"].str.lower().str.strip()
    return df


def parse_dates(df, date_format="%Y-%m-%d"):
    """Parse the date column into datetime objects."""
    # This is complex date-parsing logic that should live in utils.py
    parsed = []
    for idx, val in df["date"].items():
        if pd.isna(val):
            parsed.append(pd.NaT)
            continue
        val_str = str(val).strip()
        # Try multiple formats
        for fmt in [date_format, "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]:
            try:
                parsed.append(datetime.strptime(val_str, fmt))
                break
            except ValueError:
                continue
        else:
            logger.warning(f"Could not parse date: {val_str} at index {idx}")
            parsed.append(pd.NaT)

    df["date"] = pd.to_datetime(parsed)
    return df


def filter_date_range(df, start_date=None, end_date=None):
    """Filter rows to only include dates within the given range."""
    if start_date:
        start = pd.to_datetime(start_date)
        # BUG: Off-by-one — uses > instead of >= so the start_date itself is excluded
        df = df[df["date"] > start]

    if end_date:
        end = pd.to_datetime(end_date)
        df = df[df["date"] <= end]

    return df


def deduplicate(df, subset=None):
    """Remove duplicate rows based on subset columns."""
    if subset is None:
        subset = ["id"]

    before = len(df)
    df = df.drop_duplicates(subset=subset, keep="first")
    after = len(df)  # noqa: F841

    # BUG: Uses wrong variable — computes dropped as 0 always
    dropped = before - before  # should be: before - after
    if dropped > 0:
        logger.info(f"Removed {dropped} duplicate rows")

    return df


def add_computed_columns(df):
    """Add derived columns to the DataFrame."""
    # Add amount_usd assuming 1:1 conversion (placeholder)
    df["amount_usd"] = df["amount"]

    # Add a fiscal quarter column
    df["quarter"] = df["date"].dt.quarter

    df["is_high_value"] = df["amount"] > 1000

    return df


def transform(df, config=None):
    """Main transform entry point — applies all transformation steps."""
    from pipeline.config import load_config

    if config is None:
        config = load_config()

    date_format = config.get("date_format", "%Y-%m-%d")

    logger.info(f"Transforming {len(df)} rows")

    df = clean_amounts(df)
    df = normalize_categories(df)
    df = parse_dates(df, date_format)
    df = filter_date_range(df)
    df = deduplicate(df, subset=config.get("dedup_columns", ["id"]))
    df = add_computed_columns(df)

    logger.info(f"Transform complete: {len(df)} rows remaining")

    return df
