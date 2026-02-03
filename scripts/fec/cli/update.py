"""Update commands for FEC data workflow."""

import asyncio
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console

from ..config import Config, UpdateState, get_cycles_to_check, get_fec_zip_url
from ..detect import detect_changes, ChangeInfo
from ..integrate import integrate_changes

console = Console()


@click.group()
@click.pass_context
def update(ctx: click.Context) -> None:
    """Check for and apply FEC data updates."""
    if ctx.obj.get("config") is None:
        console.print("[red]Error: Configuration not loaded. Check --config and --data-dir paths.[/red]")
        raise SystemExit(1)


@update.command()
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


@update.command()
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


@update.command()
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
