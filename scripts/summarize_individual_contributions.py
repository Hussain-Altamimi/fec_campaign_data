#!/usr/bin/env python3
"""Aggregate individual contributions by candidate.

Creates a summary file with total contributions and counts per candidate,
grouped by election cycle and transaction year (plus month for 2026).

Data flow:
  individual_contributions (cmte_id)
      ↓ join on cmte_id + election_cycle
  committee_registrations (cand_id)
      ↓ group by cand_id
  candidate_individual_contribution_summaries (output)

Only candidate committees (H, S, P types) have a cand_id.
PAC/party contributions won't appear in the candidate summary.
"""

import argparse
import sys
from pathlib import Path

import polars as pl
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

console = Console()

DATA_DIR = Path(__file__).parent.parent / "data"
INDIVIDUAL_CONTRIBUTIONS_DIR = Path(__file__).parent.parent / "individual_contributions"
OUTPUT_FILE = DATA_DIR / "candidate_individual_contribution_summaries_1980-2026.csv"

# Candidate committee types (House, Senate, Presidential)
CANDIDATE_COMMITTEE_TYPES = {"H", "S", "P"}


def extract_year_from_date(date_str: str | None) -> int | None:
    """Extract year from FEC date string (MMDDYYYY, MDDYYYY, or MM/DD/YYYY format)."""
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()
    if not date_str:
        return None

    # Handle MM/DD/YYYY format
    if "/" in date_str:
        parts = date_str.split("/")
        if len(parts) == 3 and len(parts[2]) == 4:
            try:
                return int(parts[2])
            except ValueError:
                return None

    # Handle MMDDYYYY format (8 chars) - year is last 4
    if len(date_str) == 8:
        try:
            return int(date_str[4:8])
        except ValueError:
            return None

    # Handle MDDYYYY format (7 chars) - year is last 4
    if len(date_str) == 7:
        try:
            return int(date_str[3:7])
        except ValueError:
            return None

    return None


def extract_month_from_date(date_str: str | None) -> int | None:
    """Extract month from FEC date string (MMDDYYYY, MDDYYYY, or MM/DD/YYYY format)."""
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()
    if not date_str:
        return None

    # Handle MM/DD/YYYY format
    if "/" in date_str:
        parts = date_str.split("/")
        if len(parts) == 3 and len(parts[0]) in (1, 2):
            try:
                return int(parts[0])
            except ValueError:
                return None

    # Handle MMDDYYYY format (8 chars) - month is first 2
    if len(date_str) == 8:
        try:
            return int(date_str[0:2])
        except ValueError:
            return None

    # Handle MDDYYYY format (7 chars) - month is first 1
    if len(date_str) == 7:
        try:
            return int(date_str[0:1])
        except ValueError:
            return None

    return None


