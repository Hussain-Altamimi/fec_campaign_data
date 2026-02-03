# Bioguide Crosswalk

Links FEC candidate IDs (`cand_id`) to Congressional Bioguide IDs (`bioguide_id`) for candidates who served in Congress.

## Source

Data sourced from: https://github.com/unitedstates/congress-legislators

The `@unitedstates/congress-legislators` repository is a community-maintained dataset of all U.S. Congress members since 1789, including their Bioguide IDs and FEC candidate IDs.

## Column Definitions

| Column | Description |
|--------|-------------|
| `cand_id` | FEC candidate ID (e.g., `H8CA05035`) |
| `bioguide_id` | Congressional Bioguide ID (e.g., `P000197`) |
| `match_method` | How the match was established |
| `confidence` | Confidence level of the match |

### match_method values

| Value | Description |
|-------|-------------|
| `authoritative` | FEC ID from congress-legislators data, verified against FEC registrations |
| `authoritative_unverified` | FEC ID from congress-legislators data, not found in current FEC registrations (may be historical or contain typos) |

### confidence values

| Value | Description |
|-------|-------------|
| `high` | Match verified against FEC candidate registration data |
| `medium` | Match from authoritative source but not verified in current FEC data |

## Important Notes

- **One bioguide_id can map to multiple cand_ids**: Members who served in both House and Senate (e.g., Ron Wyden) have separate FEC candidate IDs for each office
- **Only covers members who served in Congress**: Candidates who ran but never won do not have Bioguide IDs
- **Coverage**: ~1,700 cand_id mappings covering ~1,500 unique Congress members

## Usage Example

```python
import pandas as pd

# Load FEC data and crosswalk
candidates = pd.read_csv('data/candidate_registrations_1980-2026.csv')
bioguide = pd.read_csv('data/cand_id_bioguide_crosswalk.csv')

# Join to add bioguide_id
candidates_with_bio = candidates.merge(
    bioguide[['cand_id', 'bioguide_id']],
    on='cand_id',
    how='left'
)

# Filter to only Congress members
congress_members = candidates_with_bio[candidates_with_bio.bioguide_id.notna()]
print(f"Found {congress_members.cand_id.nunique()} candidates who served in Congress")
```

## Regenerating the Crosswalk

To update the crosswalk with the latest data:

```bash
python scripts/create_bioguide_crosswalk.py
```

The script fetches the current legislators data from GitHub and validates against FEC registrations.
