"""Date conversion CLI commands."""

from pathlib import Path

import click
import polars as pl
from rich.console import Console

from ..utils.dates import convert_to_iso_date
from ..utils.io import atomic_write_csv, read_fec_csv

console = Console()

# Mapping of data files to their date columns
DATA_FILE_DATE_COLUMNS = {
    "all_candidate_summaries_1980-2026.csv": ["cvg_end_dt"],
    "house_senate_campaign_summaries_1996-2026.csv": ["cvg_end_dt"],
    "pac_party_summaries_1996-2026.csv": ["cvg_end_dt"],
}


@click.group()
def dates() -> None:
    """Date conversion commands."""
    pass


@dates.command()
@click.option(
    "--file",
    type=str,
    help="Process only this specific file (filename only, not path)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--data-dir",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to data directory",
)
@click.pass_context
def migrate(
    ctx: click.Context,
    file: str | None,
    dry_run: bool,
    data_dir: Path | None,
) -> None:
    """Convert dates from MM/DD/YYYY to ISO 8601 (YYYY-MM-DD) format.

    This is a one-time migration command. Future updates will automatically
    apply date conversion during processing.

    Examples:

        # Preview changes (dry run)
        python -m fec dates migrate --dry-run

        # Migrate all data files with date columns
        python -m fec dates migrate

        # Migrate a specific file
        python -m fec dates migrate --file all_candidate_summaries_1980-2026.csv
    """
    if dry_run:
        console.print("[yellow]DRY RUN - no files will be modified[/yellow]\n")

    # Determine data directory
    config = ctx.obj.get("config") if ctx.obj else None
    data_path = data_dir or (config.data_dir if config else Path("data"))

    # Process data files
    files_to_process = (
        {file: DATA_FILE_DATE_COLUMNS[file]}
        if file and file in DATA_FILE_DATE_COLUMNS
        else DATA_FILE_DATE_COLUMNS
    )

    console.print("[bold]Converting dates to ISO 8601 format...[/bold]\n")

    for filename, date_cols in files_to_process.items():
        filepath = data_path / filename
        if not filepath.exists():
            console.print(f"[yellow]Skipping {filename}: not found[/yellow]")
            continue

        _process_file(filepath, date_cols, dry_run)

    console.print("\n[green]Done![/green]")


def _process_file(filepath: Path, date_cols: list[str], dry_run: bool) -> None:
    """Process a single file, converting date columns to ISO 8601."""
    console.print(f"[bold]{filepath.name}[/bold]")
    console.print(f"  Columns: {', '.join(date_cols)}")

    df = read_fec_csv(filepath)
    original_count = len(df)

    for col in date_cols:
        if col not in df.columns:
            console.print(f"  [yellow]Column '{col}' not found, skipping[/yellow]")
            continue

        # Sample before/after
        sample_before = df[col].drop_nulls().head(3).to_list()

        df = df.with_columns(
            pl.col(col)
            .map_elements(convert_to_iso_date, return_dtype=pl.Utf8)
            .alias(col)
        )

        sample_after = df[col].drop_nulls().head(3).to_list()

        # Show samples
        for before, after in zip(sample_before, sample_after):
            if before != after:
                console.print(f"    {before} -> {after}")

    if dry_run:
        console.print(f"  [dim]Would write {original_count:,} rows[/dim]")
    else:
        atomic_write_csv(df, filepath, backup=True)
        console.print(f"  [green]Wrote {original_count:,} rows[/green]")


@dates.command()
@click.argument("date_string")
def test(date_string: str) -> None:
    """Test date conversion on a single date string.

    Examples:

        python -m fec dates test "12/31/2024"
        python -m fec dates test "01/15/1980"
        python -m fec dates test "12312024"
    """
    result = convert_to_iso_date(date_string)
    console.print(f"[dim]Input:[/dim]  {date_string}")
    if result:
        console.print(f"[green]Output:[/green] {result}")
    else:
        console.print(f"[red]Output:[/red] (invalid date)")
