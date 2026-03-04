# Devin ETL Pipeline

## What This Project Does

This is a **transaction data processing pipeline** — the kind of tool a finance, operations, or analytics team would use to take raw spending records (from expense reports, bank exports, POS systems, etc.) and turn them into clean, validated, analysis-ready data.

**In plain terms:** raw transaction data comes in messy — inconsistent date formats, missing amounts, duplicate entries, mixed-case categories. This pipeline reads that raw data, cleans and standardizes it, and produces a reliable output file that can feed dashboards, reports, or downstream analytics systems.

### Why It Matters

Every data-driven organization has pipelines like this. When they break or silently produce bad data, the consequences are real:

- **Finance teams** make budget decisions on incorrect totals
- **Operations teams** miss spending anomalies because duplicates weren't removed
- **Analysts** report wrong category breakdowns because "Food" and " Food " are counted separately

This pipeline is intentionally built to be realistic — including the kinds of bugs and gaps that occur in real production code — so that it can serve as a sandbox for demonstrating automated issue detection and resolution.

---

## How the Pipeline Works

The pipeline follows a standard **ETL (Extract, Transform, Load)** pattern:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   EXTRACT   │ ──→ │  TRANSFORM   │ ──→ │    LOAD     │
│  Read CSV   │     │ Clean & Fix  │     │ Write CSV   │
│  Validate   │     │ Deduplicate  │     │ Summarize   │
└─────────────┘     └──────────────┘     └─────────────┘
```

1. **Extract** (`pipeline/extract.py`) — Reads one or more CSV files, validates that required columns (`id`, `date`, `amount`, `category`) are present
2. **Transform** (`pipeline/transform.py`) — Cleans amounts, normalizes categories to lowercase, parses dates across multiple formats, removes duplicates, and adds computed columns
3. **Load** (`pipeline/load.py`) — Writes the cleaned data to an output CSV and generates a summary report (row counts, date range, totals by category)

### Sample Data

The included `data/input.csv` contains **50 realistic transaction records** spanning January–February 2024, across categories like Food, Transport, Utilities, Healthcare, Entertainment, and Housing. The data intentionally includes:

| Data Quality Issue | Example | Where It Appears |
|---|---|---|
| Missing amounts | `amount` is blank | Rows 8, 16, 37 |
| Duplicate entries | Same date, amount, and description but different `id` — not caught by default dedup config | Row 20 duplicates row 14 |
| Inconsistent date formats | `01/22/2024`, `2024/02/16` mixed with `2024-01-02` | Rows 21, 38, 46 |
| Unparseable dates | `invalid-date` instead of a real date | Row 24 |
| Inconsistent categories | `" Food "`, `TRANSPORT` instead of `food`, `transport` | Rows 17, 22, 23, 41 |
| Zero-value transactions | `amount = 0.00` | Row 25 |
| High-value outliers | `$1,200+` transactions | Rows 5, 17, 32, 45 |
| Tags for categorization | Semicolon-separated tags like `groceries;weekly` | All rows |

---

## Project Structure

```
devin-etl-pipeline/
├── pipeline/                  # Core pipeline package
│   ├── __init__.py
│   ├── cli.py                 # CLI entry point (Click-based)
│   ├── config.py              # Configuration management (YAML + defaults)
│   ├── extract.py             # Data extraction from CSV files
│   ├── transform.py           # Data cleaning and transformation
│   ├── load.py                # Output writing (CSV/JSON) and summarization
│   └── utils.py               # Shared utility functions
├── tests/                     # Test suite (partial coverage)
│   ├── test_config.py         # Config loading and validation tests
│   ├── test_extract.py        # CSV reading and schema validation tests
│   └── test_transform.py      # Transform step tests (clean, normalize, parse)
├── data/
│   ├── input.csv              # Sample transaction data (50 rows)
│   └── config.example.yaml    # Example configuration file
├── .github/workflows/
│   └── ci.yml                 # GitHub Actions CI (lint + test, Python 3.10–3.12)
├── pyproject.toml             # Project metadata and dependencies
└── README.md
```

### What's Tested (and What's Not)

| Module | Test Coverage | Notes |
|--------|--------------|-------|
| `config.py` | Covered | Config loading, validation, defaults |
| `extract.py` | Covered | CSV reading, schema validation |
| `transform.py` | Partial | Covers clean_amounts, normalize, parse_dates; missing filter_date_range, deduplicate, add_computed_columns |
| `load.py` | **Not covered** | No tests for write_csv, write_json, generate_summary |
| `utils.py` | **Not covered** | No tests for any utility functions |
| `cli.py` | **Not covered** | No integration tests for the CLI |

---

## Getting Started

### Prerequisites

- Python 3.10 or later
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/antoniolruiz/devin_demo.git
cd devin_demo

# Install the package and dev dependencies
pip install -e ".[dev]"
```

### Running the Pipeline

```bash
# Run with default settings (reads data/input.csv, writes data/output.csv)
etl-pipeline

# Specify custom input and output paths
etl-pipeline -i data/input.csv -o results/cleaned_transactions.csv

# Enable verbose logging to see each pipeline step
etl-pipeline -v

# Use a custom config file
etl-pipeline -c data/config.example.yaml
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run tests with coverage report
pytest tests/ --cov=pipeline --cov-report=term-missing
```

### Linting

```bash
ruff check pipeline/ tests/
```

---

## Configuration

The pipeline can be configured via a YAML file (see `data/config.example.yaml`). If no config file is provided, it uses sensible defaults:

| Setting | Default | Description |
|---------|---------|-------------|
| `input_path` | `data/input.csv` | Path to the input CSV file |
| `output_path` | `data/output.csv` | Path for the cleaned output CSV |
| `date_format` | `%Y-%m-%d` | Primary date format to expect |
| `dedup_columns` | `["id"]` | Columns used to identify duplicate rows |
| `batch_size` | `1000` | Rows per batch (for future streaming support) |
| `log_level` | `INFO` | Logging verbosity |

---

## Known Issues

This codebase contains intentional issues that represent common real-world data pipeline problems. See the [GitHub Issues](https://github.com/antoniolruiz/devin_demo/issues) tab for a full list, including:

- **Bugs** — Silent data loss, off-by-one errors, incorrect type comparisons
- **Missing features** — No dry-run mode, no data validation step, no summary output
- **Documentation gaps** — Missing type hints, incomplete docstrings, misleading comments
- **Refactoring opportunities** — Dead code, logic that should be extracted into utilities
- **Test gaps** — Multiple modules with zero test coverage

These issues are labeled by category (`bug`, `feature`, `docs`, `refactor`, `tests`) and complexity (`easy`, `medium`).

---

## Technology Stack

- **Python 3.10+** — Core language
- **pandas** — Data manipulation and transformation
- **Click** — CLI framework
- **PyYAML** — Configuration file parsing
- **pytest** — Testing framework
- **ruff** — Linting and code quality
- **GitHub Actions** — Continuous integration
