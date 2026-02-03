#!/usr/bin/env python3
"""
Create a crosswalk table linking FEC candidate IDs to Congressional Bioguide IDs.

This script:
1. Fetches Congressional member data from the @unitedstates/congress-legislators repository
2. Extracts bioguide_id to fec_id mappings from both current and historical legislators
3. Validates mappings against FEC candidate registrations
4. Outputs a crosswalk CSV

Data source: https://github.com/unitedstates/congress-legislators

Usage:
    python scripts/create_bioguide_crosswalk.py
"""

import csv
import re
import ssl
import urllib.request
import urllib.error
from pathlib import Path
from collections import defaultdict

# Try to import yaml, fall back to simple parser if not available
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# Create SSL context for downloads
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# URLs for congress-legislators data
CURRENT_URL = "https://raw.githubusercontent.com/unitedstates/congress-legislators/main/legislators-current.yaml"
HISTORICAL_URL = "https://raw.githubusercontent.com/unitedstates/congress-legislators/main/legislators-historical.yaml"


def fetch_yaml_data(url: str) -> str:
    """Fetch YAML data from URL."""
    print(f"Fetching {url}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'FEC-Bioguide-Crosswalk/1.0'})
        with urllib.request.urlopen(req, timeout=60, context=SSL_CONTEXT) as response:
            return response.read().decode('utf-8')
    except urllib.error.URLError as e:
        print(f"Error fetching {url}: {e}")
        return None


def simple_yaml_parse(content: str) -> list:
    """
    Simple YAML parser for the congress-legislators format.
    Only extracts id.bioguide and id.fec fields.
    """
    members = []
    current_member = None
    in_id_block = False
    in_fec_list = False

    for line in content.split('\n'):
        # New member starts with "- id:"
        if line.startswith('- id:'):
            if current_member and current_member.get('bioguide'):
                members.append(current_member)
            current_member = {'bioguide': None, 'fec': []}
            in_id_block = True
            in_fec_list = False
            continue

        if current_member is None:
            continue

        # Check if we're still in the id block
        if in_id_block:
            # End of id block when we hit name:, bio:, terms:, or another top-level key
            if line.startswith('  name:') or line.startswith('  bio:') or line.startswith('  terms:'):
                in_id_block = False
                in_fec_list = False
                continue

            # Extract bioguide
            match = re.match(r'\s+bioguide:\s*(\S+)', line)
            if match:
                current_member['bioguide'] = match.group(1)
                continue

            # Start of fec list
            if re.match(r'\s+fec:\s*$', line):
                in_fec_list = True
                continue

            # FEC ID in list format
            if in_fec_list:
                match = re.match(r'\s+- (\S+)', line)
                if match:
                    current_member['fec'].append(match.group(1))
                elif not line.strip().startswith('-') and line.strip():
                    # No longer in fec list
                    in_fec_list = False

    # Don't forget last member
    if current_member and current_member.get('bioguide'):
        members.append(current_member)

    return members


def parse_legislators(content: str) -> list:
    """Parse legislators YAML content."""
    if HAS_YAML:
        try:
            data = yaml.safe_load(content)
            members = []
            for item in data:
                ids = item.get('id', {})
                bioguide = ids.get('bioguide')
                fec_ids = ids.get('fec', [])
                if bioguide:
                    members.append({
                        'bioguide': bioguide,
                        'fec': fec_ids if isinstance(fec_ids, list) else [fec_ids] if fec_ids else []
                    })
            return members
        except Exception as e:
            print(f"YAML parsing failed, using simple parser: {e}")

    return simple_yaml_parse(content)


def load_fec_cand_ids(data_dir: Path) -> set:
    """Load all valid cand_ids from FEC data."""
    cand_ids = set()
    reg_file = data_dir / 'candidate_registrations_1980-2026.csv'

    print(f"Loading FEC candidate IDs from {reg_file}...")

    with open(reg_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cand_id = row.get('cand_id', '').strip()
            if cand_id:
                cand_ids.add(cand_id)

    print(f"Loaded {len(cand_ids)} unique FEC candidate IDs")
    return cand_ids


def create_crosswalk(members: list, valid_cand_ids: set) -> list:
    """
    Create crosswalk from members data.
    Returns list of (cand_id, bioguide_id) mappings.
    """
    crosswalk = []
    seen_pairs = set()

    for member in members:
        bioguide = member['bioguide']
        fec_ids = member['fec']

        for fec_id in fec_ids:
            if not fec_id:
                continue

            # Clean FEC ID
            fec_id = fec_id.strip()

            # Skip if we've seen this pair
            pair = (fec_id, bioguide)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            # Determine confidence based on FEC validation
            if fec_id in valid_cand_ids:
                confidence = 'high'
                match_method = 'authoritative'
            else:
                confidence = 'medium'
                match_method = 'authoritative_unverified'

            crosswalk.append({
                'cand_id': fec_id,
                'bioguide_id': bioguide,
                'match_method': match_method,
                'confidence': confidence,
            })

    return crosswalk


def write_crosswalk(crosswalk: list, output_file: Path):
    """Write crosswalk to CSV file."""
    print(f"Writing crosswalk to {output_file}...")

    # Sort by cand_id
    crosswalk = sorted(crosswalk, key=lambda x: x['cand_id'])

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['cand_id', 'bioguide_id', 'match_method', 'confidence'])
        writer.writeheader()
        writer.writerows(crosswalk)

    print(f"Wrote {len(crosswalk)} rows")


def verify_results(crosswalk: list):
    """Print verification statistics."""
    print("\n=== Verification ===")

    # Count by confidence
    by_conf = defaultdict(int)
    for m in crosswalk:
        by_conf[m['confidence']] += 1

    print("\nMatches by confidence:")
    for conf, count in sorted(by_conf.items()):
        print(f"  {conf}: {count}")

    # Check for duplicate cand_ids
    cand_ids = [m['cand_id'] for m in crosswalk]
    unique_cand_ids = len(set(cand_ids))
    print(f"\nUnique cand_ids: {unique_cand_ids}")
    print(f"Total rows: {len(crosswalk)}")

    if len(cand_ids) != unique_cand_ids:
        print("WARNING: Some cand_ids map to multiple bioguide_ids")
        from collections import Counter
        counts = Counter(cand_ids)
        for cid, count in counts.items():
            if count > 1:
                print(f"  {cid}: {count} bioguide_ids")

    # Check unique bioguide_ids
    bio_ids = [m['bioguide_id'] for m in crosswalk]
    unique_bio_ids = len(set(bio_ids))
    print(f"Unique bioguide_ids: {unique_bio_ids}")

    # Check known members
    known_checks = {
        'P000197': 'Nancy Pelosi',
        'M000355': 'Mitch McConnell',
        'W000779': 'Ron Wyden',
        'S000148': 'Chuck Schumer',
        'C000127': 'Maria Cantwell',
    }

    print("\nKnown member checks:")
    bio_to_cands = defaultdict(list)
    for m in crosswalk:
        bio_to_cands[m['bioguide_id']].append(m['cand_id'])

    for bio_id, name in known_checks.items():
        cands = bio_to_cands.get(bio_id, [])
        if cands:
            print(f"  {name} ({bio_id}): {', '.join(cands)}")
        else:
            print(f"  {name} ({bio_id}): NOT FOUND")


def main():
    # Setup paths
    script_dir = Path(__file__).parent
    repo_dir = script_dir.parent
    data_dir = repo_dir / 'data'
    output_file = data_dir / 'cand_id_bioguide_crosswalk.csv'

    # Fetch current and historical legislators
    current_yaml = fetch_yaml_data(CURRENT_URL)
    historical_yaml = fetch_yaml_data(HISTORICAL_URL)

    if not current_yaml and not historical_yaml:
        print("ERROR: Failed to fetch any legislator data")
        return 1

    # Parse legislators
    all_members = []

    if current_yaml:
        current_members = parse_legislators(current_yaml)
        print(f"Parsed {len(current_members)} current legislators")
        all_members.extend(current_members)

    if historical_yaml:
        historical_members = parse_legislators(historical_yaml)
        print(f"Parsed {len(historical_members)} historical legislators")
        all_members.extend(historical_members)

    print(f"Total legislators: {len(all_members)}")

    # Count how many have FEC IDs
    with_fec = sum(1 for m in all_members if m['fec'])
    print(f"Legislators with FEC IDs: {with_fec}")

    # Load valid FEC cand_ids for validation
    valid_cand_ids = load_fec_cand_ids(data_dir)

    # Create crosswalk
    crosswalk = create_crosswalk(all_members, valid_cand_ids)

    # Write output
    write_crosswalk(crosswalk, output_file)

    # Verify results
    verify_results(crosswalk)

    print("\nDone!")
    return 0


if __name__ == '__main__':
    exit(main())
