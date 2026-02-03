# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **data repository** containing processed FEC (Federal Election Commission) bulk campaign finance data from 1980-2026. Total size: 581 MB. There is no application code to build or test.

## Data Structure

All CSV files are in `data/` with corresponding documentation in `data/metadata/`:

| File | Description | Rows |
|------|-------------|------|
| `all_candidate_summaries_1980-2026.csv` | Financial summaries per candidate per cycle | 69K |
| `candidate_registrations_1980-2026.csv` | Candidate registration info | 129K |
| `candidate_committee_links_2000-2026.csv` | Candidate-to-committee links | 81K |
| `committee_registrations_1980-2026.csv` | Committee registration info | 296K |
| `house_senate_campaign_summaries_1996-2026.csv` | House/Senate financials | 32K |
| `pac_party_summaries_1996-2026.csv` | PAC/party financials | 140K |
| `committee_transaction_summaries_1980-2026.csv` | Committee-to-committee transactions (aggregated) | 3.8M |
| `committee_to_candidate_summaries_1980-2026.csv` | Committee-to-candidate contributions (aggregated) | 2.8M |
| `expenditures_by_category_2004-2026.csv` | Spending by disbursement category | 129K |
| `expenditures_by_state_2004-2026.csv` | Spending by payee state | 319K |

## Key Data Conventions

- All headers are `snake_case`
- All files include `election_cycle` as the first column to identify the 2-year FEC reporting period
- Aggregated transaction files also include `transaction_year` (the actual year from transaction dates), `total_amount`, and `transaction_count`
- Transaction data excludes memos (`memo_cd = 'X'`), amendments (`amndt_ind != 'N'`), and duplicate `sub_id` values to prevent double-counting

## Working with This Data

- Column definitions are in `data/metadata/*.md` files
- For accurate candidate totals, subtract `trans_from_auth` and `trans_to_auth` (inter-committee transfers)
- Large transaction files (committee_transaction_summaries, committee_to_candidate_summaries) are pre-aggregated summaries, not raw itemized data

## Source

All data sourced from: https://www.fec.gov/data/browse-data/?tab=bulk-data

See `PROCESS.md` for the full data preparation methodology.
