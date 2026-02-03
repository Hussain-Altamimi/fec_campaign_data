"""Individual contributions CLI commands."""

from pathlib import Path

import click
from rich.console import Console

console = Console()

# Default paths
SCRIPT_DIR = Path(__file__).parent.parent.parent
PROJECT_DIR = SCRIPT_DIR.parent
INDIVIDUAL_DIR = PROJECT_DIR / "individual_contributions"
DATA_DIR = PROJECT_DIR / "data"
HEADER_FILE = INDIVIDUAL_DIR / "indiv_header_file.csv"
OUTPUT_FILE = DATA_DIR / "candidate_individual_contribution_summaries_1980-2026.csv"


@click.group()
def individual() -> None:
    """Individual contributions commands.

    Download, process, and summarize FEC individual contribution data.
    """
    pass


@individual.command()
@click.option(
    "--cycle",
    type=int,
    help="Download only this election cycle",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be downloaded without downloading",
)
@click.pass_context
def download(ctx: click.Context, cycle: int | None, dry_run: bool) -> None:
    """Download FEC individual contributions data (1980-2026).

    Downloads ZIP files from FEC, extracts pipe-delimited data, and
    converts to CSV. Skips cycles where output file already exists.
    """
    from ..processors.individual import IndividualDownloader

    if dry_run:
        console.print("[yellow]DRY RUN - no files will be downloaded[/yellow]\n")

    console.print("[bold]FEC Individual Contributions Download[/bold]")
    console.print(f"Output directory: {INDIVIDUAL_DIR}\n")

    if not INDIVIDUAL_DIR.exists():
        console.print(f"[red]Error: Output directory not found: {INDIVIDUAL_DIR}[/red]")
        raise SystemExit(1)

    downloader = IndividualDownloader(INDIVIDUAL_DIR, HEADER_FILE)

    cycles = [cycle] if cycle else None
    successful, skipped, failed = downloader.download_all(dry_run=dry_run, cycles=cycles)

    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Successful: {successful}")
    console.print(f"  Skipped: {skipped}")
    console.print(f"  Failed: {failed}")

    if failed > 0:
        raise SystemExit(1)


@individual.command("add-year")
@click.option(
    "--cycle",
    type=int,
    help="Process only this election cycle",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--force",
    is_flag=True,
    help="Recompute transaction_year even if column already exists",
)
@click.option(
    "--dir",
    "input_dir",
    type=click.Path(exists=True, path_type=Path),
    default=INDIVIDUAL_DIR,
    help="Directory containing individual contribution files",
)
@click.pass_context
def add_year(ctx: click.Context, cycle: int | None, dry_run: bool, force: bool, input_dir: Path) -> None:
    """Add transaction_year column to individual contribution files.

    Extracts the year from transaction_dt and inserts it as the second column.
    """
    from ..processors.individual import TransactionYearAdder

    if dry_run:
        console.print("[yellow]DRY RUN - no files will be modified[/yellow]\n")

    console.print("[bold]Add Transaction Year Column[/bold]")
    console.print(f"Input directory: {input_dir}\n")

    adder = TransactionYearAdder(input_dir)
    total_rows = adder.process_all(cycle=cycle, dry_run=dry_run, force=force)

    console.print(f"\n[green]Done![/green] Processed {total_rows:,} total rows")


@individual.command()
@click.option(
    "--cycle",
    type=int,
    help="Process only this election cycle",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without writing output",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=OUTPUT_FILE,
    help="Output file path",
)
@click.pass_context
def summarize(ctx: click.Context, cycle: int | None, dry_run: bool, output: Path) -> None:
    """Aggregate individual contributions by candidate.

    Creates a summary file with total contributions and counts per candidate,
    grouped by election cycle and transaction year.
    """
    from ..processors.individual import IndividualSummarizer

    if dry_run:
        console.print("[yellow]DRY RUN - no files will be written[/yellow]\n")

    console.print("[bold]Individual Contributions Summary[/bold]")
    console.print(f"Output file: {output}\n")

    summarizer = IndividualSummarizer(DATA_DIR, INDIVIDUAL_DIR, output)
    summarizer.summarize_all(cycle=cycle, dry_run=dry_run)
