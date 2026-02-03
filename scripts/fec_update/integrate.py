"""Integration logic for merging new data into existing files."""

from pathlib import Path
from tempfile import TemporaryDirectory

from rich.console import Console

from .config import Config, UpdateState
from .detect import ChangeInfo
from .download import download_cycle
from .processors import CombineProcessor, SummarizeProcessor

console = Console()


def find_input_file(work_dir: Path, fec_prefix: str, cycle: int) -> Path | None:
    """Find the extracted input file for a dataset and cycle."""
    # Pattern: {cycle}_{prefix}{yy}.txt
    year_suffix = str(cycle)[2:]
    pattern = f"{cycle}_{fec_prefix}{year_suffix}.txt"

    matches = list(work_dir.glob(pattern))
    if matches:
        return matches[0]

    # Try case-insensitive match
    for f in work_dir.iterdir():
        if f.name.lower() == pattern.lower():
            return f

    return None


async def process_change(
    change: ChangeInfo,
    config: Config,
    work_dir: Path,
    dry_run: bool = False,
) -> bool:
    """Process a single detected change.

    Downloads the file, processes it, and integrates into existing data.
    """
    console.print(f"\n[bold]Processing {change.dataset} cycle {change.cycle}[/bold]")

    # Download and extract
    extracted = await download_cycle(change.url, change.cycle, work_dir, dry_run)
    if extracted is None:
        console.print(f"[red]Failed to download {change.dataset} {change.cycle}[/red]")
        return False

    if dry_run:
        return True

    # Determine dataset type and get processor
    if change.dataset in config.combine_datasets:
        dataset = config.combine_datasets[change.dataset]
        processor = CombineProcessor(dataset, config.data_dir)
        input_file = find_input_file(work_dir, dataset.fec_prefix, change.cycle)

        if input_file is None:
            console.print(f"[red]Could not find input file for {change.dataset} {change.cycle}[/red]")
            return False

        processor.update_cycle(input_file, change.cycle, dry_run)

    elif change.dataset in config.summarize_datasets:
        dataset = config.summarize_datasets[change.dataset]
        processor = SummarizeProcessor(dataset, config.data_dir)
        input_file = find_input_file(work_dir, dataset.fec_prefix, change.cycle)

        if input_file is None:
            console.print(f"[red]Could not find input file for {change.dataset} {change.cycle}[/red]")
            return False

        processor.update_cycle(input_file, change.cycle, dry_run)

        # Special handling: expenditures_by_category and expenditures_by_state use same source
        if change.dataset == "expenditures_by_category":
            state_dataset = config.summarize_datasets.get("expenditures_by_state")
            if state_dataset:
                console.print(f"\n[bold]Also processing expenditures_by_state cycle {change.cycle}[/bold]")
                state_processor = SummarizeProcessor(state_dataset, config.data_dir)
                state_processor.update_cycle(input_file, change.cycle, dry_run)

    else:
        console.print(f"[red]Unknown dataset: {change.dataset}[/red]")
        return False

    return True


async def integrate_changes(
    changes: list[ChangeInfo],
    config: Config,
    state: UpdateState,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Integrate all detected changes.

    Returns:
        Tuple of (successful_count, failed_count)
    """
    if not changes:
        console.print("[dim]No changes to integrate[/dim]")
        return 0, 0

    successful = 0
    failed = 0

    with TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)

        for change in changes:
            try:
                success = await process_change(change, config, work_dir, dry_run)

                if success:
                    successful += 1
                    # Update state with new metadata
                    if not dry_run:
                        state.update_cycle(
                            change.dataset,
                            change.cycle,
                            change.new_etag,
                            change.new_last_modified,
                            change.new_content_length,
                        )
                else:
                    failed += 1

            except Exception as e:
                console.print(f"[red]Error processing {change.dataset} {change.cycle}: {e}[/red]")
                failed += 1

    return successful, failed
