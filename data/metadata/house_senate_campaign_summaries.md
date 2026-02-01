Source: https://www.fec.gov/campaign-finance-data/current-campaigns-house-and-senate-file-description/

# House & Senate Campaign Summaries (1996-2026)

**File:** `house_senate_campaign_summaries_1996-2026.csv`

Summary financial information for House and Senate campaign committees only. One record per campaign committee per election cycle.

## Columns

| Column | Description |
|--------|-------------|
| `year` | Election cycle (added during consolidation) |
| `cand_id` | Candidate identification |
| `cand_name` | Candidate name |
| `cand_ici` | Incumbent/challenger status |
| `pty_cd` | Party code |
| `cand_pty_affiliation` | Party affiliation |
| `ttl_receipts` | Total receipts |
| `trans_from_auth` | Transfers from authorized committees |
| `ttl_disb` | Total disbursements |
| `trans_to_auth` | Transfers to authorized committees |
| `coh_bop` | Cash on hand - beginning of period |
| `coh_cop` | Cash on hand - close of period |
| `cand_contrib` | Contributions from candidate |
| `cand_loans` | Loans from candidate |
| `other_loans` | Other loans |
| `cand_loan_repay` | Candidate loan repayments |
| `other_loan_repay` | Other loan repayments |
| `debts_owed_by` | Debts owed by |
| `ttl_indiv_contrib` | Total individual contributions |
| `cand_office_st` | Candidate state |
| `cand_office_district` | Candidate district |
| `spec_election` | Special election status |
| `prim_election` | Primary election status |
| `run_election` | Runoff election status |
| `gen_election` | General election status |
| `gen_election_precent` | General election percentage |
| `other_pol_cmte_contrib` | Contributions from other political committees |
| `pol_pty_contrib` | Contributions from party committees |
| `cvg_end_dt` | Coverage end date |
| `indiv_refunds` | Refunds to individuals |
| `cmte_refunds` | Refunds to committees |

## Notes

- Election result data (spec_election, prim_election, etc.) only included in 1996-2006 files
- Double-counting may occur if candidate has multiple authorized committees
