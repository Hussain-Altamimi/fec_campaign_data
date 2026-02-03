"""Bioguide crosswalk CLI commands."""

from pathlib import Path

import click
from rich.console import Console

console = Console()

# Default paths
SCRIPT_DIR = Path(__file__).parent.parent.parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_FILE = DATA_DIR / "cand_id_bioguide_crosswalk.csv"


@click.group()
def bioguide() -> None:
    """Bioguide crosswalk commands.

    Create and manage FEC-to-Bioguide ID mappings.
    """
    pass


@bioguide.command()
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=OUTPUT_FILE,
    help="Output file path",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without writing output",
)
@click.pass_context
def create(ctx: click.Context, output: Path, dry_run: bool) -> None:
    """Create FEC-to-Bioguide ID crosswalk.

    Fetches Congressional legislator data from the unitedstates/congress-legislators
    repository and creates a mapping between FEC candidate IDs and Bioguide IDs.
    """
    from ..processors.bioguide import BioguideProcessor

    if dry_run:
        console.print("[yellow]DRY RUN - no files will be written[/yellow]\n")

    processor = BioguideProcessor(DATA_DIR, output)
    processor.create_crosswalk(dry_run=dry_run)
