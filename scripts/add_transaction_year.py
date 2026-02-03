#!/usr/bin/env python3
"""Add transaction_year column to individual contribution CSV files.

Extracts the year from transaction_dt (MMDDYYYY format) and inserts it
as the second column (after election_cycle). Overwrites files in place.
"""

import argparse
import sys
from pathlib import Path

import polars as pl
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

console = Console()

INDIVIDUAL_CONTRIBUTIONS_DIR = Path(__file__).parent.parent / "individual_contributions"


def extract_year_from_date(date_str: str | None) -> int | None:
    """Extract year from FEC date string (MMDDYYYY, MDDYYYY, or MM/DD/YYYY format)."""
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()
    if not date_str:
        return None

    # Handle MM/DD/YYYY format
    if "/" in date_str:
        parts = date_str.split("/")
        if len(parts) == 3 and len(parts[2]) == 4:
            try:
                return int(parts[2])
            except ValueError:
                return None

    # Handle MMDDYYYY format (8 chars) - year is last 4
    if len(date_str) == 8:
        try:
            return int(date_str[4:8])
        except ValueError:
            return None

    # Handle MDDYYYY format (7 chars) - year is last 4
    if len(date_str) == 7:
        try:
            return int(date_str[3:7])
        except ValueError:
            return None

    return None


def add_transaction_year(input_file: Path, dry_run: bool = False, force: bool = False) -> int:
    """Add transaction_year column to a CSV file.

    Args:
        input_file: Path to the individual contributions CSV
        dry_run: If True, don't write changes
        force: If True, recompute even if column exists

    Returns:
        Number of rows processed
    """
    console.print(f"Processing {input_file.name}...")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Reading file...", total=None)

        # Read the CSV
        df = pl.read_csv(
            input_file,
            infer_schema_length=10000,
            ignore_errors=True,
            encoding="utf8-lossy",
        )

        # Check if transaction_year already exists
        if "transaction_year" in df.columns and not force:
            console.print(f"  [yellow]Skipping: transaction_year column already exists (use --force to recompute)[/yellow]")
            return len(df)

        # Drop existing column if force recompute
        if "transaction_year" in df.columns:
            df = df.drop("transaction_year")

        progress.update(task, description="Extracting transaction year...")

        # Extract year from transaction_dt
        df = df.with_columns(
            pl.col("transaction_dt")
            .cast(pl.Utf8)
            .map_elements(extract_year_from_date, return_dtype=pl.Int64)
            .alias("transaction_year")
        )

        # Reorder columns: election_cycle, transaction_year, then the rest
        cols = df.columns
        cols.remove("transaction_year")
        new_order = [cols[0], "transaction_year"] + cols[1:]
        df = df.select(new_order)

        row_count = len(df)

        if dry_run:
            console.print(f"  [dim]Would write {row_count:,} rows[/dim]")
            # Show sample
            console.print(f"  Sample columns: {df.columns[:5]}")
            return row_count

        progress.update(task, description="Writing file...")

        # Write atomically (to temp file then rename)
        temp_path = input_file.with_suffix(".csv.tmp")
        df.write_csv(temp_path)
        temp_path.rename(input_file)

        progress.update(task, description="Done")

    console.print(f"  → {row_count:,} rows written")
    return row_count


def main():
    parser = argparse.ArgumentParser(
        description="Add transaction_year column to individual contribution files"
    )
    parser.add_argument(
        "--cycle",
        type=int,
        help="Process only this election cycle (e.g., 2020)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recompute transaction_year even if column already exists",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=INDIVIDUAL_CONTRIBUTIONS_DIR,
        help="Directory containing individual contribution files",
    )
    args = parser.parse_args()

    if not args.dir.exists():
        console.print(f"[red]Error: Directory not found: {args.dir}[/red]")
        sys.exit(1)

    # Find files to process
    if args.cycle:
        files = [args.dir / f"{args.cycle}_individual_contributions.csv"]
        if not files[0].exists():
            console.print(f"[red]Error: File not found: {files[0]}[/red]")
            sys.exit(1)
    else:
        files = sorted(args.dir.glob("*_individual_contributions.csv"))

    if not files:
        console.print("[yellow]No individual contribution files found[/yellow]")
        sys.exit(0)

    console.print(f"Found {len(files)} file(s) to process\n")

    total_rows = 0
    for file_path in files:
        try:
            rows = add_transaction_year(file_path, dry_run=args.dry_run, force=args.force)
            total_rows += rows
        except Exception as e:
            console.print(f"[red]Error processing {file_path.name}: {e}[/red]")
            raise

    console.print(f"\n[green]Done![/green] Processed {total_rows:,} total rows")


if __name__ == "__main__":
    main()
