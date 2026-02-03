# Candidate Individual Contribution Summaries (1980-2026)

**File:** `data/candidate_individual_contribution_summaries_1980-2026.csv`

Aggregated individual contributions per candidate, grouped by election cycle and transaction year. For the 2026 cycle, data is further grouped by month to enable tracking of in-progress fundraising.

## Data Flow

```
individual_contributions (cmte_id)
    ↓ join on cmte_id + election_cycle
committee_registrations (cand_id)
    ↓ group by cand_id
candidate_individual_contribution_summaries (output)
```

Only candidate committees (types H, S, P) have a `cand_id`. Contributions to PACs and party committees are not included in this summary.

## Columns

| Column | Description |
|--------|-------------|
| `election_cycle` | 2-year FEC reporting period |
| `transaction_year` | Year extracted from transaction date |
| `transaction_month` | Month (1-12) for 2026 cycle only; NULL for all other cycles |
| `cand_id` | FEC candidate ID |
| `bioguide_id` | Congressional Bioguide ID, expanded via name matching (NULL if candidate never served in Congress) |
| `total_raised` | Sum of contribution amounts in dollars |
| `transaction_count` | Number of individual contributions |

## Filtering Applied

The following filters are applied to avoid double-counting:

- **Memos excluded**: Records with `memo_cd = 'X'` are subtransactions
- **Amendments excluded**: Only records with `amndt_ind = 'N'` (new) are included
- **Deduplicated**: Unique by `sub_id` to prevent counting the same transaction twice

## Usage Notes

- Join with `candidate_registrations_1980-2026.csv` on `cand_id` to get candidate names and party
- Join with `cand_id_bioguide_crosswalk.csv` on `cand_id` to link to Congressional Bioguide IDs
- The 2026 cycle includes monthly breakdowns (`transaction_month`) for tracking ongoing fundraising
- For historical cycles (1980-2024), `transaction_month` is NULL

## Example Queries

**Total individual contributions by candidate for 2024:**
```python
import polars as pl

df = pl.read_csv('data/candidate_individual_contribution_summaries_1980-2026.csv')
totals_2024 = (
    df.filter(pl.col('election_cycle') == 2024)
    .group_by('cand_id')
    .agg(
        pl.col('total_amount').sum(),
        pl.col('transaction_count').sum(),
    )
    .sort('total_amount', descending=True)
)
```

**Monthly fundraising trend for 2026:**
```python
monthly_2026 = (
    df.filter(pl.col('election_cycle') == 2026)
    .group_by('transaction_month')
    .agg(
        pl.col('total_amount').sum(),
        pl.col('transaction_count').sum(),
    )
    .sort('transaction_month')
)
```

## Relationship to Other Files

- **Source data**: `individual_contributions/*.csv` (itemized contributions)
- **Committee mapping**: `committee_registrations_1980-2026.csv` (cmte_id → cand_id)
- **Candidate details**: `candidate_registrations_1980-2026.csv` (names, party, state)
- **Financial summaries**: `all_candidate_summaries_1980-2026.csv` (broader financial data including PAC contributions)
