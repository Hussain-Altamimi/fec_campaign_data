"""Processor for creating bioguide crosswalk."""

import csv
import json
import re
from pathlib import Path

import pandas as pd
from rich.console import Console

console = Console()

# Nickname mappings for name matching
NICKNAME_MAP = {
    "bob": "robert",
    "bobby": "robert",
    "rob": "robert",
    "bill": "william",
    "billy": "william",
    "will": "william",
    "jim": "james",
    "jimmy": "james",
    "jamie": "james",
    "mike": "michael",
    "mick": "michael",
    "dick": "richard",
    "rick": "richard",
    "rich": "richard",
    "ted": "theodore",
    "teddy": "theodore",
    "tom": "thomas",
    "tommy": "thomas",
    "joe": "joseph",
    "joey": "joseph",
    "dan": "daniel",
    "danny": "daniel",
    "dave": "david",
    "davy": "david",
    "tony": "anthony",
    "al": "albert",
    "al": "alfred",
    "al": "alan",
    "ed": "edward",
    "eddy": "edward",
    "eddie": "edward",
    "ned": "edward",
    "sam": "samuel",
    "sammy": "samuel",
    "charlie": "charles",
    "chuck": "charles",
    "chas": "charles",
    "ben": "benjamin",
    "benny": "benjamin",
    "jack": "john",
    "johnny": "john",
    "jon": "john",
    "steve": "stephen",
    "steven": "stephen",
    "pat": "patrick",
    "patty": "patricia",
    "chris": "christopher",
    "kit": "christopher",
    "matt": "matthew",
    "andy": "andrew",
    "drew": "andrew",
    "nick": "nicholas",
    "nicky": "nicholas",
    "pete": "peter",
    "jerry": "gerald",
    "jerry": "jerome",
    "gerry": "gerald",
    "larry": "lawrence",
    "lawrie": "lawrence",
    "harry": "harold",
    "hal": "harold",
    "hank": "henry",
    "liz": "elizabeth",
    "lizzy": "elizabeth",
    "beth": "elizabeth",
    "betty": "elizabeth",
    "betsy": "elizabeth",
    "kate": "katherine",
    "kathy": "katherine",
    "cathy": "catherine",
    "katie": "katherine",
    "maggie": "margaret",
    "peggy": "margaret",
    "meg": "margaret",
    "margie": "margaret",
    "sue": "susan",
    "suzy": "susan",
    "debbie": "deborah",
    "deb": "deborah",
    "barb": "barbara",
    "barbie": "barbara",
    "jenny": "jennifer",
    "jen": "jennifer",
    "cindy": "cynthia",
    "sandy": "sandra",
    "mandy": "amanda",
    "becky": "rebecca",
    "vicky": "victoria",
    "tina": "christina",
    "nancy": "ann",
    "sally": "sarah",
    "phil": "philip",
    "don": "donald",
    "donny": "donald",
    "ron": "ronald",
    "ronny": "ronald",
    "ray": "raymond",
    "ken": "kenneth",
    "kenny": "kenneth",
    "greg": "gregory",
    "gregg": "gregory",
    "walt": "walter",
    "wally": "walter",
    "fred": "frederick",
    "freddy": "frederick",
    "gene": "eugene",
    "lenny": "leonard",
    "len": "leonard",
    "leo": "leonard",
    "norm": "norman",
    "bernie": "bernard",
    "ernie": "ernest",
    "arnie": "arnold",
    "abe": "abraham",
    "max": "maxwell",
    "max": "maximilian",
    "doug": "douglas",
    "cliff": "clifford",
    "tim": "timothy",
    "timmy": "timothy",
    "bart": "bartholomew",
    "zach": "zachary",
    "zack": "zachary",
    "alex": "alexander",
    "sandy": "alexander",
    "jeff": "jeffrey",
    "geoffrey": "jeffrey",
    "geoff": "geoffrey",
    "josh": "joshua",
    "nate": "nathaniel",
    "nathan": "nathaniel",
    "nat": "nathaniel",
    "cy": "cyrus",
    "ike": "isaac",
    "izzy": "isidore",
    "manny": "manuel",
    "manny": "emmanuel",
    "mort": "mortimer",
    "mort": "morton",
    "sy": "seymour",
    "si": "simon",
    "vinny": "vincent",
    "vic": "victor",
    "vince": "vincent",
    "wes": "wesley",
    "tony": "antonio",
    "frank": "francis",
    "frankie": "francis",
    "fran": "frances",
    "frannie": "frances",
}

