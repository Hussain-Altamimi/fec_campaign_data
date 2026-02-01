Source: https://www.fec.gov/campaign-finance-data/all-candidates-file-description/

# All Candidate Summaries (1980-2026)

**File:** `all_candidate_summaries_1980-2026.csv`

Summary financial information for each candidate who raised or spent money during the period, regardless of when they are up for election. One record per candidate per election cycle.

## Columns

| Column | Description |
|--------|-------------|
| `year` | Election cycle (added during consolidation) |
| `cand_id` | Candidate identification (9-character code) |
| `cand_name` | Candidate name |
| `cand_ici` | Incumbent/challenger status (I/C/O) |
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
| `debts_owed_by` | Debts owed by committee |
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

- A candidate's financial summary may have double-counted activity if they have multiple authorized committees
- Subtract `trans_from_auth` and `trans_to_auth` from totals for more accurate values
