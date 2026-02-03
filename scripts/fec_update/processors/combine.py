"""Combine processor for summary datasets."""

from pathlib import Path

import polars as pl
from rich.console import Console

from ..config import CombineDataset

console = Console()


class CombineProcessor:
    """Processes combine-strategy datasets (simple concatenation)."""

    def __init__(self, dataset: CombineDataset, data_dir: Path):
        self.dataset = dataset
        self.data_dir = data_dir

    def process_cycle(self, input_file: Path, cycle: int) -> pl.DataFrame:
        """Process a single cycle's data file.

        Args:
            input_file: Path to the pipe-delimited input file
            cycle: Election cycle year

        Returns:
            DataFrame with election_cycle column prepended
        """
        console.print(f"    Processing {input_file.name}...")

        # Read pipe-delimited file
        df = pl.read_csv(
            input_file,
            separator="|",
            has_header=False,
            new_columns=self.dataset.columns,
            infer_schema_length=10000,
            ignore_errors=True,
            encoding="utf8-lossy",
        )

        # Prepend election_cycle column
        df = df.with_columns(pl.lit(cycle).alias("election_cycle"))

        # Reorder to put election_cycle first
        columns = ["election_cycle"] + self.dataset.columns
        df = df.select(columns)

        console.print(f"    → {len(df):,} rows")
        return df

    def get_output_path(self) -> Path:
        """Get the output file path."""
        return self.data_dir / self.dataset.output_file

    def read_existing(self) -> pl.DataFrame | None:
        """Read existing output file if it exists."""
        output_path = self.get_output_path()
        if not output_path.exists():
            return None

        return pl.read_csv(output_path)

    def remove_cycle(self, df: pl.DataFrame, cycle: int) -> pl.DataFrame:
        """Remove all rows for a given cycle."""
        return df.filter(pl.col("election_cycle") != cycle)

    def append_cycle(self, existing: pl.DataFrame | None, new_data: pl.DataFrame) -> pl.DataFrame:
        """Append new cycle data to existing data."""
        if existing is None:
            return new_data

        return pl.concat([existing, new_data])

    def write_output(self, df: pl.DataFrame, backup: bool = True) -> None:
        """Write output file with optional backup."""
        output_path = self.get_output_path()

        if backup and output_path.exists():
            backup_path = output_path.with_suffix(".csv.bak")
            output_path.rename(backup_path)

        # Sort by election_cycle for consistent output
        df = df.sort("election_cycle")

        # Write atomically (to temp file then rename)
        temp_path = output_path.with_suffix(".csv.tmp")
        df.write_csv(temp_path)
        temp_path.rename(output_path)

        console.print(f"    Wrote {output_path.name}: {len(df):,} rows")

    def update_cycle(self, input_file: Path, cycle: int, dry_run: bool = False) -> int:
        """Update a single cycle in the output file.

        Args:
            input_file: Path to the downloaded input file
            cycle: Election cycle year
            dry_run: If True, don't write changes

        Returns:
            Number of rows in the new cycle
        """
        # Process new data
        new_data = self.process_cycle(input_file, cycle)

        if dry_run:
            console.print(f"    [dim]Would update {cycle}: {len(new_data):,} rows[/dim]")
            return len(new_data)

        # Read existing data
        existing = self.read_existing()

        # Remove old cycle data if present
        if existing is not None:
            old_count = len(existing.filter(pl.col("election_cycle") == cycle))
            if old_count > 0:
                console.print(f"    Removing {old_count:,} existing rows for cycle {cycle}")
            existing = self.remove_cycle(existing, cycle)

        # Append new data
        result = self.append_cycle(existing, new_data)

        # Write output
        self.write_output(result)

        return len(new_data)