def normalize_name(name: str | None) -> str:
    """Normalize candidate name for matching.

    Extracts just LASTNAME, FIRSTNAME to handle middle name/initial variations.
    """
    if not name:
        return ""
    import re

    name = name.upper().strip()

    # Extract LASTNAME, FIRSTNAME only (ignore middle name/initial)
    # Format is typically "LASTNAME, FIRSTNAME [MIDDLE]"
    if "," in name:
        parts = name.split(",", 1)
        lastname = parts[0].strip()
        # Remove punctuation from lastname
        lastname = re.sub(r"[.']", "", lastname)
        if len(parts) > 1:
            # Get just the first name (first word after comma)
            firstname_part = parts[1].strip()
            # Remove punctuation
            firstname_part = re.sub(r"[.']", "", firstname_part)
            firstname_parts = firstname_part.split()
            firstname = firstname_parts[0] if firstname_parts else ""
            # Remove suffixes from firstname if it's a suffix
            if firstname in ["JR", "SR", "II", "III", "IV"]:
                firstname = firstname_parts[1] if len(firstname_parts) > 1 else ""
            result = f"{lastname}, {firstname}"
            # Remove trailing suffix from result
            for suffix in [" JR", " SR", " II", " III", " IV"]:
                if result.endswith(suffix):
                    result = result[:-len(suffix)]
            return result.strip()
        return lastname

    # No comma - just normalize
    name = re.sub(r"[.,']", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def load_bioguide_crosswalk(crosswalk_file: Path, candidate_file: Path) -> pl.DataFrame:
    """Load FEC candidate ID to Bioguide ID crosswalk, expanded by name matching.

    The original crosswalk only links Congressional candidate IDs to bioguide.
    This function expands it by finding other candidate IDs (e.g., presidential)
    that belong to the same person based on name matching.
    """
    if not crosswalk_file.exists():
        console.print(f"[yellow]Warning: Bioguide crosswalk not found: {crosswalk_file}[/yellow]")
        return pl.DataFrame({"cand_id": [], "bioguide_id": []})

    console.print("Loading bioguide crosswalk...")
    crosswalk = pl.read_csv(
        crosswalk_file,
        columns=["cand_id", "bioguide_id"],
        infer_schema_length=10000,
    )
    console.print(f"  → {len(crosswalk):,} direct candidate-bioguide mappings")

    if not candidate_file.exists():
        return crosswalk

    console.print("Expanding crosswalk via name matching...")

    # Load candidate names
    candidates = pl.read_csv(
        candidate_file,
        columns=["cand_id", "cand_name"],
        infer_schema_length=10000,
    ).unique(subset=["cand_id"])

    # Add normalized names
    candidates = candidates.with_columns(
        pl.col("cand_name")
        .map_elements(normalize_name, return_dtype=pl.Utf8)
        .alias("norm_name")
    )

    # Get names for candidates in crosswalk
    crosswalk_with_names = crosswalk.join(
        candidates.select(["cand_id", "norm_name"]),
        on="cand_id",
        how="left"
    )

    # Find all candidate IDs that share a normalized name with someone in crosswalk
    # Create name -> bioguide mapping
    name_to_bioguide = (
        crosswalk_with_names
        .filter(pl.col("norm_name").is_not_null() & (pl.col("norm_name") != ""))
        .select(["norm_name", "bioguide_id"])
        .unique()
    )

    # Join candidates with name_to_bioguide to expand mappings
    expanded = (
        candidates
        .join(name_to_bioguide, on="norm_name", how="inner")
        .select(["cand_id", "bioguide_id"])
        .unique()
    )

    console.print(f"  → {len(expanded):,} expanded candidate-bioguide mappings (via name matching)")
    return expanded


def load_committee_to_candidate_lookup(committee_file: Path) -> pl.DataFrame:
    """Load committee registrations and create cmte_id -> cand_id lookup.

    Only includes candidate committees (H, S, P types) with valid cand_id.
    """
    console.print("Loading committee registrations...")

    df = pl.read_csv(
        committee_file,
        columns=["election_cycle", "cmte_id", "cmte_tp", "cand_id"],
        infer_schema_length=10000,
        ignore_errors=True,
    )

    # Filter to candidate committees with valid cand_id
    df = df.filter(
        (pl.col("cmte_tp").is_in(CANDIDATE_COMMITTEE_TYPES))
        & (pl.col("cand_id").is_not_null())
        & (pl.col("cand_id") != "")
    )

    # Keep unique cmte_id + election_cycle combinations
    # (a committee might change candidate affiliation across cycles)
    df = df.select(["election_cycle", "cmte_id", "cand_id"]).unique()

    console.print(f"  → {len(df):,} committee-candidate mappings")
    return df


def process_cycle(
    input_file: Path,
    cycle: int,
    committee_lookup: pl.DataFrame,
) -> pl.DataFrame:
    """Process a single cycle's individual contributions.

    Args:
        input_file: Path to the individual contributions CSV
        cycle: Election cycle year
        committee_lookup: DataFrame with cmte_id -> cand_id mapping

    Returns:
        Aggregated DataFrame with candidate contribution summaries
    """
    console.print(f"Processing {input_file.name}...")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Reading file...", total=None)

        # Filter committee lookup to this cycle
        cycle_lookup = committee_lookup.filter(pl.col("election_cycle") == cycle)

        if len(cycle_lookup) == 0:
            console.print(f"  [yellow]No candidate committees for cycle {cycle}[/yellow]")
            return pl.DataFrame()

        # Read with lazy evaluation for memory efficiency
        df = pl.scan_csv(
            input_file,
            infer_schema_length=10000,
            ignore_errors=True,
            encoding="utf8-lossy",
        )

        progress.update(task, description="Filtering memos and amendments...")

        # Filter out memo transactions (memo_cd = 'X')
        df = df.filter(
            (pl.col("memo_cd").is_null()) | (pl.col("memo_cd") != "X")
        )

        # Filter out amendments (amndt_ind != 'N')
        df = df.filter(
            (pl.col("amndt_ind").is_null()) | (pl.col("amndt_ind") == "N")
        )

        # Deduplicate by sub_id
        df = df.unique(subset=["sub_id"], keep="first")

        progress.update(task, description="Joining with committee lookup...")

        # Select only needed columns before join
        df = df.select([
            "election_cycle",
            "cmte_id",
            "transaction_dt",
            "transaction_amt",
        ])

        # Collect for join (necessary for cross-dataframe join)
        df = df.collect()

        # Join to get cand_id
        df = df.join(
            cycle_lookup.select(["cmte_id", "cand_id"]),
            on="cmte_id",
            how="inner",
        )

        if len(df) == 0:
            console.print(f"  [yellow]No matching contributions for cycle {cycle}[/yellow]")
            return pl.DataFrame()

        progress.update(task, description="Extracting dates...")

        # Extract transaction_year from transaction_dt
        df = df.with_columns(
            pl.col("transaction_dt")
            .cast(pl.Utf8)
            .map_elements(extract_year_from_date, return_dtype=pl.Int64)
            .alias("transaction_year")
        )

        # For 2026, also extract month
        if cycle == 2026:
            df = df.with_columns(
                pl.col("transaction_dt")
                .cast(pl.Utf8)
                .map_elements(extract_month_from_date, return_dtype=pl.Int64)
                .alias("transaction_month")
            )
            group_cols = ["election_cycle", "cand_id", "transaction_year", "transaction_month"]
        else:
            group_cols = ["election_cycle", "cand_id", "transaction_year"]

        progress.update(task, description="Aggregating...")

        # Group and aggregate
        result = (
            df.group_by(group_cols)
            .agg(
                pl.col("transaction_amt").sum().alias("total_raised"),
                pl.len().alias("transaction_count"),
            )
        )

        # For non-2026 cycles, add NULL transaction_month column
        if cycle != 2026:
            result = result.with_columns(pl.lit(None).cast(pl.Int64).alias("transaction_month"))

        # Ensure consistent column order: cycle, year, month, then cand_id
        result = result.select([
            "election_cycle",
            "transaction_year",
            "transaction_month",
            "cand_id",
            "total_raised",
            "transaction_count",
        ])

        progress.update(task, description="Done")

    console.print(f"  → {len(result):,} candidate-year groups")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate individual contributions by candidate"
    )
    parser.add_argument(
        "--cycle",
        type=int,
        help="Process only this election cycle (e.g., 2020)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing output",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_FILE,
        help="Output file path",
    )
    args = parser.parse_args()

    # Load committee lookup
    committee_file = DATA_DIR / "committee_registrations_1980-2026.csv"
    if not committee_file.exists():
        console.print(f"[red]Error: Committee file not found: {committee_file}[/red]")
        sys.exit(1)

    committee_lookup = load_committee_to_candidate_lookup(committee_file)

    # Load bioguide crosswalk (expanded via name matching)
    bioguide_file = DATA_DIR / "cand_id_bioguide_crosswalk.csv"
    candidate_file = DATA_DIR / "candidate_registrations_1980-2026.csv"
    bioguide_lookup = load_bioguide_crosswalk(bioguide_file, candidate_file)

    # Find files to process
    if args.cycle:
        files = [(args.cycle, INDIVIDUAL_CONTRIBUTIONS_DIR / f"{args.cycle}_individual_contributions.csv")]
        if not files[0][1].exists():
            console.print(f"[red]Error: File not found: {files[0][1]}[/red]")
            sys.exit(1)
    else:
        files = []
        for f in sorted(INDIVIDUAL_CONTRIBUTIONS_DIR.glob("*_individual_contributions.csv")):
            cycle = int(f.stem.split("_")[0])
            files.append((cycle, f))

    if not files:
        console.print("[yellow]No individual contribution files found[/yellow]")
        sys.exit(0)

    console.print(f"\nFound {len(files)} file(s) to process\n")

    # Process each cycle
    all_results = []
    for cycle, file_path in files:
        try:
            result = process_cycle(file_path, cycle, committee_lookup)
            if len(result) > 0:
                all_results.append(result)
        except Exception as e:
            console.print(f"[red]Error processing {file_path.name}: {e}[/red]")
            raise

    if not all_results:
        console.print("[yellow]No results to write[/yellow]")
        sys.exit(0)

    # Combine all results
    console.print("\nCombining results...")
    combined = pl.concat(all_results)

    # Join with bioguide crosswalk
    if len(bioguide_lookup) > 0:
        console.print("Joining with bioguide crosswalk...")
        combined = combined.join(bioguide_lookup, on="cand_id", how="left")
    else:
        combined = combined.with_columns(pl.lit(None).cast(pl.Utf8).alias("bioguide_id"))

    # Reorder columns: cycle, year, month, cand_id, bioguide_id, totals
    combined = combined.select([
        "election_cycle",
        "transaction_year",
        "transaction_month",
        "cand_id",
        "bioguide_id",
        "total_raised",
        "transaction_count",
    ])

    # Sort by election_cycle, transaction_year, transaction_month, cand_id
    combined = combined.sort(["election_cycle", "transaction_year", "transaction_month", "cand_id"])

    console.print(f"  → {len(combined):,} total rows")

    if args.dry_run:
        console.print(f"\n[dim]Would write to {args.output}[/dim]")
        console.print("\nSample output:")
        console.print(combined.head(10))
        return

    # Write output atomically
    console.print(f"\nWriting to {args.output}...")
    temp_path = args.output.with_suffix(".csv.tmp")
    combined.write_csv(temp_path)
    temp_path.rename(args.output)

    console.print(f"[green]Done![/green] Wrote {len(combined):,} rows to {args.output.name}")


if __name__ == "__main__":
    main()
