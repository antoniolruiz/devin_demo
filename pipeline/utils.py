"""Utility functions for the ETL pipeline."""

import hashlib
import logging
import os


def setup_logging(level="INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def file_checksum(filepath):
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_directory(path):
    os.makedirs(path, exist_ok=True)


def flatten_dict(d, parent_key="", sep="_"):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def truncate_string(s, max_len=100):
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


def safe_divide(a, b):
    if b == 0:
        return 0.0
    return a / b
