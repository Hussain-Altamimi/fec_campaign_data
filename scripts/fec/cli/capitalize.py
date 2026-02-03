"""Name capitalization CLI commands."""

from pathlib import Path

import click
import polars as pl
from rich.console import Console

from ..utils.names import capitalize_name
from ..utils.io import atomic_write_csv, read_fec_csv

console = Console()

# Mapping of data files to their name columns
DATA_FILE_NAME_COLUMNS = {
    "all_candidate_summaries_1980-2026.csv": ["cand_name"],
    "candidate_registrations_1980-2026.csv": ["cand_name"],
    "committee_registrations_1980-2026.csv": ["cmte_nm", "tres_nm", "connected_org_nm"],
    "house_senate_campaign_summaries_1996-2026.csv": ["cand_name"],
    "pac_party_summaries_1996-2026.csv": ["cmte_nm"],
    "committee_transaction_summaries_1980-2026.csv": ["dest_name"],
    "committee_to_candidate_summaries_1980-2026.csv": ["cmte_name"],
}

# Individual contribution columns to capitalize
INDIVIDUAL_NAME_COLUMNS = ["name", "employer", "occupation"]


@click.group()
def capitalize() -> None:
    """Name capitalization commands."""
    pass


@capitalize.command()
@click.option(
    "--file",
    type=str,
    help="Process only this specific file (filename only, not path)",
)
@click.option(
    "--include-individual",
    is_flag=True,
    help="Also process individual contributions files (large, may take a long time)",
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
@click.option(
    "--individual-dir",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to individual contributions directory",
)
@click.pass_context
def migrate(
    ctx: click.Context,
    file: str | None,
    include_individual: bool,
    dry_run: bool,
    data_dir: Path | None,
    individual_dir: Path | None,
) -> None:
    """Convert ALL-CAPS names to Capital Case in existing data files.

    This is a one-time migration command. Future updates will automatically
    apply capitalization during processing.

    Examples:

        # Preview changes (dry run)
        python -m fec capitalize migrate --dry-run

        # Migrate main data files
        python -m fec capitalize migrate

        # Migrate a specific file
        python -m fec capitalize migrate --file candidate_registrations_1980-2026.csv

        # Also migrate individual contributions (large files)
        python -m fec capitalize migrate --include-individual
    """
    if dry_run:
        console.print("[yellow]DRY RUN - no files will be modified[/yellow]\n")

    # Determine data directory
    config = ctx.obj.get("config") if ctx.obj else None
    data_path = data_dir or (config.data_dir if config else Path("data"))

    # Process main data files
    files_to_process = {file: DATA_FILE_NAME_COLUMNS[file]} if file and file in DATA_FILE_NAME_COLUMNS else DATA_FILE_NAME_COLUMNS

    console.print("[bold]Processing main data files...[/bold]\n")

    for filename, name_cols in files_to_process.items():
        filepath = data_path / filename
        if not filepath.exists():
            console.print(f"[yellow]Skipping {filename}: not found[/yellow]")
            continue

        _process_file(filepath, name_cols, dry_run)

    # Process individual contributions if requested
    if include_individual:
        console.print("\n[bold]Processing individual contributions files...[/bold]\n")

        ind_path = individual_dir or data_path.parent / "individual_contributions"
        if not ind_path.exists():
            console.print(f"[yellow]Individual contributions directory not found: {ind_path}[/yellow]")
        else:
            ind_files = sorted(ind_path.glob("*_individual_contributions.csv"))
            if not ind_files:
                console.print("[yellow]No individual contribution files found[/yellow]")
            else:
                for filepath in ind_files:
                    _process_file(filepath, INDIVIDUAL_NAME_COLUMNS, dry_run)

    console.print("\n[green]Done![/green]")


def _process_file(filepath: Path, name_cols: list[str], dry_run: bool) -> None:
    """Process a single file, capitalizing name columns."""
    console.print(f"[bold]{filepath.name}[/bold]")
    console.print(f"  Columns: {', '.join(name_cols)}")

    df = read_fec_csv(filepath)
    original_count = len(df)

    for col in name_cols:
        if col not in df.columns:
            console.print(f"  [yellow]Column '{col}' not found, skipping[/yellow]")
            continue

        # Sample before/after
        sample_before = df[col].drop_nulls().head(3).to_list()

        df = df.with_columns(
            pl.col(col)
            .map_elements(capitalize_name, return_dtype=pl.Utf8)
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


@capitalize.command()
@click.argument("name")
def test(name: str) -> None:
    """Test capitalization on a single name.

    Examples:

        python -m fec capitalize test "SMITH, JOHN JR"
        python -m fec capitalize test "O'BRIEN, PAT"
        python -m fec capitalize test "MCDONALD, RONALD"
        python -m fec capitalize test "AFL-CIO COPE COMMITTEE"
    """
    result = capitalize_name(name)
    console.print(f"[dim]Input:[/dim]  {name}")
    console.print(f"[green]Output:[/green] {result}")