# Reverse map for looking up canonical names
CANONICAL_NAMES = {}
for nickname, canonical in NICKNAME_MAP.items():
    CANONICAL_NAMES.setdefault(canonical, set()).add(nickname)

# Party mappings from congress-legislators to FEC codes
PARTY_TO_FEC = {
    "Democrat": "DEM",
    "Democratic": "DEM",
    "Republican": "REP",
    "Independent": "IND",
    "Libertarian": "LIB",
    "Green": "GRE",
    "Liberal": "LIB",
    "Reform": "REF",
    "Conservative": "CON",
    "Democrat-Farmer-Labor": "DFL",
    "Farmer-Labor": "DFL",
}


class BioguideProcessor:
    """Creates FEC candidate ID to Bioguide ID crosswalk."""

    def __init__(self, data_dir: Path, output_file: Path):
        self.data_dir = data_dir
        self.output_file = output_file
        self.congress_api_file = data_dir / "bioguide_ids" / "congress_api_members.json"

    def load_congress_members(self) -> list[dict]:
        """Load congress API members from JSON file."""
        if not self.congress_api_file.exists():
            raise FileNotFoundError(f"Congress API members file not found: {self.congress_api_file}")

        with open(self.congress_api_file, encoding="utf-8") as f:
            return json.load(f)

    def load_candidate_registrations(self) -> pd.DataFrame:
        """Load FEC candidate registrations."""
        candidate_file = self.data_dir / "candidate_registrations_1980-2026.csv"
        if not candidate_file.exists():
            raise FileNotFoundError(f"Candidate registrations file not found: {candidate_file}")

        return pd.read_csv(candidate_file, dtype=str, low_memory=False)

    def has_term_in_range(self, member: dict, start_year: int = 1980, end_year: int = 2026) -> bool:
        """Check if member has terms in the specified year range."""
        for term in member.get("terms", []):
            term_start = term.get("start", "")
            term_end = term.get("end", "")
            if term_start:
                start = int(term_start[:4])
                end = int(term_end[:4]) if term_end else start + 2
                # Check if term overlaps with our range
                if start <= end_year and end >= start_year:
                    return True
        return False

    def get_terms_in_range(self, member: dict, start_year: int = 1980, end_year: int = 2026) -> list[dict]:
        """Get all terms for a member in the specified year range."""
        terms = []
        for term in member.get("terms", []):
            term_start = term.get("start", "")
            term_end = term.get("end", "")
            if term_start:
                start = int(term_start[:4])
                end = int(term_end[:4]) if term_end else start + 2
                if start <= end_year and end >= start_year:
                    terms.append(term)
        return terms

    def normalize_name(self, name: str) -> tuple[str, str, str]:
        """Parse 'Last, First Middle Jr' into (last, first, suffix).

        Returns lowercase, stripped name components.
        """
        name = name.strip()

        # Handle suffixes
        suffix = ""
        suffix_patterns = [
            r"\s+(jr\.?|sr\.?|ii|iii|iv|v|2nd|3rd|4th)$",
            r",\s*(jr\.?|sr\.?|ii|iii|iv|v|2nd|3rd|4th)$",
        ]
        for pattern in suffix_patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                suffix = match.group(1).lower().rstrip(".")
                name = name[: match.start()].strip()
                break

        # Parse "Last, First Middle" format
        if "," in name:
            parts = name.split(",", 1)
            last = parts[0].strip().lower()
            first_middle = parts[1].strip() if len(parts) > 1 else ""
            # Get just the first name (before any middle names)
            first = first_middle.split()[0].lower() if first_middle else ""
        else:
            # "First Last" format - less common in FEC data
            parts = name.split()
            if len(parts) >= 2:
                first = parts[0].lower()
                last = parts[-1].lower()
            elif len(parts) == 1:
                first = ""
                last = parts[0].lower()
            else:
                first = ""
                last = ""

        # Clean up quotes and special characters from first name
        first = re.sub(r'["\']', "", first)
        first = re.sub(r"\s+", " ", first).strip()

        return (last, first, suffix)

    def get_canonical_name(self, name: str) -> str:
        """Get canonical form of a name (handle nicknames)."""
        name = name.lower().strip()
        return NICKNAME_MAP.get(name, name)

    def names_match(self, fec_name: str, first: str, last: str, suffix: str = "") -> tuple[bool, float]:
        """Compare FEC name to congress member name.

        Returns (match, confidence_score).
        """
        fec_last, fec_first, fec_suffix = self.normalize_name(fec_name)

        # Clean up names
        first = first.lower().strip()
        last = last.lower().strip()
        suffix = suffix.lower().strip() if suffix else ""

        # Exact last name match is required
        if fec_last != last:
            return (False, 0.0)

        # Check first name
        fec_first_canonical = self.get_canonical_name(fec_first)
        first_canonical = self.get_canonical_name(first)

        # Exact first name match
        if fec_first == first:
            if fec_suffix == suffix or not suffix:
                return (True, 1.0)
            else:
                return (True, 0.9)  # Suffix mismatch

        # Canonical name match (nicknames)
        if fec_first_canonical == first_canonical or fec_first_canonical == first or fec_first == first_canonical:
            if fec_suffix == suffix or not suffix:
                return (True, 0.95)
            else:
                return (True, 0.85)

        # Check if one is a nickname of the other
        if first in NICKNAME_MAP and NICKNAME_MAP[first] == fec_first:
            return (True, 0.9)
        if fec_first in NICKNAME_MAP and NICKNAME_MAP[fec_first] == first:
            return (True, 0.9)

        # First initial match
        if fec_first and first and fec_first[0] == first[0]:
            return (True, 0.7)

        return (False, 0.0)

    def term_to_election_cycles(self, term: dict) -> list[int]:
        """Convert a congressional term to overlapping FEC election cycles.

        FEC election cycles are 2-year periods ending in even years.
        A term from 1995-2001 would have campaigns in 1994 (initial) and 2000 (re-election).
        """
        term_start = term.get("start", "")
        term_end = term.get("end", "")
        if not term_start:
            return []

        start_year = int(term_start[:4])
        end_year = int(term_end[:4]) if term_end else start_year + 2

        cycles = []

        # The campaign cycle for the initial election (even year before or of term start)
        initial_campaign = start_year if start_year % 2 == 0 else start_year - 1

        # The re-election campaign cycle (even year before or of term end)
        reelection_campaign = end_year if end_year % 2 == 0 else end_year - 1

        term_type = term.get("type")
        if term_type == "rep":
            # House members campaign every 2 years
            year = initial_campaign
            while year <= end_year:
                if 1980 <= year <= 2026:
                    cycles.append(year)
                year += 2
        else:
            # Senate - include both initial campaign and re-election campaign
            # Initial election
            if 1980 <= initial_campaign <= 2026:
                cycles.append(initial_campaign)
            # Re-election campaign (if different from initial and in range)
            if reelection_campaign != initial_campaign and 1980 <= reelection_campaign <= 2026:
                cycles.append(reelection_campaign)

        return cycles

    def match_by_name(
        self, members_without_fec: list[dict], candidates_df: pd.DataFrame
    ) -> list[dict]:
        """Match Congress members to FEC candidates by name, state, office, and time."""
        matches = []

        # Preprocess candidates dataframe for faster lookups
        # Group by state, office type
        candidates_df["cand_office"] = candidates_df["cand_office"].fillna("")
        candidates_df["cand_office_st"] = candidates_df["cand_office_st"].fillna("")
        candidates_df["cand_pty_affiliation"] = candidates_df["cand_pty_affiliation"].fillna("")
        candidates_df["election_cycle"] = candidates_df["election_cycle"].astype(int)

        console.print(f"\nAttempting name matching for {len(members_without_fec)} members...")

        matched_count = 0
        for member in members_without_fec:
            bioguide = member.get("id", {}).get("bioguide")
            name = member.get("name", {})
            first = name.get("first", "")
            last = name.get("last", "")
            suffix = name.get("suffix", "")
            nickname = name.get("nickname", "")

            if not bioguide or not last:
                continue

            terms = self.get_terms_in_range(member)
            if not terms:
                continue

            # Collect all potential matches across terms
            member_matches = []

            for term in terms:
                state = term.get("state")
                term_type = term.get("type")  # "rep" or "sen"
                party = term.get("party", "")
                cycles = self.term_to_election_cycles(term)

                if not state or not term_type or not cycles:
                    continue

                # Map term type to FEC office code
                office_code = "H" if term_type == "rep" else "S"

                # Map party to FEC code
                fec_party = PARTY_TO_FEC.get(party, "")

                # Filter candidates by state, office, and cycle
                mask = (
                    (candidates_df["cand_office_st"] == state)
                    & (candidates_df["cand_office"] == office_code)
                    & (candidates_df["election_cycle"].isin(cycles))
                )
                filtered = candidates_df[mask]

                if filtered.empty:
                    continue

                # Try to match by name
                for _, row in filtered.iterrows():
                    cand_name = row.get("cand_name", "")
                    cand_party = row.get("cand_pty_affiliation", "")
                    cand_id = row.get("cand_id", "")

                    if not cand_name or not cand_id:
                        continue

                    # Try matching with formal first name first
                    is_match, name_score = self.names_match(cand_name, first, last, suffix)

                    # If no match, try with nickname
                    if not is_match and nickname:
                        is_match, name_score = self.names_match(cand_name, nickname, last, suffix)

                    if not is_match:
                        continue

                    # Calculate overall confidence
                    confidence_score = name_score

                    # Party match bonus
                    party_match = False
                    if fec_party and cand_party:
                        if fec_party == cand_party:
                            party_match = True
                            confidence_score = min(1.0, confidence_score + 0.1)
                        else:
                            confidence_score = max(0.5, confidence_score - 0.2)

                    member_matches.append(
                        {
                            "cand_id": cand_id,
                            "bioguide_id": bioguide,
                            "name_score": name_score,
                            "confidence_score": confidence_score,
                            "party_match": party_match,
                            "cand_name": cand_name,
                            "member_name": f"{last}, {first}",
                        }
                    )

            if not member_matches:
                continue

            # Deduplicate by cand_id and keep highest confidence
            best_by_cand_id = {}
            for m in member_matches:
                cand_id = m["cand_id"]
                if cand_id not in best_by_cand_id or m["confidence_score"] > best_by_cand_id[cand_id]["confidence_score"]:
                    best_by_cand_id[cand_id] = m

            # Determine confidence level
            for cand_id, m in best_by_cand_id.items():
                score = m["confidence_score"]
                if score >= 0.95:
                    confidence = "high"
                elif score >= 0.8:
                    confidence = "medium"
                else:
                    confidence = "low"

                matches.append(
                    {
                        "cand_id": cand_id,
                        "bioguide_id": m["bioguide_id"],
                        "match_method": "name_match",
                        "confidence": confidence,
                    }
                )

            matched_count += 1

        console.print(f"  → Matched {matched_count} members to {len(matches)} FEC candidate IDs")
        return matches

    def validate_fec_ids(self, crosswalk: list[dict], valid_ids: set) -> list[dict]:
        """Validate FEC IDs against candidate registrations."""
        validated = []
        invalid_count = 0

        for entry in crosswalk:
            if entry["cand_id"] in valid_ids:
                validated.append(entry)
            else:
                invalid_count += 1

        if invalid_count > 0:
            console.print(f"  → {len(validated):,} valid IDs, {invalid_count:,} invalid IDs removed")

        return validated

    def create_crosswalk(self, dry_run: bool = False) -> None:
        """Create the bioguide crosswalk file."""
        console.print("[bold]Creating FEC-Bioguide Crosswalk[/bold]\n")

        # Load data sources
        console.print(f"Loading Congress API members from {self.congress_api_file.name}...")
        members = self.load_congress_members()
        console.print(f"  → {len(members):,} total members")

        console.print("Loading FEC candidate registrations...")
        candidates_df = self.load_candidate_registrations()
        valid_fec_ids = set(candidates_df["cand_id"].dropna().unique())
        console.print(f"  → {len(valid_fec_ids):,} unique candidate IDs")

        # Step 1: Extract direct FEC ID mappings (authoritative)
        console.print("\n[bold]Step 1:[/bold] Extracting authoritative FEC ID mappings...")
        authoritative_matches = []
        members_with_fec = 0
        members_without_fec = []

        for member in members:
            bioguide = member.get("id", {}).get("bioguide")
            fec_ids = member.get("id", {}).get("fec", [])

            if not bioguide:
                continue

            if fec_ids:
                members_with_fec += 1
                for fec_id in fec_ids:
                    authoritative_matches.append(
                        {
                            "cand_id": fec_id,
                            "bioguide_id": bioguide,
                            "match_method": "authoritative",
                            "confidence": "high",
                        }
                    )
            elif self.has_term_in_range(member):
                members_without_fec.append(member)

        console.print(f"  → {members_with_fec:,} members have embedded FEC IDs")
        console.print(f"  → {len(authoritative_matches):,} authoritative FEC-Bioguide mappings")

        # Validate authoritative matches
        authoritative_matches = self.validate_fec_ids(authoritative_matches, valid_fec_ids)

        # Step 2: Name matching for members without FEC IDs
        console.print(f"\n[bold]Step 2:[/bold] Name matching for {len(members_without_fec):,} members without FEC IDs...")
        name_matches = self.match_by_name(members_without_fec, candidates_df)

        # Combine all matches
        all_matches = authoritative_matches + name_matches

        # Remove duplicates and conflicts
        console.print("\n[bold]Step 3:[/bold] Deduplicating and resolving conflicts...")

        # First, identify FEC IDs that have authoritative matches
        authoritative_fec_ids = {e["cand_id"] for e in authoritative_matches}

        # Remove name_match entries for FEC IDs that have authoritative matches
        # (unless it's the same bioguide - which would be redundant anyway)
        filtered_name_matches = [
            e for e in name_matches
            if e["cand_id"] not in authoritative_fec_ids
        ]
        conflicts_removed = len(name_matches) - len(filtered_name_matches)
        if conflicts_removed > 0:
            console.print(f"  → Removed {conflicts_removed} name matches that conflict with authoritative matches")

        # Also remove name_match entries where same FEC ID maps to different bioguides (ambiguous)
        fec_to_bioguides = {}
        for e in filtered_name_matches:
            fec_id = e["cand_id"]
            if fec_id not in fec_to_bioguides:
                fec_to_bioguides[fec_id] = set()
            fec_to_bioguides[fec_id].add(e["bioguide_id"])

        ambiguous_fec_ids = {fec_id for fec_id, bios in fec_to_bioguides.items() if len(bios) > 1}
        if ambiguous_fec_ids:
            console.print(f"  → Removed {len(ambiguous_fec_ids)} FEC IDs with ambiguous name matches (multiple Congress members)")
            filtered_name_matches = [e for e in filtered_name_matches if e["cand_id"] not in ambiguous_fec_ids]

        # Now deduplicate (cand_id, bioguide_id) pairs
        all_matches = authoritative_matches + filtered_name_matches
        seen = {}
        for entry in all_matches:
            key = (entry["cand_id"], entry["bioguide_id"])
            if key not in seen:
                seen[key] = entry
            elif entry["match_method"] == "authoritative":
                # Prefer authoritative match
                seen[key] = entry

        crosswalk = list(seen.values())

        # Sort by cand_id for consistent output
        crosswalk.sort(key=lambda x: x["cand_id"])

        console.print(f"  → {len(crosswalk):,} unique mappings total")

        # Stats
        authoritative_count = sum(1 for e in crosswalk if e["match_method"] == "authoritative")
        name_match_count = sum(1 for e in crosswalk if e["match_method"] == "name_match")
        high_confidence = sum(1 for e in crosswalk if e["confidence"] == "high")
        medium_confidence = sum(1 for e in crosswalk if e["confidence"] == "medium")
        low_confidence = sum(1 for e in crosswalk if e["confidence"] == "low")

        console.print(f"\n[bold]Summary (before filtering):[/bold]")
        console.print(f"  Authoritative matches: {authoritative_count:,}")
        console.print(f"  Name matches: {name_match_count:,}")
        console.print(f"  High confidence: {high_confidence:,}")
        console.print(f"  Medium confidence: {medium_confidence:,} (discarded)")
        console.print(f"  Low confidence: {low_confidence:,} (discarded)")

        # Filter to only high confidence matches
        crosswalk = [e for e in crosswalk if e["confidence"] == "high"]
        console.print(f"\n  → {len(crosswalk):,} high-confidence mappings retained")

        # Check for bioguide IDs with multiple FEC IDs
        bioguide_counts = {}
        for entry in crosswalk:
            bg = entry["bioguide_id"]
            bioguide_counts[bg] = bioguide_counts.get(bg, 0) + 1

        multi_fec = sum(1 for count in bioguide_counts.values() if count > 1)
        console.print(f"  Members with multiple FEC IDs: {multi_fec:,}")

        if dry_run:
            console.print(f"\n[dim]Would write {len(crosswalk):,} high-confidence rows to {self.output_file}[/dim]")
            console.print("\nSample authoritative matches:")
            for entry in [e for e in crosswalk if e["match_method"] == "authoritative"][:5]:
                console.print(f"  {entry['cand_id']} → {entry['bioguide_id']} ({entry['match_method']})")
            console.print("\nSample name matches:")
            for entry in [e for e in crosswalk if e["match_method"] == "name_match"][:10]:
                console.print(f"  {entry['cand_id']} → {entry['bioguide_id']} ({entry['match_method']})")
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
