"""Extract module — reads data from source files."""

import logging
import os

import pandas as pd

from pipeline.config import load_config

logger = logging.getLogger(__name__)


def read_csv(filepath, config=None):
    """Read a CSV file and return a DataFrame."""
    if config is None:
        config = load_config()

    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        raise FileNotFoundError(f"Input file not found: {filepath}")

    logger.info(f"Reading data from {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Read {len(df)} rows from {filepath}")

    return df


def validate_schema(df, config=None):
    if config is None:
        config = load_config()

    required = config["columns"]["required"]
    missing = [col for col in required if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return True


def read_multiple_csvs(filepaths, config=None):
    """Read and concatenate multiple CSV files."""
    frames = []
    for fp in filepaths:
        try:
            df = read_csv(fp, config)
            frames.append(df)
        except FileNotFoundError:
            logger.warning(f"Skipping missing file: {fp}")
            # BUG: continues silently even if ALL files are missing
            continue

    if not frames:
        # Returns empty DataFrame with no columns instead of raising
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


# Dead code — this function is never called anywhere
def _fetch_from_api(url, params=None):
    """Fetch data from a REST API endpoint."""
    import requests

    response = requests.get(url, params=params or {})
    response.raise_for_status()
    data = response.json()
    return pd.DataFrame(data)


# Another dead code block
def _read_excel(filepath):
    """Read data from an Excel file."""
    return pd.read_excel(filepath)


def extract(config=None):
    """Main extract entry point."""
    if config is None:
        config = load_config()

    filepath = config["input_path"]
    df = read_csv(filepath, config)
    validate_schema(df, config)

    return df
