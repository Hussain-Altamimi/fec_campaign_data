"""Summarize processor for transaction datasets."""

from pathlib import Path

import polars as pl
from rich.console import Console

from ..config import SummarizeDataset

# Import shared utilities
# Try fec package first (new location), fall back to local for compatibility
try:
    from fec.utils.dates import extract_year_from_date
    from fec.utils.progress import create_spinner_progress
except ImportError:
    # Fallback: define locally for backward compatibility during transition
    def extract_year_from_date(date_str: str | None) -> int | None:
        """Extract year from FEC date string (MMDDYYYY, MDDYYYY, or MM/DD/YYYY format)."""
        if not date_str or not isinstance(date_str, str):
            return None
        date_str = date_str.strip()
        if not date_str:
            return None
        if "/" in date_str:
            parts = date_str.split("/")
            if len(parts) == 3 and len(parts[2]) == 4:
                try:
                    return int(parts[2])
                except ValueError:
                    return None
        if len(date_str) == 8:
            try:
                return int(date_str[4:8])
            except ValueError:
                return None
        if len(date_str) == 7:
            try:
                return int(date_str[3:7])
            except ValueError:
                return None
        return None

    from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

    def create_spinner_progress(console, transient=True):
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=transient,
        )

console = Console()


class SummarizeProcessor:
    """Processes summarize-strategy datasets (aggregation with deduplication)."""

    def __init__(self, dataset: SummarizeDataset, data_dir: Path):
        self.dataset = dataset
        self.data_dir = data_dir

    def process_cycle(self, input_file: Path, cycle: int) -> pl.DataFrame:
        """Process a single cycle's data file with filtering and aggregation.

        Args:
            input_file: Path to the pipe-delimited input file
            cycle: Election cycle year

        Returns:
            Aggregated DataFrame
        """
        console.print(f"    Processing {input_file.name}...")

        with create_spinner_progress(console) as progress:
            task = progress.add_task("Reading file...", total=None)

            # Read pipe-delimited file with lazy evaluation for memory efficiency
            df = pl.scan_csv(
                input_file,
                separator="|",
                has_header=False,
                new_columns=self.dataset.input_columns,
                infer_schema_length=10000,
                ignore_errors=True,
                encoding="utf8-lossy",
            )

            progress.update(task, description="Filtering memos and amendments...")

            # Filter out memo transactions (memo_cd = 'X')
            df = df.filter(
                (pl.col(self.dataset.memo_field).is_null())
                | (pl.col(self.dataset.memo_field) != "X")
            )

            # Filter out amendments (amndt_ind != 'N')
            df = df.filter(
                (pl.col(self.dataset.amendment_field).is_null())
                | (pl.col(self.dataset.amendment_field) == "N")
            )

            # Deduplicate by sub_id
            df = df.unique(subset=[self.dataset.sub_id_field], keep="first")

            progress.update(task, description="Extracting transaction year...")

            # Extract transaction_year from date field
            # Use map_elements for the date parsing
            df = df.with_columns(
                pl.col(self.dataset.date_field)
                .map_elements(extract_year_from_date, return_dtype=pl.Int64)
                .alias("transaction_year")
            )

            progress.update(task, description="Aggregating...")

            # Add election_cycle
            df = df.with_columns(pl.lit(cycle).alias("election_cycle"))

            # Build the columns for grouping based on column_mapping
            group_cols = []
            for out_col in self.dataset.group_by:
                if out_col in ("election_cycle", "transaction_year"):
                    group_cols.append(pl.col(out_col))
                elif out_col in self.dataset.column_mapping:
                    in_col = self.dataset.column_mapping[out_col]
                    group_cols.append(pl.col(in_col).alias(out_col))
                else:
                    group_cols.append(pl.col(out_col))

            # Select columns for grouping
            select_cols = [pl.lit(cycle).alias("election_cycle"), pl.col("transaction_year")]
            for out_col in self.dataset.group_by:
                if out_col in ("election_cycle", "transaction_year"):
                    continue
                if out_col in self.dataset.column_mapping:
                    in_col = self.dataset.column_mapping[out_col]
                    select_cols.append(pl.col(in_col).alias(out_col))
                else:
                    select_cols.append(pl.col(out_col))

            select_cols.append(pl.col(self.dataset.amount_field).alias("amount"))

            df = df.select(select_cols)

            # Group and aggregate
            result = (
                df.group_by(self.dataset.group_by)
                .agg(
                    pl.col("amount").sum().alias("total_amount"),
                    pl.len().alias("transaction_count"),
                )
                .collect()
            )

            progress.update(task, description="Done")

        console.print(f"    → {len(result):,} aggregated rows")
        return result

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

        # Sort by election_cycle, then by other group columns
        sort_cols = [col for col in self.dataset.group_by if col in df.columns]
        df = df.sort(sort_cols)

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
