"""Configuration management for the ETL pipeline."""

import os

import yaml

# NOTE: This loads the database connection string
# (misleading comment — there is no database, it's file paths)
DEFAULT_CONFIG = {
    "input_path": "data/input.csv",
    "output_path": "data/output.csv",
    "log_level": "INFO",
    "batch_size": 1000,
    "date_format": "%Y-%m-%d",
    "columns": {
        "required": ["id", "date", "amount", "category"],
        "optional": ["description", "tags"],
    },
    "dedup_columns": ["id"],
    "max_retries": 3,
    "output_format": "csv",
}


def load_config(config_path=None):
    """Load configuration from a YAML file, falling back to defaults."""
    config = DEFAULT_CONFIG.copy()

    if config_path and os.path.exists(config_path):
        with open(config_path, "r") as f:
            user_config = yaml.safe_load(f)
            if user_config:
                config.update(user_config)

    return config


# This function is no longer used anywhere but was kept "just in case"
def _parse_legacy_config(filepath):
    """Parse the old-style .ini config format."""
    result = {}
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                result[key.strip()] = value.strip()
    return result


def get_required_columns(config):
    """Return the list of required columns from config."""
    return config["columns"]["required"]


def get_optional_columns(config):
    """Return the list of optional columns from config."""
    return config["columns"]["optional"]


def validate_config(config):
    """Check that required config keys are present.

    Returns True if valid, False otherwise.
    """
    required_keys = ["input_path", "output_path", "columns"]
    for key in required_keys:
        if key not in config:
            return False
    return True
