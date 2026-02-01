Source: https://www.fec.gov/campaign-finance-data/contributions-committees-candidates-file-description/

# Committee to Candidate Summaries (1980-2026)

**File:** `committee_to_candidate_summaries_1980-2026.csv`

Aggregated contributions and independent expenditures from committees (PACs, party committees, candidate committees) to candidates.

## Columns

| Column | Description |
|--------|-------------|
| `election_cycle` | 2-year FEC reporting period (from original filename) |
| `transaction_year` | Actual year from transaction date |
| `cmte_id` | Committee making the contribution |
| `cmte_name` | Name of the committee |
| `cand_id` | Candidate receiving the contribution |
| `transaction_tp` | Transaction type code |
| `total_amount` | Sum of transaction amounts |
| `transaction_count` | Number of transactions aggregated |

## Transaction Types

Includes types: 24A, 24C, 24E, 24F, 24H, 24K, 24N, 24P, 24R, 24Z

## Exclusions

To prevent double-counting:
- Memo transactions (`memo_cd = 'X'`) — 88.5K rows excluded
- Amended filings (`amndt_ind != 'N'`) — 2.9M rows excluded
