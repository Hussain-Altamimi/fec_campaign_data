"""Verify command for FEC data validation."""

import click
from rich.console import Console

from ..config import Config
from ..verify import print_cycle_summary, print_verification_report, verify_all

console = Console()


@click.command()
@click.option(
    "--cycle-counts",
    is_flag=True,
    help="Show row counts per election cycle",
)
@click.pass_context
def verify(ctx: click.Context, cycle_counts: bool) -> None:
    """Verify data file integrity.

    Checks:
    - All expected files exist
    - No null election_cycle values
    - Transaction amounts are reasonable
    - Row counts match expectations
    """
    config: Config = ctx.obj["config"]

    if config is None:
        console.print("[red]Error: Configuration not loaded. Check --config and --data-dir paths.[/red]")
        raise SystemExit(1)

    results = verify_all(config)
    print_verification_report(results)

    if cycle_counts:
        print_cycle_summary(config)

    # Exit with error if any validation failed
    if any(not r.is_valid for r in results):
        raise SystemExit(1)
