"""Download FEC data files with retry logic.

This module re-exports from fec.async_utils for backward compatibility.
New code should import directly from fec.async_utils.download.
"""

from pathlib import Path

from rich.console import Console

# Import shared utilities
# Try fec package first (new location), fall back to local for compatibility
try:
    from fec.async_utils.download import (
        download_with_retry,
        extract_zip,
        download_and_extract,
        download_cycle,
        DEFAULT_MAX_RETRIES as MAX_RETRIES,
        DEFAULT_RETRY_DELAY as RETRY_DELAY,
    )
except ImportError:
    # Fallback: keep original implementation for backward compatibility
    import zipfile
    from tempfile import TemporaryDirectory

    import httpx
    from rich.progress import (
        BarColumn,
        DownloadColumn,
        Progress,
        TextColumn,
        TimeRemainingColumn,
        TransferSpeedColumn,
    )

    MAX_RETRIES = 3
    RETRY_DELAY = 2.0

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
                    import asyncio
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    console.print(f"[red]Failed to download {url} after {MAX_RETRIES} attempts: {e}[/red]")
                    return False
        return False

    def extract_zip(zip_path: Path, dest_dir: Path, cycle: int) -> list[Path]:
        """Extract zip file with year-prefix naming."""
        extracted_files: list[Path] = []
        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                original_name = Path(info.filename).name
                new_name = f"{cycle}_{original_name}"
                dest_path = dest_dir / new_name
                with zf.open(info) as src, open(dest_path, "wb") as dst:
                    dst.write(src.read())
                extracted_files.append(dest_path)
        return extracted_files

    async def download_and_extract(
        url: str,
        cycle: int,
        work_dir: Path,
    ) -> list[Path] | None:
        """Download zip file, extract with year prefix, and return extracted paths."""
        async with httpx.AsyncClient(timeout=300.0) as client:
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                with TemporaryDirectory() as tmpdir:
                    zip_path = Path(tmpdir) / f"{cycle}.zip"
                    success = await download_with_retry(client, url, zip_path, progress)
                    if not success:
                        return None
                    console.print(f"  Extracting {zip_path.name}...")
                    extracted = extract_zip(zip_path, work_dir, cycle)
                    console.print(f"  Extracted {len(extracted)} file(s)")
                    return extracted

    async def download_cycle(
        url: str,
        cycle: int,
        work_dir: Path,
        dry_run: bool = False,
    ) -> list[Path] | None:
        """Download and extract a single cycle's data."""
        if dry_run:
            console.print(f"  [dim]Would download: {url}[/dim]")
            return []
        console.print(f"  Downloading cycle {cycle}...")
        return await download_and_extract(url, cycle, work_dir)

console = Console()

__all__ = [
    "download_with_retry",
    "extract_zip",
    "download_and_extract",
    "download_cycle",
    "MAX_RETRIES",
    "RETRY_DELAY",
]
