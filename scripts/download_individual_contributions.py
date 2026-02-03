#!/usr/bin/env python3
"""Download and process FEC individual contributions data (1980-2026).

Downloads ZIP files from FEC bulk data, extracts pipe-delimited itcont.txt,
and converts to CSV with snake_case headers.
"""

import asyncio
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

import click
import httpx
import polars as pl
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

console = Console()

# Configuration
FEC_BASE_URL = "https://www.fec.gov/files/bulk-downloads"
ELECTION_CYCLES = list(range(1980, 2028, 2))  # 1980, 1982, ..., 2026
MAX_RETRIES = 3
RETRY_DELAY = 2.0

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_DIR / "individual_contributions"
HEADER_FILE = OUTPUT_DIR / "indiv_header_file.csv"


def get_fec_url(cycle: int) -> str:
    """Build FEC URL for individual contributions ZIP file."""
    year_suffix = str(cycle)[2:]
    return f"{FEC_BASE_URL}/{cycle}/indiv{year_suffix}.zip"


def get_output_path(cycle: int) -> Path:
    """Get output CSV path for a cycle."""
    return OUTPUT_DIR / f"{cycle}_individual_contributions.csv"


def load_headers() -> list[str]:
    """Load headers from header file and convert to snake_case."""
    with open(HEADER_FILE) as f:
        raw_headers = f.read().strip().split(",")
    # Convert to snake_case (already lowercase in file, just ensure consistency)
    return [h.lower() for h in raw_headers]


async def download_with_retry(
    client: httpx.AsyncClient,
    url: str,
    dest: Path,
    progress: Progress,
) -> bool:
    """Download a file with retry logic and progress bar."""
    for attempt in range(MAX_RETRIES):
        try:
            async with client.stream("GET", url, follow_redirects=True) as response:
                response.raise_for_status()

                total = int(response.headers.get("content-length", 0))
                task_id = progress.add_task(
                    f"[cyan]Downloading {dest.name}",
                    total=total,
                )

                with open(dest, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        progress.update(task_id, advance=len(chunk))

                progress.remove_task(task_id)
                return True

        except httpx.HTTPError as e:
            if attempt < MAX_RETRIES - 1:
                console.print(
                    f"[yellow]Retry {attempt + 1}/{MAX_RETRIES} for {url}: {e}[/yellow]"
                )
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
            else:
                console.print(
                    f"[red]Failed to download {url} after {MAX_RETRIES} attempts: {e}[/red]"
                )
                return False

    return False


def process_zip(zip_path: Path, cycle: int, headers: list[str], output_path: Path) -> bool:
    """Extract and convert pipe-delimited data to CSV."""
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Find itcont.txt in the zip
            itcont_name = None
            for name in zf.namelist():
                if name.lower().endswith("itcont.txt"):
                    itcont_name = name
                    break

            if not itcont_name:
                console.print(f"[red]No itcont.txt found in {zip_path.name}[/red]")
                return False

            console.print(f"  Extracting and converting {itcont_name}...")

            with zf.open(itcont_name) as f:
                # Read pipe-delimited file with polars
                # FEC files have unescaped quotes, so disable quoting entirely
                df = pl.read_csv(
                    f,
                    separator="|",
                    has_header=False,
                    new_columns=headers,
                    infer_schema_length=10000,
                    ignore_errors=True,
                    quote_char=None,  # Disable quote parsing - FEC data has unescaped quotes
                    truncate_ragged_lines=True,  # Handle malformed rows
                    encoding="utf8-lossy",  # Handle invalid UTF-8 sequences
                )

                # Prepend election_cycle column
                df = df.with_columns(pl.lit(cycle).alias("election_cycle"))

                # Reorder to put election_cycle first
                cols = ["election_cycle"] + headers
                df = df.select(cols)

                # Write as CSV
                df.write_csv(output_path)

        return True

    except Exception as e:
        console.print(f"[red]Error processing {zip_path.name}: {e}[/red]")
        return False


async def download_cycle(cycle: int, headers: list[str], dry_run: bool) -> bool:
    """Download and process a single cycle."""
    output_path = get_output_path(cycle)

    # Check if already exists
    if output_path.exists():
        console.print(f"[dim]{cycle}: Already exists, skipping[/dim]")
        return True

    url = get_fec_url(cycle)

    if dry_run:
        console.print(f"[dim]{cycle}: Would download {url}[/dim]")
        return True

    console.print(f"\n[bold]{cycle}:[/bold] {url}")

    async with httpx.AsyncClient(timeout=600.0) as client:
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            with TemporaryDirectory() as tmpdir:
                zip_path = Path(tmpdir) / f"indiv{str(cycle)[2:]}.zip"

                success = await download_with_retry(client, url, zip_path, progress)
                if not success:
                    return False

                success = process_zip(zip_path, cycle, headers, output_path)
                if success:
                    # Report file size
                    size_mb = output_path.stat().st_size / (1024 * 1024)
                    console.print(f"  [green]Wrote {output_path.name} ({size_mb:.1f} MB)[/green]")

                return success


@click.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be downloaded without downloading",
)
def main(dry_run: bool) -> None:
    """Download FEC individual contributions data (1980-2026).

    Downloads ZIP files from FEC, extracts pipe-delimited data, and
    converts to CSV with snake_case headers. Skips cycles where
    output file already exists.
    """
    if dry_run:
        console.print("[yellow]DRY RUN - no files will be downloaded[/yellow]\n")

    console.print("[bold]FEC Individual Contributions Download[/bold]")
    console.print(f"Output directory: {OUTPUT_DIR}\n")

    # Load headers
    if not HEADER_FILE.exists():
        console.print(f"[red]Header file not found: {HEADER_FILE}[/red]")
        raise SystemExit(1)

    headers = load_headers()
    console.print(f"Headers: {len(headers)} columns (+ election_cycle)\n")

    # Process each cycle
    successful = 0
    failed = 0
    skipped = 0

    for cycle in ELECTION_CYCLES:
        output_path = get_output_path(cycle)
        if output_path.exists():
            skipped += 1
            console.print(f"[dim]{cycle}: Already exists, skipping[/dim]")
            continue

        success = asyncio.run(download_cycle(cycle, headers, dry_run))
        if success:
            successful += 1
        else:
            failed += 1

    # Summary
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Successful: {successful}")
    console.print(f"  Skipped: {skipped}")
    console.print(f"  Failed: {failed}")

    if failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
