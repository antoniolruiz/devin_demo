# Devin ETL Pipeline

A sample Python ETL (Extract, Transform, Load) pipeline for processing transaction data. This repository serves as a sandbox for demonstrating automated issue triage and resolution.

## Project Structure

```
pipeline/
  __init__.py       # Package init
  cli.py            # CLI entry point (click)
  config.py         # Configuration management
  extract.py        # Data extraction from CSV files
  transform.py      # Data cleaning and transformation
  load.py           # Output writing (CSV, JSON)
  utils.py          # Utility functions
tests/
  test_config.py    # Config module tests
  test_extract.py   # Extract module tests
  test_transform.py # Transform module tests
data/
  input.csv         # Sample input data
```

## Setup

```bash
pip install -e ".[dev]"
```

## Usage

```bash
# Run with defaults
etl-pipeline

# Run with custom input/output
etl-pipeline -i data/input.csv -o data/output.csv

# Verbose mode
etl-pipeline -v
```

## Testing

```bash
pytest tests/ -v
pytest tests/ --cov=pipeline --cov-report=term-missing
```

## Linting

```bash
ruff check pipeline/ tests/
```
