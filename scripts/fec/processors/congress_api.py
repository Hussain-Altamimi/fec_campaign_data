"""Processor for fetching member data from Congress.gov API and GitHub."""

import json
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()

# GitHub raw URLs for congress-legislators data
CURRENT_LEGISLATORS_URL = "https://raw.githubusercontent.com/unitedstates/congress-legislators/main/legislators-current.yaml"
HISTORICAL_LEGISLATORS_URL = "https://raw.githubusercontent.com/unitedstates/congress-legislators/main/legislators-historical.yaml"


def _get_ssl_context() -> ssl.SSLContext:
    """Get SSL context, using certifi if available for better compatibility."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


class CongressAPIProcessor:
    """Fetches member data from unitedstates/congress-legislators GitHub repo."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_file = output_dir / "bioguide_ids" / "congress_api_members.json"

    def _fetch_url(self, url: str, max_retries: int = 5) -> str:
        """Fetch content from URL with retry logic."""
        context = _get_ssl_context()
        headers = {"User-Agent": "Mozilla/5.0 (compatible; FEC-Data-Tools/1.0)"}

        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, context=context, timeout=60) as response:
                    return response.read().decode("utf-8")
            except urllib.error.HTTPError as e:
                if e.code in (429, 503):
                    wait_time = 2 ** attempt
                    console.print(f"[yellow]HTTP {e.code}. Waiting {wait_time}s...[/yellow]")
                    time.sleep(wait_time)
                    continue
                raise
            except urllib.error.URLError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    console.print(f"[yellow]Connection error. Retrying in {wait_time}s...[/yellow]")
                    time.sleep(wait_time)
                    continue
                raise

        raise RuntimeError(f"Failed to fetch {url} after {max_retries} attempts")

    def _parse_legislators_yaml(self, content: str) -> list[dict]:
        """Parse congress-legislators YAML format into member records."""
        members = []
        current_member = None
        in_id_block = False
        in_fec_list = False
        in_name_block = False
        in_bio_block = False
        in_terms_block = False
        in_term_item = False
        current_term = None

        # ID fields to capture (simple key: value pairs)
        id_fields = [
            "bioguide", "thomas", "lis", "govtrack", "opensecrets",
            "votesmart", "cspan", "wikipedia", "house_history",
            "ballotpedia", "maplight", "icpsr", "wikidata", "google_entity_id",
        ]

        for line in content.split("\n"):
            # New legislator entry
            if line.startswith("- id:"):
                # Save the last term for the previous member
                if current_term and current_member:
                    current_member["terms"].append(current_term)
                    current_term = None
                if current_member:
                    members.append(current_member)
                current_member = {
                    "id": {},
                    "name": {},
                    "bio": {},
                    "terms": [],
                }
                in_id_block = True
                in_fec_list = False
                in_name_block = False
                in_bio_block = False
                in_terms_block = False
                in_term_item = False
                continue

            if current_member is None:
                continue

            stripped = line.strip()

            # Detect block transitions
            if line.startswith("  name:"):
                in_id_block = False
                in_fec_list = False
                in_name_block = True
                in_bio_block = False
                in_terms_block = False
                continue
            elif line.startswith("  bio:"):
                in_id_block = False
                in_fec_list = False
                in_name_block = False
                in_bio_block = True
                in_terms_block = False
                continue
            elif line.startswith("  terms:"):
                in_id_block = False
                in_fec_list = False
                in_name_block = False
                in_bio_block = False
                in_terms_block = True
                in_term_item = False
                continue

            # Parse ID block
            if in_id_block:
                # Handle fec: which starts a list
                if stripped.startswith("fec:"):
                    in_fec_list = True
                    current_member["id"]["fec"] = []
                    # Check if there's a value on the same line (single FEC ID)
                    value = stripped.split(":", 1)[1].strip()
                    if value:
                        current_member["id"]["fec"].append(value)
                        in_fec_list = False
                    continue
                # Handle FEC list items
                if in_fec_list:
                    if stripped.startswith("- "):
                        fec_id = stripped[2:].strip()
                        if fec_id:
                            current_member["id"]["fec"].append(fec_id)
                        continue
                    else:
                        in_fec_list = False
                # Handle other ID fields
                for field in id_fields:
                    if stripped.startswith(f"{field}:"):
                        value = stripped.split(":", 1)[1].strip().strip("'\"")
                        if value:
                            current_member["id"][field] = value
                        break

            # Parse name block
            if in_name_block:
                for field in ["first", "last", "middle", "suffix", "nickname", "official_full"]:
                    if stripped.startswith(f"{field}:"):
                        value = stripped.split(":", 1)[1].strip()
                        if value:
                            current_member["name"][field] = value
                        break

            # Parse bio block
            if in_bio_block:
                if stripped.startswith("gender:"):
                    current_member["bio"]["gender"] = stripped.split(":", 1)[1].strip()
                elif stripped.startswith("birthday:"):
                    current_member["bio"]["birthday"] = stripped.split(":", 1)[1].strip().strip("'\"")
                elif stripped.startswith("religion:"):
                    current_member["bio"]["religion"] = stripped.split(":", 1)[1].strip()

            # Parse terms block
            if in_terms_block:
                if stripped.startswith("- type:"):
                    # Save previous term
                    if current_term:
                        current_member["terms"].append(current_term)
                    term_type = stripped.split(":", 1)[1].strip()
                    current_term = {"type": term_type}
                    in_term_item = True
                elif in_term_item:
                    # Term fields to capture
                    term_fields = [
                        "start", "end", "state", "district", "party", "class",
                        "state_rank", "url", "address", "phone", "fax",
                        "contact_form", "office", "rss_url", "how",
                    ]
                    for field in term_fields:
                        if stripped.startswith(f"{field}:"):
                            value = stripped.split(":", 1)[1].strip().strip("'\"")
                            if value:
                                # Convert numeric fields
                                if field in ("district", "class") and value.isdigit():
                                    current_term[field] = int(value)
                                else:
                                    current_term[field] = value
                            break

        # Don't forget the last member and term
        if current_term:
            current_member["terms"].append(current_term)
        if current_member:
            members.append(current_member)

        # Reverse terms to show most recent first (YAML has oldest first)
        for member in members:
            if member["terms"]:
                member["terms"] = list(reversed(member["terms"]))

        return members

    def fetch_all_members(self, api_key: str = None, dry_run: bool = False) -> list[dict]:
        """Fetch all members from unitedstates/congress-legislators GitHub repo."""
        console.print("[bold]Fetching members from unitedstates/congress-legislators[/bold]\n")

        if dry_run:
            console.print("[dim]Would fetch from:[/dim]")
            console.print(f"[dim]  - {CURRENT_LEGISLATORS_URL}[/dim]")
            console.print(f"[dim]  - {HISTORICAL_LEGISLATORS_URL}[/dim]")
            console.print(f"[dim]Expected: ~12,700 total members[/dim]")
            return []

        # Fetch current legislators
        console.print("Fetching current legislators...")
        current_yaml = self._fetch_url(CURRENT_LEGISLATORS_URL)
        current_members = self._parse_legislators_yaml(current_yaml)
        console.print(f"  -> {len(current_members):,} current members")

        # Fetch historical legislators
        console.print("Fetching historical legislators...")
        historical_yaml = self._fetch_url(HISTORICAL_LEGISLATORS_URL)
        historical_members = self._parse_legislators_yaml(historical_yaml)
        console.print(f"  -> {len(historical_members):,} historical members")

        # Combine and deduplicate by bioguide ID
        all_members = {}
        for member in historical_members + current_members:
            bioguide_id = member.get("id", {}).get("bioguide")
            if bioguide_id:
                all_members[bioguide_id] = member

        members_list = list(all_members.values())
        console.print(f"\n  -> Total unique members: {len(members_list):,}")
        return members_list

    def save_members(self, members: list[dict]) -> None:
        """Save members to JSON file."""
        # Ensure directory exists
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        console.print(f"\nWriting to {self.output_file}...")
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(members, f, indent=2)

        console.print(f"[green]Done![/green] Wrote {len(members):,} members to {self.output_file.name}")

    def get_status(self) -> dict:
        """Get status of current congress_api_members.json file."""
        if not self.output_file.exists():
            return {"exists": False, "count": 0}

        with open(self.output_file, "r", encoding="utf-8") as f:
            members = json.load(f)

        # Count by party (from most recent term)
        party_counts = {}
        for member in members:
            terms = member.get("terms", [])
            party = terms[0].get("party", "Unknown") if terms else "Unknown"
            party_counts[party] = party_counts.get(party, 0) + 1

        # Count by chamber (based on most recent term)
        chamber_counts = {"Senate": 0, "House": 0, "Unknown": 0}
        for member in members:
            terms = member.get("terms", [])
            if terms:
                term_type = terms[0].get("type", "")
                if term_type == "sen":
                    chamber_counts["Senate"] += 1
                elif term_type == "rep":
                    chamber_counts["House"] += 1
                else:
                    chamber_counts["Unknown"] += 1
            else:
                chamber_counts["Unknown"] += 1

        # Count members with FEC IDs
        fec_count = sum(1 for m in members if m.get("id", {}).get("fec"))

        return {
            "exists": True,
            "count": len(members),
            "fec_count": fec_count,
            "party_counts": party_counts,
            "chamber_counts": chamber_counts,
            "file_path": str(self.output_file),
        }
