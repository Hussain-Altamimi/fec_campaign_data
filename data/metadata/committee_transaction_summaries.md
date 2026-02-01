Source: https://www.fec.gov/campaign-finance-data/any-transaction-one-committee-another-file-description/

# Committee Transaction Summaries (1980-2026)

**File:** `committee_transaction_summaries_1980-2026.csv`

Aggregated transactions from one committee to another, including contributions, transfers, and independent expenditures between PACs, party committees, and candidate committees.

## Columns

| Column | Description |
|--------|-------------|
| `election_cycle` | 2-year FEC reporting period (from original filename) |
| `transaction_year` | Actual year from transaction date |
| `source_cmte_id` | Committee making the transaction |
| `dest_cmte_id` | Committee receiving the transaction |
| `dest_name` | Name of receiving committee |
| `transaction_tp` | Transaction type code |
| `total_amount` | Sum of transaction amounts |
| `transaction_count` | Number of transactions aggregated |

## Transaction Types

Includes types: 10J, 11J, 13, 15J, 15Z, 16C, 16F, 16G, 16R, 17R, 17Z, 18G, 18J, 18K, 18U, 19J, 20, 20C, 20F, 20G, 20R, 22H, 22Z, 23Y, 24A, 24C, 24E, 24F, 24G, 24H, 24K, 24N, 24P, 24R, 24U, 24Z, 29, and (from 2016) 30F, 30G, 30J, 30K, 31F, 31G, 31J, 31K, 32F, 32G, 32J, 32K, 40, 40Z, 41, 41Z, 42, 42Z.

## Exclusions

To prevent double-counting:
- Memo transactions (`memo_cd = 'X'`) — 34.6M rows excluded
- Amended filings (`amndt_ind != 'N'`) — 5.2M rows excluded
- Duplicate `sub_id` values — 2 rows excluded
