"""Main CLI entry point for FEC data tools."""

from pathlib import Path

import click
from rich.console import Console

from ..config import Config, UpdateState

console = Console()

# Default paths relative to script location
SCRIPT_DIR = Path(__file__).parent.parent.parent
CONFIG_PATH = SCRIPT_DIR / "fec" / "config" / "datasets.yaml"
DATA_DIR = SCRIPT_DIR.parent / "data"


@click.group()
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to datasets.yaml config file",
)
@click.option(
    "--data-dir",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to data directory",
)
@click.pass_context
def cli(ctx: click.Context, config: Path | None, data_dir: Path | None) -> None:
    """FEC Data Tools.

    Download, process, and manage FEC campaign finance data.
    """
    ctx.ensure_object(dict)

    # Use defaults if not provided
    config_path = config or CONFIG_PATH
    data_path = data_dir or DATA_DIR

    # Only load config if it exists (some commands may not need it)
    if config_path.exists() and data_path.exists():
        ctx.obj["config"] = Config.load(config_path, data_path)
        ctx.obj["state"] = UpdateState.load(ctx.obj["config"].state_file)
    else:
        ctx.obj["config"] = None
        ctx.obj["state"] = None


# Import and register command groups
from .update import update
from .verify import verify
from .individual import individual
from .bioguide import bioguide
from .capitalize import capitalize
from .dates import dates
from .congress_api import congress

cli.add_command(update)
cli.add_command(verify)
cli.add_command(individual)
cli.add_command(bioguide)
cli.add_command(capitalize)
cli.add_command(dates)
cli.add_command(congress)


def main() -> None:
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
