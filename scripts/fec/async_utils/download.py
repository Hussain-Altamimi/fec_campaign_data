"""Async download utilities for FEC data.

Provides download functions with retry logic, progress bars, and ZIP extraction.
"""

import asyncio
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

import httpx
from rich.console import Console
from rich.progress import Progress

from ..utils.progress import create_download_progress

console = Console()

# Default configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 2.0  # seconds
DEFAULT_TIMEOUT = 300.0  # seconds
DEFAULT_CHUNK_SIZE = 8192


async def download_with_retry(
    client: httpx.AsyncClient,
    url: str,
    dest: Path,
    progress: Progress,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> bool:
    """Download a file with retry logic and progress bar.

    Args:
        client: httpx async client
        url: URL to download
        dest: Destination path
        progress: Rich progress instance
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries (multiplied by attempt number)
        chunk_size: Size of chunks to read

    Returns:
        True if download succeeded, False otherwise
    """
    for attempt in range(max_retries):
        try:
            async with client.stream("GET", url, follow_redirects=True) as response:
                response.raise_for_status()

                total = int(response.headers.get("content-length", 0))
                task_id = progress.add_task(
                    f"[cyan]Downloading {dest.name}",
                    total=total,
                )

                with open(dest, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                        f.write(chunk)
                        progress.update(task_id, advance=len(chunk))

                progress.remove_task(task_id)
                return True

        except httpx.HTTPError as e:
            if attempt < max_retries - 1:
                console.print(
                    f"[yellow]Retry {attempt + 1}/{max_retries} for {url}: {e}[/yellow]"
                )
                await asyncio.sleep(retry_delay * (attempt + 1))
            else:
                console.print(
                    f"[red]Failed to download {url} after {max_retries} attempts: {e}[/red]"
                )
                return False

    return False


def extract_zip(
    zip_path: Path,
    dest_dir: Path,
    cycle: int | None = None,
    prefix_with_cycle: bool = True,
) -> list[Path]:
    """Extract zip file contents.

    Args:
        zip_path: Path to the ZIP file
        dest_dir: Directory to extract to
        cycle: Election cycle (used for year-prefix naming)
        prefix_with_cycle: If True, prefix filenames with cycle year

    Returns:
        List of extracted file paths
    """
    extracted_files: list[Path] = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue

            # Get just the filename, ignoring nested directories
            original_name = Path(info.filename).name

            # Add year prefix to prevent collisions
            if prefix_with_cycle and cycle:
                new_name = f"{cycle}_{original_name}"
            else:
                new_name = original_name

            dest_path = dest_dir / new_name

            # Extract to destination
            with zf.open(info) as src, open(dest_path, "wb") as dst:
                dst.write(src.read())

            extracted_files.append(dest_path)

    return extracted_files


async def download_and_extract(
    url: str,
    cycle: int,
    work_dir: Path,
    timeout: float = DEFAULT_TIMEOUT,
    prefix_with_cycle: bool = True,
) -> list[Path] | None:
    """Download ZIP file, extract contents, and return extracted paths.

    Args:
        url: URL to download
        cycle: Election cycle year
        work_dir: Directory to extract files to
        timeout: HTTP timeout in seconds
        prefix_with_cycle: If True, prefix filenames with cycle year

    Returns:
        List of extracted file paths, or None if download failed
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        with create_download_progress(console) as progress:
            with TemporaryDirectory() as tmpdir:
                zip_path = Path(tmpdir) / f"{cycle}.zip"

                success = await download_with_retry(client, url, zip_path, progress)
                if not success:
                    return None

                console.print(f"  Extracting {zip_path.name}...")
                extracted = extract_zip(
                    zip_path, work_dir, cycle, prefix_with_cycle=prefix_with_cycle
                )
                console.print(f"  Extracted {len(extracted)} file(s)")

                return extracted


async def download_cycle(
    url: str,
    cycle: int,
    work_dir: Path,
    dry_run: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> list[Path] | None:
    """Download and extract a single cycle's data.

    Args:
        url: URL to download
        cycle: Election cycle year
        work_dir: Directory to extract files to
        dry_run: If True, don't actually download
        timeout: HTTP timeout in seconds

    Returns:
        List of extracted file paths, or empty list for dry run, or None if failed
    """
    if dry_run:
        console.print(f"  [dim]Would download: {url}[/dim]")
        return []

    console.print(f"  Downloading cycle {cycle}...")
    return await download_and_extract(url, cycle, work_dir, timeout=timeout)


async def download_file(
    url: str,
    dest: Path,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> bool:
    """Download a single file without extraction.

    Args:
        url: URL to download
        dest: Destination path
        timeout: HTTP timeout in seconds
        max_retries: Maximum retry attempts

    Returns:
        True if download succeeded, False otherwise
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        with create_download_progress(console) as progress:
            return await download_with_retry(
                client, url, dest, progress, max_retries=max_retries
            )
