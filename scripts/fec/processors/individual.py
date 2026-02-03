"""Processors for individual contributions data."""

import asyncio
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

import polars as pl
from rich.console import Console

from ..utils.dates import extract_year_from_date, extract_month_from_date
from ..utils.io import atomic_write_csv, read_fec_csv, read_fec_pipe_delimited
from ..utils.names import capitalize_name
from ..utils.progress import create_download_progress, create_spinner_progress
from ..async_utils.download import download_with_retry

console = Console()

# Configuration
FEC_BASE_URL = "https://www.fec.gov/files/bulk-downloads"
ELECTION_CYCLES = list(range(1980, 2028, 2))  # 1980, 1982, ..., 2026

# Candidate committee types (House, Senate, Presidential)
CANDIDATE_COMMITTEE_TYPES = {"H", "S", "P"}


def get_fec_url(cycle: int) -> str:
    """Build FEC URL for individual contributions ZIP file."""
    year_suffix = str(cycle)[2:]
    return f"{FEC_BASE_URL}/{cycle}/indiv{year_suffix}.zip"


class IndividualDownloader:
    """Downloads and processes individual contributions from FEC."""

    def __init__(self, output_dir: Path, header_file: Path):
        self.output_dir = output_dir
        self.header_file = header_file

    def get_output_path(self, cycle: int) -> Path:
        """Get output CSV path for a cycle."""
        return self.output_dir / f"{cycle}_individual_contributions.csv"

    def load_headers(self) -> list[str]:
        """Load headers from header file."""
        with open(self.header_file) as f:
            raw_headers = f.read().strip().split(",")
        return [h.lower() for h in raw_headers]

    def process_zip(
        self, zip_path: Path, cycle: int, headers: list[str], output_path: Path
    ) -> bool:
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
                    # Read pipe-delimited file
                    df = pl.read_csv(
                        f,
                        separator="|",
                        has_header=False,
                        new_columns=headers,
                        infer_schema_length=10000,
                        ignore_errors=True,
                        quote_char=None,
                        truncate_ragged_lines=True,
                        encoding="utf8-lossy",
                    )

                    # Apply name capitalization to contributor name fields
                    name_columns = ["name", "employer", "occupation"]
                    for col in name_columns:
                        if col in df.columns:
                            df = df.with_columns(
                                pl.col(col)
                                .map_elements(capitalize_name, return_dtype=pl.Utf8)
                                .alias(col)
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

    async def download_cycle(self, cycle: int, headers: list[str], dry_run: bool) -> bool:
        """Download and process a single cycle."""
        import httpx

        output_path = self.get_output_path(cycle)

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
            with create_download_progress(console) as progress:
                with TemporaryDirectory() as tmpdir:
                    zip_path = Path(tmpdir) / f"indiv{str(cycle)[2:]}.zip"

                    success = await download_with_retry(client, url, zip_path, progress)
                    if not success:
                        return False

                    success = self.process_zip(zip_path, cycle, headers, output_path)
                    if success:
                        size_mb = output_path.stat().st_size / (1024 * 1024)
                        console.print(f"  [green]Wrote {output_path.name} ({size_mb:.1f} MB)[/green]")

                    return success

    def download_all(self, dry_run: bool = False, cycles: list[int] | None = None) -> tuple[int, int, int]:
        """Download all cycles.

        Returns:
            Tuple of (successful, skipped, failed)
        """
        if not self.header_file.exists():
            console.print(f"[red]Header file not found: {self.header_file}[/red]")
            raise SystemExit(1)

        headers = self.load_headers()
        console.print(f"Headers: {len(headers)} columns (+ election_cycle)\n")

        cycles_to_process = cycles or ELECTION_CYCLES
        successful = 0
        failed = 0
        skipped = 0

        for cycle in cycles_to_process:
            output_path = self.get_output_path(cycle)
            if output_path.exists():
                skipped += 1
                console.print(f"[dim]{cycle}: Already exists, skipping[/dim]")
                continue

            success = asyncio.run(self.download_cycle(cycle, headers, dry_run))
            if success:
                successful += 1
            else:
                failed += 1

        return successful, skipped, failed


class TransactionYearAdder:
    """Adds transaction_year column to individual contribution files."""

    def __init__(self, input_dir: Path):
        self.input_dir = input_dir

    def process_file(self, input_file: Path, dry_run: bool = False, force: bool = False) -> int:
        """Add transaction_year column to a CSV file.

        Args:
            input_file: Path to the individual contributions CSV
            dry_run: If True, don't write changes
            force: If True, recompute even if column exists

        Returns:
            Number of rows processed
        """
        console.print(f"Processing {input_file.name}...")

        with create_spinner_progress(console) as progress:
            task = progress.add_task("Reading file...", total=None)

            # Read the CSV
            df = read_fec_csv(input_file)

            # Check if transaction_year already exists
            if "transaction_year" in df.columns and not force:
                console.print(f"  [yellow]Skipping: transaction_year column already exists (use --force to recompute)[/yellow]")
                return len(df)

            # Drop existing column if force recompute
            if "transaction_year" in df.columns:
                df = df.drop("transaction_year")

            progress.update(task, description="Extracting transaction year...")

            # Extract year from transaction_dt
            df = df.with_columns(
                pl.col("transaction_dt")
                .cast(pl.Utf8)
                .map_elements(extract_year_from_date, return_dtype=pl.Int64)
                .alias("transaction_year")
            )

            # Reorder columns: election_cycle, transaction_year, then the rest
            cols = df.columns
            cols.remove("transaction_year")
            new_order = [cols[0], "transaction_year"] + cols[1:]
            df = df.select(new_order)

            row_count = len(df)

            if dry_run:
                console.print(f"  [dim]Would write {row_count:,} rows[/dim]")
                console.print(f"  Sample columns: {df.columns[:5]}")
                return row_count

            progress.update(task, description="Writing file...")

            # Write atomically
            atomic_write_csv(df, input_file)

            progress.update(task, description="Done")

        console.print(f"  → {row_count:,} rows written")
        return row_count

    def process_all(
        self, cycle: int | None = None, dry_run: bool = False, force: bool = False
    ) -> int:
        """Process all individual contribution files.

        Args:
            cycle: If provided, process only this cycle
            dry_run: If True, don't write changes
            force: If True, recompute even if column exists

        Returns:
            Total rows processed
        """
        if cycle:
            files = [self.input_dir / f"{cycle}_individual_contributions.csv"]
            if not files[0].exists():
                console.print(f"[red]Error: File not found: {files[0]}[/red]")
                raise SystemExit(1)
        else:
            files = sorted(self.input_dir.glob("*_individual_contributions.csv"))

        if not files:
            console.print("[yellow]No individual contribution files found[/yellow]")
            return 0

        console.print(f"Found {len(files)} file(s) to process\n")

        total_rows = 0
        for file_path in files:
            rows = self.process_file(file_path, dry_run=dry_run, force=force)
            total_rows += rows

        return total_rows


class IndividualSummarizer:
    """Aggregates individual contributions by candidate."""

    def __init__(self, data_dir: Path, individual_dir: Path, output_file: Path):
        self.data_dir = data_dir
        self.individual_dir = individual_dir
        self.output_file = output_file

    def normalize_name(self, name: str | None) -> str:
        """Normalize candidate name for matching."""
        import re

        if not name:
            return ""

        name = name.upper().strip()

        if "," in name:
            parts = name.split(",", 1)
            lastname = parts[0].strip()
            lastname = re.sub(r"[.']", "", lastname)
            if len(parts) > 1:
                firstname_part = parts[1].strip()
                firstname_part = re.sub(r"[.']", "", firstname_part)
                firstname_parts = firstname_part.split()
                firstname = firstname_parts[0] if firstname_parts else ""
                if firstname in ["JR", "SR", "II", "III", "IV"]:
                    firstname = firstname_parts[1] if len(firstname_parts) > 1 else ""
                result = f"{lastname}, {firstname}"
                for suffix in [" JR", " SR", " II", " III", " IV"]:
                    if result.endswith(suffix):
                        result = result[:-len(suffix)]
                return result.strip()
            return lastname

        name = re.sub(r"[.,']", "", name)
        name = re.sub(r"\s+", " ", name).strip()
        return name

    def load_bioguide_crosswalk(self, crosswalk_file: Path, candidate_file: Path) -> pl.DataFrame:
        """Load and expand bioguide crosswalk via name matching."""
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

        candidates = pl.read_csv(
            candidate_file,
            columns=["cand_id", "cand_name"],
            infer_schema_length=10000,
        ).unique(subset=["cand_id"])

        candidates = candidates.with_columns(
            pl.col("cand_name")
            .map_elements(self.normalize_name, return_dtype=pl.Utf8)
            .alias("norm_name")
        )

        crosswalk_with_names = crosswalk.join(
            candidates.select(["cand_id", "norm_name"]),
            on="cand_id",
            how="left"
        )

        name_to_bioguide = (
            crosswalk_with_names
            .filter(pl.col("norm_name").is_not_null() & (pl.col("norm_name") != ""))
            .select(["norm_name", "bioguide_id"])
            .unique()
        )

        expanded = (
            candidates
            .join(name_to_bioguide, on="norm_name", how="inner")
            .select(["cand_id", "bioguide_id"])
            .unique()
        )

        console.print(f"  → {len(expanded):,} expanded candidate-bioguide mappings")
        return expanded

    def load_committee_lookup(self, committee_file: Path) -> pl.DataFrame:
        """Load committee-to-candidate lookup."""
        console.print("Loading committee registrations...")

        df = pl.read_csv(
            committee_file,
            columns=["election_cycle", "cmte_id", "cmte_tp", "cand_id"],
            infer_schema_length=10000,
            ignore_errors=True,
        )

        df = df.filter(
            (pl.col("cmte_tp").is_in(CANDIDATE_COMMITTEE_TYPES))
            & (pl.col("cand_id").is_not_null())
            & (pl.col("cand_id") != "")
        )

        df = df.select(["election_cycle", "cmte_id", "cand_id"]).unique()

        console.print(f"  → {len(df):,} committee-candidate mappings")
        return df

    def process_cycle(
        self, input_file: Path, cycle: int, committee_lookup: pl.DataFrame
    ) -> pl.DataFrame:
        """Process a single cycle's contributions."""
        console.print(f"Processing {input_file.name}...")

        with create_spinner_progress(console) as progress:
            task = progress.add_task("Reading file...", total=None)

            cycle_lookup = committee_lookup.filter(pl.col("election_cycle") == cycle)

            if len(cycle_lookup) == 0:
                console.print(f"  [yellow]No candidate committees for cycle {cycle}[/yellow]")
                return pl.DataFrame()

            df = pl.scan_csv(
                input_file,
                infer_schema_length=10000,
                ignore_errors=True,
                encoding="utf8-lossy",
            )

            progress.update(task, description="Filtering memos and amendments...")

            df = df.filter(
                (pl.col("memo_cd").is_null()) | (pl.col("memo_cd") != "X")
            )

            df = df.filter(
                (pl.col("amndt_ind").is_null()) | (pl.col("amndt_ind") == "N")
            )

            df = df.unique(subset=["sub_id"], keep="first")

            progress.update(task, description="Joining with committee lookup...")

            df = df.select([
                "election_cycle",
                "cmte_id",
                "transaction_dt",
                "transaction_amt",
            ])

            df = df.collect()

            df = df.join(
                cycle_lookup.select(["cmte_id", "cand_id"]),
                on="cmte_id",
                how="inner",
            )

            if len(df) == 0:
                console.print(f"  [yellow]No matching contributions for cycle {cycle}[/yellow]")
                return pl.DataFrame()

            progress.update(task, description="Extracting dates...")

            df = df.with_columns(
                pl.col("transaction_dt")
                .cast(pl.Utf8)
                .map_elements(extract_year_from_date, return_dtype=pl.Int64)
                .alias("transaction_year")
            )

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

            result = (
                df.group_by(group_cols)
                .agg(
                    pl.col("transaction_amt").sum().alias("total_raised"),
                    pl.len().alias("transaction_count"),
                )
            )

            if cycle != 2026:
                result = result.with_columns(pl.lit(None).cast(pl.Int64).alias("transaction_month"))

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

    def summarize_all(self, cycle: int | None = None, dry_run: bool = False) -> None:
        """Aggregate all individual contributions by candidate."""
        committee_file = self.data_dir / "committee_registrations_1980-2026.csv"
        if not committee_file.exists():
            console.print(f"[red]Error: Committee file not found: {committee_file}[/red]")
            raise SystemExit(1)

        committee_lookup = self.load_committee_lookup(committee_file)

        bioguide_file = self.data_dir / "cand_id_bioguide_crosswalk.csv"
        candidate_file = self.data_dir / "candidate_registrations_1980-2026.csv"
        bioguide_lookup = self.load_bioguide_crosswalk(bioguide_file, candidate_file)

        if cycle:
            files = [(cycle, self.individual_dir / f"{cycle}_individual_contributions.csv")]
            if not files[0][1].exists():
                console.print(f"[red]Error: File not found: {files[0][1]}[/red]")
                raise SystemExit(1)
        else:
            files = []
            for f in sorted(self.individual_dir.glob("*_individual_contributions.csv")):
                c = int(f.stem.split("_")[0])
                files.append((c, f))

        if not files:
            console.print("[yellow]No individual contribution files found[/yellow]")
            return

        console.print(f"\nFound {len(files)} file(s) to process\n")

        all_results = []
        for c, file_path in files:
            result = self.process_cycle(file_path, c, committee_lookup)
            if len(result) > 0:
                all_results.append(result)

        if not all_results:
            console.print("[yellow]No results to write[/yellow]")
            return

        console.print("\nCombining results...")
        combined = pl.concat(all_results)

        if len(bioguide_lookup) > 0:
            console.print("Joining with bioguide crosswalk...")
            combined = combined.join(bioguide_lookup, on="cand_id", how="left")
        else:
            combined = combined.with_columns(pl.lit(None).cast(pl.Utf8).alias("bioguide_id"))

        combined = combined.select([
            "election_cycle",
            "transaction_year",
            "transaction_month",
            "cand_id",
            "bioguide_id",
            "total_raised",
            "transaction_count",
        ])

        combined = combined.sort(["election_cycle", "transaction_year", "transaction_month", "cand_id"])

        console.print(f"  → {len(combined):,} total rows")

        if dry_run:
            console.print(f"\n[dim]Would write to {self.output_file}[/dim]")
            console.print("\nSample output:")
            console.print(combined.head(10))
            return

        console.print(f"\nWriting to {self.output_file}...")
        atomic_write_csv(combined, self.output_file)

        console.print(f"[green]Done![/green] Wrote {len(combined):,} rows to {self.output_file.name}")
