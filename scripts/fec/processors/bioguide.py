"""Processor for creating bioguide crosswalk."""

import csv
import ssl
import urllib.request
from pathlib import Path

from rich.console import Console

console = Console()

# Congressional Legislators data URLs
CURRENT_LEGISLATORS_URL = "https://raw.githubusercontent.com/unitedstates/congress-legislators/main/legislators-current.yaml"
HISTORICAL_LEGISLATORS_URL = "https://raw.githubusercontent.com/unitedstates/congress-legislators/main/legislators-historical.yaml"


class BioguideProcessor:
    """Creates FEC candidate ID to Bioguide ID crosswalk."""

    def __init__(self, data_dir: Path, output_file: Path):
        self.data_dir = data_dir
        self.output_file = output_file

    def fetch_yaml(self, url: str) -> str:
        """Fetch YAML data from URL."""
        context = ssl.create_default_context()
        with urllib.request.urlopen(url, context=context) as response:
            return response.read().decode("utf-8")

    def parse_yaml_simple(self, content: str) -> list[dict]:
        """Simple YAML parser for congress-legislators format."""
        legislators = []
        current_legislator = None
        current_key = None
        in_id_block = False
        in_fec_list = False

        for line in content.split("\n"):
            # New legislator entry
            if line.startswith("- id:"):
                if current_legislator:
                    legislators.append(current_legislator)
                current_legislator = {"id": {}, "name": {}}
                in_id_block = True
                in_fec_list = False
                continue

            if current_legislator is None:
                continue

            stripped = line.strip()

            # ID block entries
            if in_id_block:
                if stripped.startswith("bioguide:"):
                    current_legislator["id"]["bioguide"] = stripped.split(":", 1)[1].strip()
                elif stripped.startswith("fec:"):
                    in_fec_list = True
                    current_legislator["id"]["fec"] = []
                elif in_fec_list and stripped.startswith("- "):
                    fec_id = stripped[2:].strip()
                    if fec_id:
                        current_legislator["id"]["fec"].append(fec_id)
                elif stripped.startswith("name:"):
                    in_id_block = False
                    in_fec_list = False
                    current_key = "name"
                elif not stripped.startswith("-") and ":" in stripped and not stripped.startswith("  "):
                    in_fec_list = False

            # Name block
            if not in_id_block and stripped.startswith("first:"):
                current_legislator["name"]["first"] = stripped.split(":", 1)[1].strip()
            elif not in_id_block and stripped.startswith("last:"):
                current_legislator["name"]["last"] = stripped.split(":", 1)[1].strip()

        if current_legislator:
            legislators.append(current_legislator)

        return legislators

    def validate_fec_ids(self, crosswalk: list[dict], candidate_file: Path) -> list[dict]:
        """Validate FEC IDs against candidate registrations."""
        if not candidate_file.exists():
            console.print(f"[yellow]Warning: Cannot validate - candidate file not found[/yellow]")
            return crosswalk

        console.print("Validating FEC IDs against candidate registrations...")

        # Load valid FEC candidate IDs
        valid_ids = set()
        with open(candidate_file, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "cand_id" in row:
                    valid_ids.add(row["cand_id"])

        validated = []
        invalid_count = 0
        for entry in crosswalk:
            if entry["cand_id"] in valid_ids:
                validated.append(entry)
            else:
                invalid_count += 1

        console.print(f"  → {len(validated):,} valid IDs, {invalid_count:,} invalid IDs removed")
        return validated

    def create_crosswalk(self, dry_run: bool = False) -> None:
        """Create the bioguide crosswalk file."""
        console.print("[bold]Creating FEC-Bioguide Crosswalk[/bold]\n")

        # Fetch legislator data
        console.print("Fetching current legislators...")
        current_yaml = self.fetch_yaml(CURRENT_LEGISLATORS_URL)
        console.print("Fetching historical legislators...")
        historical_yaml = self.fetch_yaml(HISTORICAL_LEGISLATORS_URL)

        # Try to use PyYAML if available, otherwise use simple parser
        try:
            import yaml
            current = yaml.safe_load(current_yaml)
            historical = yaml.safe_load(historical_yaml)
        except ImportError:
            console.print("[dim]PyYAML not available, using simple parser[/dim]")
            current = self.parse_yaml_simple(current_yaml)
            historical = self.parse_yaml_simple(historical_yaml)

        # Combine and extract FEC-bioguide mappings
        crosswalk = []
        legislators = current + historical

        for leg in legislators:
            bioguide = leg.get("id", {}).get("bioguide")
            fec_ids = leg.get("id", {}).get("fec", [])

            if not bioguide or not fec_ids:
                continue

            for fec_id in fec_ids:
                crosswalk.append({
                    "cand_id": fec_id,
                    "bioguide_id": bioguide,
                    "match_method": "direct",
                    "confidence": "high",
                })

        console.print(f"  → {len(crosswalk):,} FEC-Bioguide mappings found")

        # Validate against candidate registrations
        candidate_file = self.data_dir / "candidate_registrations_1980-2026.csv"
        crosswalk = self.validate_fec_ids(crosswalk, candidate_file)

        # Remove duplicates
        seen = set()
        unique_crosswalk = []
        for entry in crosswalk:
            key = (entry["cand_id"], entry["bioguide_id"])
            if key not in seen:
                seen.add(key)
                unique_crosswalk.append(entry)

        crosswalk = unique_crosswalk
        console.print(f"  → {len(crosswalk):,} unique mappings")

        # Check for bioguide IDs with multiple FEC IDs
        bioguide_counts = {}
        for entry in crosswalk:
            bg = entry["bioguide_id"]
            bioguide_counts[bg] = bioguide_counts.get(bg, 0) + 1

        multi_fec = sum(1 for count in bioguide_counts.values() if count > 1)
        console.print(f"  → {multi_fec:,} bioguide IDs map to multiple FEC candidate IDs")

        if dry_run:
            console.print(f"\n[dim]Would write {len(crosswalk):,} rows to {self.output_file}[/dim]")
            console.print("\nSample output:")
            for entry in crosswalk[:5]:
                console.print(f"  {entry['cand_id']} → {entry['bioguide_id']}")
            return

        # Write output
        console.print(f"\nWriting to {self.output_file}...")
        with open(self.output_file, "w", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["cand_id", "bioguide_id", "match_method", "confidence"]
            )
            writer.writeheader()
            writer.writerows(crosswalk)

        console.print(f"[green]Done![/green] Wrote {len(crosswalk):,} rows to {self.output_file.name}")

        # Verification
        known_members = [
            ("P80000722", "P000197"),  # Nancy Pelosi
            ("S2KY00012", "M000355"),  # Mitch McConnell
        ]

        console.print("\nVerification:")
        mapping = {e["cand_id"]: e["bioguide_id"] for e in crosswalk}
        for fec_id, bioguide in known_members:
            if fec_id in mapping:
                status = "[green]✓[/green]" if mapping[fec_id] == bioguide else "[red]✗[/red]"
                console.print(f"  {status} {fec_id} → {mapping[fec_id]}")
            else:
                console.print(f"  [yellow]?[/yellow] {fec_id} not found")
