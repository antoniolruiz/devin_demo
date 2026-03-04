"""CLI entry point for the ETL pipeline."""

import logging
import sys

import click

from pipeline.config import load_config
from pipeline.extract import extract
from pipeline.load import load
from pipeline.transform import transform
from pipeline.utils import setup_logging

logger = logging.getLogger(__name__)


@click.command()
@click.option("--config", "-c", default=None, help="Path to YAML config file")
@click.option("--input", "-i", "input_path", default=None, help="Input CSV file path")
@click.option("--output", "-o", "output_path", default=None, help="Output CSV file path")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def main(config, input_path, output_path, verbose):
    """Run the ETL pipeline."""
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)

    logger.info("Starting ETL pipeline")

    try:
        cfg = load_config(config)

        if input_path:
            cfg["input_path"] = input_path
        if output_path:
            cfg["output_path"] = output_path

        # Extract
        logger.info("Step 1: Extract")
        df = extract(cfg)

        # Transform
        logger.info("Step 2: Transform")
        df = transform(df, cfg)

        # Load
        logger.info("Step 3: Load")
        summary = load(df, cfg)

        logger.info("Pipeline completed successfully")
        click.echo(f"Pipeline complete. {summary['total_rows']} rows written.")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
