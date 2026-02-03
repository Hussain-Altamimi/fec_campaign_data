"""Congress.gov API CLI commands."""

import os
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()

# Default paths
SCRIPT_DIR = Path(__file__).parent.parent.parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"


def load_api_key_from_env_file() -> str | None:
    """Load API key from .env.local file."""
    env_file = PROJECT_DIR / ".env.local"
    if not env_file.exists():
        return None

    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                if key.strip() == "CONGRESS_GOV_API_KEY":
                    # Remove quotes if present
                    value = value.strip().strip("'").strip('"')
                    return value
    return None


@click.group()
def congress() -> None:
    """Congress.gov API commands.

    Download and manage member data from the Congress.gov API.
    """
    pass


@congress.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
def download(dry_run: bool) -> None:
    """Download all members from unitedstates/congress-legislators.

    Fetches all ~12,700 members of Congress (1789-present) from the
    unitedstates/congress-legislators GitHub repository and saves to
    data/bioguide_ids/congress_api_members.json.

    No API key required - data is fetched from public GitHub repo.
    """
    from ..processors.congress_api import CongressAPIProcessor

    if dry_run:
        console.print("[yellow]DRY RUN - no files will be written[/yellow]\n")

    processor = CongressAPIProcessor(DATA_DIR)
    members = processor.fetch_all_members(dry_run=dry_run)

    if not dry_run and members:
        processor.save_members(members)


@congress.command()
def status() -> None:
    """Show current congress_api_members.json stats."""
    from ..processors.congress_api import CongressAPIProcessor

    processor = CongressAPIProcessor(DATA_DIR)
    stats = processor.get_status()

    if not stats["exists"]:
        console.print("[yellow]congress_api_members.json not found[/yellow]")
        console.print(f"Expected location: {DATA_DIR / 'bioguide_ids' / 'congress_api_members.json'}")
        return

    console.print("[bold]Congress API Members Status[/bold]\n")
    console.print(f"File: {stats['file_path']}")
    console.print(f"Total members: {stats['count']:,}\n")

    # Party breakdown table
    table = Table(title="Members by Party")
    table.add_column("Party", style="cyan")
    table.add_column("Count", justify="right")

    for party, count in sorted(stats["party_counts"].items(), key=lambda x: -x[1]):
        table.add_row(party, f"{count:,}")
    console.print(table)

    # Chamber breakdown
    console.print()
    table = Table(title="Members by Chamber (Most Recent Term)")
    table.add_column("Chamber", style="cyan")
    table.add_column("Count", justify="right")

    for chamber, count in sorted(stats["chamber_counts"].items(), key=lambda x: -x[1]):
        if count > 0:
            table.add_row(chamber, f"{count:,}")
    console.print(table)
