"""CLI entry point for FEC update workflow."""

import asyncio
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console

from .config import Config, UpdateState, get_cycles_to_check
from .detect import detect_changes
from .integrate import integrate_changes
from .verify import print_cycle_summary, print_verification_report, verify_all

console = Console()

# Default paths relative to script location
SCRIPT_DIR = Path(__file__).parent.parent
CONFIG_PATH = SCRIPT_DIR / "config" / "datasets.yaml"
DATA_DIR = SCRIPT_DIR.parent / "data"


@click.group()
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    default=CONFIG_PATH,
    help="Path to datasets.yaml config file",
)
@click.option(
    "--data-dir",
    type=click.Path(exists=True, path_type=Path),
    default=DATA_DIR,
    help="Path to data directory",
)
@click.pass_context
def cli(ctx: click.Context, config: Path, data_dir: Path) -> None:
    """FEC Data Update Workflow.

    Check for updates, download new data, and integrate into existing files.
    """
    ctx.ensure_object(dict)
    ctx.obj["config"] = Config.load(config, data_dir)
    ctx.obj["state"] = UpdateState.load(ctx.obj["config"].state_file)


@cli.command()
@click.option(
    "--cycle",
    type=int,
    multiple=True,
    help="Specific cycle(s) to check. Default: current + 2 prior",
)
@click.pass_context
def check(ctx: click.Context, cycle: tuple[int, ...]) -> None:
    """Check FEC for updated data files.

    Compares ETag/Last-Modified headers to saved state to detect changes.
    Does not download or modify any files.
    """
    config: Config = ctx.obj["config"]
    state: UpdateState = ctx.obj["state"]

    cycles = list(cycle) if cycle else get_cycles_to_check()

    console.print(f"[bold]Checking FEC for updates...[/bold]")
    console.print(f"Cycles to check: {cycles}\n")

    changes = asyncio.run(detect_changes(config, state, cycles))

    console.print()
    if changes:
        console.print(f"[green]Found {len(changes)} update(s):[/green]")
        for change in changes:
            console.print(f"  • {change.dataset} {change.cycle}: {change.reason}")
    else:
        console.print("[dim]No updates found[/dim]")


@cli.command()
@click.option(
    "--cycle",
    type=int,
    multiple=True,
    help="Specific cycle(s) to update. Default: current + 2 prior",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.option(
    "--force",
    is_flag=True,
    help="Update even if no changes detected",
)
@click.pass_context
def run(ctx: click.Context, cycle: tuple[int, ...], dry_run: bool, force: bool) -> None:
    """Run the full update workflow.

    1. Check for changes
    2. Download updated files
    3. Process and integrate
    4. Update state
    """
    config: Config = ctx.obj["config"]
    state: UpdateState = ctx.obj["state"]

    cycles = list(cycle) if cycle else get_cycles_to_check()

    if dry_run:
        console.print("[yellow]DRY RUN - no changes will be made[/yellow]\n")

    console.print(f"[bold]FEC Data Update Workflow[/bold]")
    console.print(f"Cycles: {cycles}\n")

    # Step 1: Detect changes
    console.print("[bold]Step 1: Checking for updates...[/bold]")
    changes = asyncio.run(detect_changes(config, state, cycles))

    if not changes and not force:
        console.print("\n[dim]No updates found. Use --force to update anyway.[/dim]")
        return

    if force and not changes:
        console.print("\n[yellow]Force mode: will re-download all cycles[/yellow]")
        # Create synthetic changes for all datasets/cycles
        from .config import get_fec_zip_url
        from .detect import ChangeInfo

        changes = []
        for name, dataset in config.combine_datasets.items():
            for c in cycles:
                if c >= dataset.start_year:
                    changes.append(
                        ChangeInfo(
                            dataset=name,
                            cycle=c,
                            url=get_fec_zip_url(config.fec_base_url, dataset.fec_prefix, c),
                            reason="forced",
                        )
                    )

        for name, dataset in config.summarize_datasets.items():
            if name == "expenditures_by_state":
                continue  # Same source as by_category
            for c in cycles:
                if c >= dataset.start_year:
                    changes.append(
                        ChangeInfo(
                            dataset=name,
                            cycle=c,
                            url=get_fec_zip_url(config.fec_base_url, dataset.fec_prefix, c),
                            reason="forced",
                        )
                    )

    console.print(f"\n[green]Found {len(changes)} update(s) to process[/green]\n")

    # Step 2 & 3: Download and integrate
    console.print("[bold]Step 2-3: Downloading and integrating...[/bold]")
    successful, failed = asyncio.run(integrate_changes(changes, config, state, dry_run))

    # Step 4: Save state
    if not dry_run and successful > 0:
        console.print("\n[bold]Step 4: Saving state...[/bold]")
        state.last_check = datetime.now().isoformat()
        state.save(config.state_file)
        console.print(f"  State saved to {config.state_file}")

    # Summary
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Successful: {successful}")
    console.print(f"  Failed: {failed}")

    if failed > 0:
        raise SystemExit(1)


@cli.command()
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

    results = verify_all(config)
    print_verification_report(results)

    if cycle_counts:
        print_cycle_summary(config)

    # Exit with error if any validation failed
    if any(not r.is_valid for r in results):
        raise SystemExit(1)


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show current update state."""
    config: Config = ctx.obj["config"]
    state: UpdateState = ctx.obj["state"]

    console.print("[bold]FEC Update Status[/bold]\n")

    if state.last_check:
        console.print(f"Last check: {state.last_check}")
    else:
        console.print("Last check: never")

    console.print()

    if not state.cycles:
        console.print("[dim]No cycle state recorded yet[/dim]")
        return

    for dataset, cycles in sorted(state.cycles.items()):
        console.print(f"[cyan]{dataset}[/cyan]")
        for cycle, cycle_state in sorted(cycles.items()):
            console.print(f"  {cycle}: updated {cycle_state.last_updated or 'unknown'}")
        console.print()


def main() -> None:
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
