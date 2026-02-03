"""Change detection for FEC data files."""

from dataclasses import dataclass

import httpx
from rich.console import Console

from .config import (
    Config,
    CycleState,
    UpdateState,
    get_cycles_to_check,
    get_fec_zip_url,
)

console = Console()


@dataclass
class ChangeInfo:
    """Information about a detected change."""

    dataset: str
    cycle: int
    url: str
    reason: str
    new_etag: str | None = None
    new_last_modified: str | None = None
    new_content_length: int | None = None


def has_changed(old_state: CycleState | None, new_state: CycleState) -> tuple[bool, str]:
    """Check if a cycle has changed based on HTTP headers."""
    if old_state is None:
        return True, "new cycle"

    # Check ETag first (most reliable)
    if new_state.etag and old_state.etag:
        if new_state.etag != old_state.etag:
            return True, "etag changed"

    # Check Last-Modified
    if new_state.last_modified and old_state.last_modified:
        if new_state.last_modified != old_state.last_modified:
            return True, "last-modified changed"

    # Check Content-Length as fallback
    if new_state.content_length and old_state.content_length:
        if new_state.content_length != old_state.content_length:
            return True, "content-length changed"

    return False, "no change"


async def check_url(client: httpx.AsyncClient, url: str) -> CycleState | None:
    """Check a URL using HTTP HEAD request."""
    try:
        response = await client.head(url, follow_redirects=True)
        if response.status_code == 404:
            return None
        response.raise_for_status()

        return CycleState(
            etag=response.headers.get("etag"),
            last_modified=response.headers.get("last-modified"),
            content_length=int(response.headers.get("content-length", 0)) or None,
        )
    except httpx.HTTPError as e:
        console.print(f"[yellow]Warning: Failed to check {url}: {e}[/yellow]")
        return None


async def detect_changes(
    config: Config,
    state: UpdateState,
    cycles: list[int] | None = None,
) -> list[ChangeInfo]:
    """Detect changes across all datasets for specified cycles."""
    if cycles is None:
        cycles = get_cycles_to_check()

    changes: list[ChangeInfo] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check combine datasets
        for name, dataset in config.combine_datasets.items():
            for cycle in cycles:
                if cycle < dataset.start_year:
                    continue

                url = get_fec_zip_url(config.fec_base_url, dataset.fec_prefix, cycle)
                console.print(f"  Checking {name} {cycle}...", end=" ")

                new_state = await check_url(client, url)
                if new_state is None:
                    console.print("[yellow]not found[/yellow]")
                    continue

                old_state = state.get_cycle_state(name, cycle)
                changed, reason = has_changed(old_state, new_state)

                if changed:
                    console.print(f"[green]{reason}[/green]")
                    changes.append(
                        ChangeInfo(
                            dataset=name,
                            cycle=cycle,
                            url=url,
                            reason=reason,
                            new_etag=new_state.etag,
                            new_last_modified=new_state.last_modified,
                            new_content_length=new_state.content_length,
                        )
                    )
                else:
                    console.print("[dim]unchanged[/dim]")

        # Check summarize datasets (skip expenditures_by_state, same file as by_category)
        for name, dataset in config.summarize_datasets.items():
            if name == "expenditures_by_state":
                continue  # Same file as expenditures_by_category

            for cycle in cycles:
                if cycle < dataset.start_year:
                    continue

                url = get_fec_zip_url(config.fec_base_url, dataset.fec_prefix, cycle)
                console.print(f"  Checking {name} {cycle}...", end=" ")

                new_state = await check_url(client, url)
                if new_state is None:
                    console.print("[yellow]not found[/yellow]")
                    continue

                old_state = state.get_cycle_state(name, cycle)
                changed, reason = has_changed(old_state, new_state)

                if changed:
                    console.print(f"[green]{reason}[/green]")
                    changes.append(
                        ChangeInfo(
                            dataset=name,
                            cycle=cycle,
                            url=url,
                            reason=reason,
                            new_etag=new_state.etag,
                            new_last_modified=new_state.last_modified,
                            new_content_length=new_state.content_length,
                        )
                    )
                else:
                    console.print("[dim]unchanged[/dim]")

    return changes
