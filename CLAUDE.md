# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **data repository** containing processed FEC (Federal Election Commission) bulk campaign finance data from 1980-2026. Total size: ~50 GB (mostly individual contributions). There is no application code to build or test.

## Data Structure

All CSV files are in `data/` with corresponding documentation in `data/metadata/`:

| File | Description | Rows |
|------|-------------|------|
| `all_candidate_summaries_1980-2026.csv` | Financial summaries per candidate per cycle | 69K |
| `cand_id_bioguide_crosswalk.csv` | FEC-to-Bioguide ID crosswalk | 1.7K |
| `candidate_registrations_1980-2026.csv` | Candidate registration info | 129K |
| `candidate_committee_links_2000-2026.csv` | Candidate-to-committee links | 81K |
| `committee_registrations_1980-2026.csv` | Committee registration info | 296K |
| `house_senate_campaign_summaries_1996-2026.csv` | House/Senate financials | 32K |
| `pac_party_summaries_1996-2026.csv` | PAC/party financials | 140K |
| `committee_transaction_summaries_1980-2026.csv` | Committee-to-committee transactions (aggregated) | 3.8M |
| `committee_to_candidate_summaries_1980-2026.csv` | Committee-to-candidate contributions (aggregated) | 2.8M |
| `expenditures_by_category_2004-2026.csv` | Spending by disbursement category | 129K |
| `expenditures_by_state_2004-2026.csv` | Spending by payee state | 319K |
| `candidate_individual_contribution_summaries_1980-2026.csv` | Individual contributions aggregated by candidate | 62K |

### Individual Contributions (separate directory)

Itemized individual contributions are in `individual_contributions/` (not `data/`), split by election cycle:

| File Pattern | Description | Total Rows |
|--------------|-------------|------------|
| `YYYY_individual_contributions.csv` | Individual contributions per cycle (1980-2026) | 271M |

These files are large (49 GB total). Recent cycles (2016+) are multi-gigabyte due to small-dollar online fundraising. Each file includes `election_cycle` and `transaction_year` columns.

## Key Data Conventions

- All headers are `snake_case`
- All files include `election_cycle` as the first column to identify the 2-year FEC reporting period
- Aggregated transaction files also include `transaction_year` (the actual year from transaction dates), `total_amount`, and `transaction_count`
- Transaction data excludes memos (`memo_cd = 'X'`), amendments (`amndt_ind != 'N'`), and duplicate `sub_id` values to prevent double-counting

## Working with This Data

- Column definitions are in `data/metadata/*.md` files
- For accurate candidate totals, subtract `trans_from_auth` and `trans_to_auth` (inter-committee transfers)
- Large transaction files (committee_transaction_summaries, committee_to_candidate_summaries) are pre-aggregated summaries, not raw itemized data

## Bioguide Crosswalk

The `cand_id_bioguide_crosswalk.csv` file links FEC candidate IDs to Congressional Bioguide IDs for members who served in Congress.

**Key points:**
- One `bioguide_id` can map to multiple `cand_id` values (e.g., members who served in both House and Senate)
- Only ~3% of FEC candidates have Bioguide IDs (most candidates never won election to Congress)
- Join on `cand_id` to add Bioguide IDs to any FEC table

**Example join:**
```python
import pandas as pd
candidates = pd.read_csv('data/candidate_registrations_1980-2026.csv')
bioguide = pd.read_csv('data/cand_id_bioguide_crosswalk.csv')
merged = candidates.merge(bioguide[['cand_id', 'bioguide_id']], on='cand_id', how='left')
```

## FEC Data CLI

All data management is handled by a unified CLI in `scripts/fec/`:

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Main entry point
python -m fec [command]
```

### Update Commands

Check for and apply quarterly FEC data updates:

```bash
# Check for updates (no changes made)
python -m fec update check

# Run full update workflow
python -m fec update run

# Update specific cycle only
python -m fec update run --cycle 2026

# Verify data integrity
python -m fec verify --cycle-counts

# Show update status
python -m fec update status
```

The update workflow:
1. Checks FEC for updated files (HTTP HEAD requests)
2. Downloads changed cycles with retry logic
3. Processes using same methodology as original data
4. Replaces cycle data atomically (delete + re-import)

### Individual Contributions Commands

Download and process individual contributions data:

```bash
# Download all years (skips existing files)
python -m fec individual download

# Download specific cycle
python -m fec individual download --cycle 2024

# Dry run to see what would be downloaded
python -m fec individual download --dry-run

# Add transaction_year column to files
python -m fec individual add-year

# Aggregate individual contributions by candidate
python -m fec individual summarize
```

### Bioguide Crosswalk Commands

Create FEC-to-Bioguide ID mappings:

```bash
# Create crosswalk file
python -m fec bioguide create

# Dry run
python -m fec bioguide create --dry-run
```

### Legacy Scripts (Deprecated)

The following standalone scripts are deprecated but still work:

| Deprecated Script | Use Instead |
|-------------------|-------------|
| `download_individual_contributions.py` | `python -m fec individual download` |
| `add_transaction_year.py` | `python -m fec individual add-year` |
| `create_bioguide_crosswalk.py` | `python -m fec bioguide create` |
| `summarize_individual_contributions.py` | `python -m fec individual summarize` |
| `python -m fec_update` | `python -m fec update` |

## Source

All FEC data sourced from: https://www.fec.gov/data/browse-data/?tab=bulk-data

Bioguide crosswalk data sourced from: https://github.com/unitedstates/congress-legislators

See `PROCESS.md` for the full data preparation methodology.
