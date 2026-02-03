"""Progress bar utilities for consistent UI across scripts."""

from rich.console import Console
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)


def create_download_progress(console: Console) -> Progress:
    """Create a progress bar for file downloads.

    Shows download progress with speed and ETA.

    Args:
        console: Rich console instance

    Returns:
        Configured Progress instance for downloads
    """
    return Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    )


def create_spinner_progress(console: Console, transient: bool = True) -> Progress:
    """Create a spinner progress for processing tasks.

    Shows a spinner with elapsed time for long-running operations.

    Args:
        console: Rich console instance
        transient: If True, remove progress bar when done

    Returns:
        Configured Progress instance with spinner
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=transient,
    )
