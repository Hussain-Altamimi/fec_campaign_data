"""Verification and validation for FEC data."""

from dataclasses import dataclass
from pathlib import Path

import polars as pl
from rich.console import Console
from rich.table import Table

from .config import Config

console = Console()


@dataclass
class ValidationResult:
    """Result of validating a single file."""

    file_name: str
    row_count: int
    column_count: int
    has_election_cycle: bool
    null_election_cycle: int
    min_cycle: int | None
    max_cycle: int | None
    issues: list[str]

    @property
    def is_valid(self) -> bool:
        return len(self.issues) == 0


def validate_file(file_path: Path) -> ValidationResult:
    """Validate a single CSV file."""
    issues: list[str] = []

    try:
        # Use infer_schema_length=10000 and treat mixed types as strings
        df = pl.read_csv(file_path, infer_schema_length=10000, ignore_errors=True)
    except Exception as e:
        return ValidationResult(
            file_name=file_path.name,
            row_count=0,
            column_count=0,
            has_election_cycle=False,
            null_election_cycle=0,
            min_cycle=None,
            max_cycle=None,
            issues=[f"Failed to read file: {e}"],
        )

    row_count = len(df)
    column_count = len(df.columns)

    # Check for election_cycle column
    has_election_cycle = "election_cycle" in df.columns

    if not has_election_cycle:
        issues.append("Missing election_cycle column")
        null_election_cycle = 0
        min_cycle = None
        max_cycle = None
    else:
        # Check for null election_cycle values
        null_count = df.filter(pl.col("election_cycle").is_null()).height
        null_election_cycle = null_count
        if null_count > 0:
            issues.append(f"{null_count:,} null election_cycle values")

        # Get cycle range
        cycles = df.select("election_cycle").unique().sort("election_cycle")
        if len(cycles) > 0:
            min_cycle = cycles.item(0, 0)
            max_cycle = cycles.item(-1, 0)
        else:
            min_cycle = None
            max_cycle = None

    # Check for reasonable row count
    if row_count == 0:
        issues.append("File is empty")

    return ValidationResult(
        file_name=file_path.name,
        row_count=row_count,
        column_count=column_count,
        has_election_cycle=has_election_cycle,
        null_election_cycle=null_election_cycle,
        min_cycle=min_cycle,
        max_cycle=max_cycle,
        issues=issues,
    )


def validate_transaction_amounts(file_path: Path) -> list[str]:
    """Validate transaction amounts in summarized files."""
    issues: list[str] = []

    try:
        df = pl.read_csv(file_path, infer_schema_length=10000, ignore_errors=True)
    except Exception:
        return ["Could not read file"]

    if "total_amount" not in df.columns:
        return []  # Not a summarized file

    # Check for extremely large amounts (potential data issues)
    extreme_threshold = 1_000_000_000_000  # $1 trillion
    extreme_count = df.filter(pl.col("total_amount").abs() > extreme_threshold).height
    if extreme_count > 0:
        issues.append(f"{extreme_count} rows with amounts > $1 trillion")

    # Check for reasonable transaction counts
    if "transaction_count" in df.columns:
        zero_count = df.filter(pl.col("transaction_count") <= 0).height
        if zero_count > 0:
            issues.append(f"{zero_count} rows with zero/negative transaction_count")

    return issues


def get_cycle_counts(file_path: Path) -> dict[int, int]:
    """Get row counts per election cycle."""
    try:
        df = pl.read_csv(file_path, infer_schema_length=10000, ignore_errors=True)
        if "election_cycle" not in df.columns:
            return {}

        counts = (
            df.group_by("election_cycle")
            .count()
            .sort("election_cycle")
        )

        return {row[0]: row[1] for row in counts.iter_rows()}
    except Exception:
        return {}


def verify_all(config: Config) -> list[ValidationResult]:
    """Verify all data files."""
    results: list[ValidationResult] = []

    console.print("\n[bold]Validating data files...[/bold]\n")

    # Validate combine datasets
    for name, dataset in config.combine_datasets.items():
        file_path = config.data_dir / dataset.output_file
        if file_path.exists():
            result = validate_file(file_path)
            results.append(result)
        else:
            results.append(
                ValidationResult(
                    file_name=dataset.output_file,
                    row_count=0,
                    column_count=0,
                    has_election_cycle=False,
                    null_election_cycle=0,
                    min_cycle=None,
                    max_cycle=None,
                    issues=["File not found"],
                )
            )

    # Validate summarize datasets
    for name, dataset in config.summarize_datasets.items():
        file_path = config.data_dir / dataset.output_file
        if file_path.exists():
            result = validate_file(file_path)
            # Additional validation for transaction files
            amount_issues = validate_transaction_amounts(file_path)
            result.issues.extend(amount_issues)
            results.append(result)
        else:
            results.append(
                ValidationResult(
                    file_name=dataset.output_file,
                    row_count=0,
                    column_count=0,
                    has_election_cycle=False,
                    null_election_cycle=0,
                    min_cycle=None,
                    max_cycle=None,
                    issues=["File not found"],
                )
            )

    return results


def print_verification_report(results: list[ValidationResult]) -> None:
    """Print a formatted verification report."""
    table = Table(title="Data Validation Report")
    table.add_column("File", style="cyan")
    table.add_column("Rows", justify="right")
    table.add_column("Columns", justify="right")
    table.add_column("Cycles", justify="center")
    table.add_column("Status", justify="center")

    for result in results:
        cycle_range = ""
        if result.min_cycle and result.max_cycle:
            cycle_range = f"{result.min_cycle}-{result.max_cycle}"

        status = "[green]✓[/green]" if result.is_valid else "[red]✗[/red]"

        table.add_row(
            result.file_name,
            f"{result.row_count:,}",
            str(result.column_count),
            cycle_range,
            status,
        )

    console.print(table)

    # Print issues
    has_issues = any(r.issues for r in results)
    if has_issues:
        console.print("\n[bold red]Issues found:[/bold red]")
        for result in results:
            for issue in result.issues:
                console.print(f"  • {result.file_name}: {issue}")
    else:
        console.print("\n[green]All validations passed![/green]")


def print_cycle_summary(config: Config) -> None:
    """Print row counts per cycle for all files."""
    console.print("\n[bold]Row counts by election cycle:[/bold]\n")

    for name, dataset in list(config.combine_datasets.items()) + list(config.summarize_datasets.items()):
        file_path = config.data_dir / dataset.output_file
        if not file_path.exists():
            continue

        counts = get_cycle_counts(file_path)
        if not counts:
            continue

        console.print(f"[cyan]{dataset.output_file}[/cyan]")
        # Show last 5 cycles
        recent_cycles = sorted(counts.keys())[-5:]
        for cycle in recent_cycles:
            console.print(f"  {cycle}: {counts[cycle]:,} rows")
        console.print()
