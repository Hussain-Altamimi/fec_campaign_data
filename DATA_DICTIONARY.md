# FEC Campaign Finance Data Dictionary

This document describes all tables in the FEC campaign finance dataset. Use this as context when querying or analyzing the data.

## Quick Reference

| Table                                         | Description                                    | Rows | Key Columns                      |
| --------------------------------------------- | ---------------------------------------------- | ---- | -------------------------------- |
| `candidate_registrations`                     | Candidate info (name, party, office)           | 129K | `cand_id`                        |
| `committee_registrations`                     | Committee info (name, type, treasurer)         | 296K | `cmte_id`                        |
| `all_candidate_summaries`                     | Candidate financials (receipts, disbursements) | 69K  | `cand_id`                        |
| `house_senate_campaign_summaries`             | House/Senate campaign financials               | 32K  | `cand_id`                        |
| `pac_party_summaries`                         | PAC/party committee financials                 | 140K | `cmte_id`                        |
| `candidate_committee_links`                   | Candidate-to-committee relationships           | 81K  | `cand_id`, `cmte_id`             |
| `committee_transaction_summaries`             | Committee-to-committee money flow              | 3.8M | `source_cmte_id`, `dest_cmte_id` |
| `committee_to_candidate_summaries`            | Committee contributions to candidates          | 2.8M | `cmte_id`, `cand_id`             |
| `candidate_individual_contribution_summaries` | Individual donations by candidate              | 62K  | `cand_id`                        |
| `expenditures_by_category`                    | Spending by disbursement type                  | 129K | `cmte_id`, `category`            |
| `expenditures_by_state`                       | Spending by payee state                        | 319K | `cmte_id`, `state`               |
| `cand_id_bioguide_crosswalk`                  | FEC ID to Congress Bioguide ID                 | 1.7K | `cand_id`, `bioguide_id`         |

---

## Global Conventions

### Column Formatting

- **Headers**: All `snake_case`
- **Names**: Capital Case (e.g., "Smith, John Jr" not "SMITH, JOHN JR")
- **IDs**: Uppercase alphanumeric (e.g., `H8CA05035`, `C00401224`)
- **Dates**: `MM/DD/YYYY` format (e.g., `12/31/2024`)
- **Currency**: Numeric, no symbols, can be negative (refunds)
- **Nulls**: Empty string or missing value

### Common ID Patterns

- **`cand_id`**: 9 characters, starts with H (House), S (Senate), or P (President)
  - Example: `H8CA05035` = House candidate, registered in 1988, California, sequence 035
- **`cmte_id`**: 9 characters, starts with C
  - Example: `C00401224`
- **`bioguide_id`**: Alphanumeric, used by Congress.gov
  - Example: `P000197` (Nancy Pelosi)

### Election Cycles

- `election_cycle`: 2-year period (even years: 1980, 1982, ... 2026)
- `transaction_year`: Actual calendar year of transaction
- Data spans 1980-2026 (varies by table)

---

## Table Schemas

### candidate_registrations_1980-2026.csv

**Purpose**: Master list of all FEC-registered candidates with basic info.

| Column                 | Type   | Description                     | Example                                 |
| ---------------------- | ------ | ------------------------------- | --------------------------------------- |
| `election_cycle`       | int    | 2-year reporting period         | `2024`                                  |
| `cand_id`              | string | Unique candidate ID             | `H8CA05035`                             |
| `cand_name`            | string | "Last, First Middle" format     | `Pelosi, Nancy`                         |
| `cand_pty_affiliation` | string | Party code                      | `DEM`, `REP`, `LIB`                     |
| `cand_election_yr`     | int    | Year of election                | `2024`                                  |
| `cand_office_st`       | string | State (2-letter)                | `CA`, `TX`, `US`                        |
| `cand_office`          | string | Office sought                   | `H`=House, `S`=Senate, `P`=President    |
| `cand_office_district` | string | District number                 | `12`, `00` (at-large/Senate)            |
| `cand_ici`             | string | Incumbent status                | `I`=Incumbent, `C`=Challenger, `O`=Open |
| `cand_status`          | string | Registration status             | `C`=Current, `P`=Prior, `F`=Future      |
| `cand_pcc`             | string | Principal campaign committee ID | `C00401224`                             |
| `cand_st1`             | string | Street address                  | `123 Main St`                           |
| `cand_st2`             | string | Street address line 2           | `Suite 100`                             |
| `cand_city`            | string | City                            | `San Francisco`                         |
| `cand_st`              | string | State                           | `CA`                                    |
| `cand_zip`             | string | ZIP code                        | `94102`                                 |

---

### committee_registrations_1980-2026.csv

**Purpose**: Master list of all FEC-registered committees (PACs, party, campaign).

| Column                 | Type   | Description                          | Example                                                                                                                    |
| ---------------------- | ------ | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| `election_cycle`       | int    | 2-year reporting period              | `2024`                                                                                                                     |
| `cmte_id`              | string | Unique committee ID                  | `C00401224`                                                                                                                |
| `cmte_nm`              | string | Committee name                       | `Nancy Pelosi For Congress`                                                                                                |
| `tres_nm`              | string | Treasurer name                       | `Smith, John`                                                                                                              |
| `cmte_st1`             | string | Street address                       | `123 Main St`                                                                                                              |
| `cmte_st2`             | string | Street address line 2                | `Suite 100`                                                                                                                |
| `cmte_city`            | string | City                                 | `San Francisco`                                                                                                            |
| `cmte_st`              | string | State                                | `CA`                                                                                                                       |
| `cmte_zip`             | string | ZIP code                             | `94102`                                                                                                                    |
| `cmte_dsgn`            | string | Designation                          | `P`=Principal, `A`=Authorized, `J`=Joint, `U`=Unauthorized, `B`=Lobbyist, `D`=Leadership                                   |
| `cmte_tp`              | string | Committee type                       | `H`=House, `S`=Senate, `P`=President, `N`=PAC-Nonqualified, `Q`=PAC-Qualified, `X`=Party-Nonqualified, `Y`=Party-Qualified |
| `cmte_pty_affiliation` | string | Party affiliation                    | `DEM`, `REP`                                                                                                               |
| `cmte_filing_freq`     | string | Filing frequency                     | `Q`=Quarterly, `M`=Monthly, `T`=Terminated                                                                                 |
| `org_tp`               | string | Organization type                    | `C`=Corporation, `L`=Labor, `M`=Membership, `T`=Trade                                                                      |
| `connected_org_nm`     | string | Connected organization               | `AFL-CIO`                                                                                                                  |
| `cand_id`              | string | Associated candidate (if applicable) | `H8CA05035`                                                                                                                |

---

### all_candidate_summaries_1980-2026.csv

**Purpose**: Financial summary per candidate per cycle.

| Column                   | Type   | Description                          | Example           |
| ------------------------ | ------ | ------------------------------------ | ----------------- |
| `election_cycle`         | int    | 2-year reporting period              | `2024`            |
| `cand_id`                | string | Candidate ID                         | `H8CA05035`       |
| `cand_name`              | string | Candidate name                       | `Pelosi, Nancy`   |
| `cand_ici`               | string | Incumbent status                     | `I`, `C`, `O`     |
| `pty_cd`                 | string | Party code (numeric)                 | `1`=DEM, `2`=REP  |
| `cand_pty_affiliation`   | string | Party affiliation                    | `DEM`             |
| `ttl_receipts`           | float  | Total money received                 | `5234567.89`      |
| `trans_from_auth`        | float  | Transfers from authorized committees | `100000.00`       |
| `ttl_disb`               | float  | Total disbursements                  | `4987654.32`      |
| `trans_to_auth`          | float  | Transfers to authorized committees   | `50000.00`        |
| `coh_bop`                | float  | Cash on hand - beginning of period   | `250000.00`       |
| `coh_cop`                | float  | Cash on hand - close of period       | `496913.57`       |
| `cand_contrib`           | float  | Contributions from candidate         | `0.00`            |
| `cand_loans`             | float  | Loans from candidate                 | `0.00`            |
| `other_loans`            | float  | Other loans received                 | `0.00`            |
| `cand_loan_repay`        | float  | Candidate loan repayments            | `0.00`            |
| `other_loan_repay`       | float  | Other loan repayments                | `0.00`            |
| `debts_owed_by`          | float  | Debts owed by committee              | `0.00`            |
| `ttl_indiv_contrib`      | float  | Total individual contributions       | `4500000.00`      |
| `cand_office_st`         | string | State                                | `CA`              |
| `cand_office_district`   | string | District                             | `11`              |
| `spec_election`          | string | Special election flag                | ``or`Y`           |
| `prim_election`          | string | Primary result                       | `W`=Won, `L`=Lost |
| `run_election`           | string | Runoff result                        | `W`, `L`, ``      |
| `gen_election`           | string | General result                       | `W`, `L`, ``      |
| `gen_election_precent`   | float  | General election vote %              | `76.5`            |
| `other_pol_cmte_contrib` | float  | PAC contributions                    | `500000.00`       |
| `pol_pty_contrib`        | float  | Party contributions                  | `25000.00`        |
| `cvg_end_dt`             | string | Coverage end date                    | `12/31/2024`      |
| `indiv_refunds`          | float  | Refunds to individuals               | `5000.00`         |
| `cmte_refunds`           | float  | Refunds to committees                | `0.00`            |

**Note**: For accurate totals, subtract `trans_from_auth` and `trans_to_auth` (inter-committee transfers).

---

### house_senate_campaign_summaries_1996-2026.csv

**Purpose**: Same structure as `all_candidate_summaries` but filtered to House/Senate only.

_Schema identical to `all_candidate_summaries`_

---

### pac_party_summaries_1996-2026.csv

**Purpose**: Financial summary for PACs and party committees.

| Column                   | Type   | Description                         | Example                                          |
| ------------------------ | ------ | ----------------------------------- | ------------------------------------------------ |
| `election_cycle`         | int    | 2-year reporting period             | `2024`                                           |
| `cmte_id`                | string | Committee ID                        | `C00000935`                                      |
| `cmte_nm`                | string | Committee name                      | `AFL-CIO Cope Political Contributions Committee` |
| `cmte_tp`                | string | Committee type                      | `Q`=PAC-Qualified, `N`=PAC-Nonqualified          |
| `cmte_dsgn`              | string | Designation                         | `U`=Unauthorized                                 |
| `cmte_filing_freq`       | string | Filing frequency                    | `M`, `Q`                                         |
| `ttl_receipts`           | float  | Total receipts                      | `25000000.00`                                    |
| `trans_from_aff`         | float  | Transfers from affiliates           | `1000000.00`                                     |
| `indv_contrib`           | float  | Individual contributions            | `15000000.00`                                    |
| `other_pol_cmte_contrib` | float  | Contributions from other committees | `500000.00`                                      |
| `cand_contrib`           | float  | Contributions from candidates       | `0.00`                                           |
| `cand_loans`             | float  | Candidate loans                     | `0.00`                                           |
| `ttl_loans_received`     | float  | Total loans                         | `0.00`                                           |
| `ttl_disb`               | float  | Total disbursements                 | `24000000.00`                                    |
| `tranf_to_aff`           | float  | Transfers to affiliates             | `500000.00`                                      |
| `indv_refunds`           | float  | Refunds to individuals              | `10000.00`                                       |
| `other_pol_cmte_refunds` | float  | Refunds to committees               | `0.00`                                           |
| `cand_loan_repay`        | float  | Candidate loan repayments           | `0.00`                                           |
| `loan_repay`             | float  | Loan repayments                     | `0.00`                                           |
| `coh_bop`                | float  | Cash - beginning of period          | `5000000.00`                                     |
| `coh_cop`                | float  | Cash - close of period              | `6000000.00`                                     |
| `debts_owed_by`          | float  | Debts owed                          | `0.00`                                           |
| `nonfed_trans_received`  | float  | Non-federal transfers               | `0.00`                                           |
| `contrib_to_other_cmte`  | float  | Contributions to other committees   | `10000000.00`                                    |
| `ind_exp`                | float  | Independent expenditures            | `5000000.00`                                     |
| `pty_coord_exp`          | float  | Party coordinated expenditures      | `0.00`                                           |
| `nonfed_share_exp`       | float  | Non-federal share expenditures      | `0.00`                                           |
| `cvg_end_dt`             | string | Coverage end date                   | `12/31/2024`                                     |

---

### candidate_committee_links_2000-2026.csv

**Purpose**: Links candidates to their authorized committees.

| Column             | Type   | Description               | Example                       |
| ------------------ | ------ | ------------------------- | ----------------------------- |
| `election_cycle`   | int    | 2-year reporting period   | `2024`                        |
| `cand_id`          | string | Candidate ID              | `H8CA05035`                   |
| `cand_election_yr` | int    | Candidate's election year | `2024`                        |
| `fec_election_yr`  | int    | FEC election year         | `2024`                        |
| `cmte_id`          | string | Committee ID              | `C00401224`                   |
| `cmte_tp`          | string | Committee type            | `H`, `S`, `P`                 |
| `cmte_dsgn`        | string | Designation               | `P`=Principal, `A`=Authorized |
| `linkage_id`       | int    | Unique link ID            | `123456`                      |

---

### committee_transaction_summaries_1980-2026.csv

**Purpose**: Money flow between committees (aggregated).

| Column              | Type   | Description               | Example                     |
| ------------------- | ------ | ------------------------- | --------------------------- |
| `election_cycle`    | int    | 2-year reporting period   | `2024`                      |
| `transaction_year`  | int    | Actual transaction year   | `2023`                      |
| `source_cmte_id`    | string | Committee sending money   | `C00000935`                 |
| `dest_cmte_id`      | string | Committee receiving money | `C00401224`                 |
| `dest_name`         | string | Receiving committee name  | `Nancy Pelosi For Congress` |
| `transaction_tp`    | string | Transaction type code     | `24K`                       |
| `total_amount`      | float  | Sum of transactions       | `5000.00`                   |
| `transaction_count` | int    | Number of transactions    | `1`                         |

**Common Transaction Types**:

- `24K`: Contribution to candidate committee
- `24E`: Independent expenditure
- `24A`: Independent expenditure against
- `22Y`: Refund

---

### committee_to_candidate_summaries_1980-2026.csv

**Purpose**: Committee contributions to candidates (aggregated).

| Column              | Type   | Description             | Example            |
| ------------------- | ------ | ----------------------- | ------------------ |
| `election_cycle`    | int    | 2-year reporting period | `2024`             |
| `transaction_year`  | int    | Actual transaction year | `2023`             |
| `cmte_id`           | string | Contributing committee  | `C00000935`        |
| `cmte_name`         | string | Committee name          | `AFL-CIO Cope PAC` |
| `cand_id`           | string | Receiving candidate     | `H8CA05035`        |
| `transaction_tp`    | string | Transaction type        | `24K`              |
| `total_amount`      | float  | Sum of contributions    | `5000.00`          |
| `transaction_count` | int    | Number of contributions | `1`                |

---

### candidate_individual_contribution_summaries_1980-2026.csv

**Purpose**: Individual donations aggregated by candidate.

| Column              | Type   | Description                          | Example      |
| ------------------- | ------ | ------------------------------------ | ------------ |
| `election_cycle`    | int    | 2-year reporting period              | `2024`       |
| `transaction_year`  | int    | Transaction year                     | `2023`       |
| `transaction_month` | int    | Month (2026 only, else NULL)         | `6`          |
| `cand_id`           | string | Candidate ID                         | `H8CA05035`  |
| `bioguide_id`       | string | Congress Bioguide ID (if applicable) | `P000197`    |
| `total_raised`      | float  | Sum of individual contributions      | `4500000.00` |
| `transaction_count` | int    | Number of contributions              | `25000`      |

**Note**: Only includes contributions to candidate committees (types H, S, P). PAC contributions are not included.

---

### expenditures_by_category_2004-2026.csv

**Purpose**: Committee spending by disbursement category.

| Column              | Type   | Description             | Example                |
| ------------------- | ------ | ----------------------- | ---------------------- |
| `election_cycle`    | int    | 2-year reporting period | `2024`                 |
| `transaction_year`  | int    | Transaction year        | `2023`                 |
| `cmte_id`           | string | Spending committee      | `C00401224`            |
| `category`          | string | Category code           | `004`                  |
| `category_desc`     | string | Category description    | `Advertising Expenses` |
| `total_amount`      | float  | Total spent             | `1500000.00`           |
| `transaction_count` | int    | Number of expenditures  | `150`                  |

**Category Codes**:
| Code | Description |
|------|-------------|
| 001 | Administrative/Salary/Overhead |
| 002 | Travel |
| 003 | Solicitation/Fundraising |
| 004 | Advertising |
| 005 | Polling |
| 006 | Campaign Materials |
| 007 | Campaign Events |
| 008 | Transfers |
| 009 | Loan Repayments |
| 010 | Refunds |
| 011 | Contributions |
| 012 | Other |

---

### expenditures_by_state_2004-2026.csv

**Purpose**: Committee spending by payee state.

| Column              | Type   | Description             | Example     |
| ------------------- | ------ | ----------------------- | ----------- |
| `election_cycle`    | int    | 2-year reporting period | `2024`      |
| `transaction_year`  | int    | Transaction year        | `2023`      |
| `cmte_id`           | string | Spending committee      | `C00401224` |
| `state`             | string | Payee state (2-letter)  | `CA`        |
| `total_amount`      | float  | Total spent in state    | `500000.00` |
| `transaction_count` | int    | Number of expenditures  | `75`        |

---

### cand_id_bioguide_crosswalk.csv

**Purpose**: Links FEC candidate IDs to Congressional Bioguide IDs.

| Column         | Type   | Description               | Example          |
| -------------- | ------ | ------------------------- | ---------------- |
| `cand_id`      | string | FEC candidate ID          | `H8CA05035`      |
| `bioguide_id`  | string | Congress Bioguide ID      | `P000197`        |
| `match_method` | string | How match was established | `authoritative`  |
| `confidence`   | string | Match confidence          | `high`, `medium` |

**Notes**:

- Only ~3% of FEC candidates have Bioguide IDs (only those who served in Congress)
- One `bioguide_id` can map to multiple `cand_id` (e.g., House then Senate)

---

## Relationships

```
candidate_registrations (cand_id)
    ├── all_candidate_summaries (cand_id)
    ├── house_senate_campaign_summaries (cand_id)
    ├── candidate_committee_links (cand_id) ──► committee_registrations (cmte_id)
    ├── committee_to_candidate_summaries (cand_id)
    ├── candidate_individual_contribution_summaries (cand_id)
    └── cand_id_bioguide_crosswalk (cand_id)

committee_registrations (cmte_id)
    ├── pac_party_summaries (cmte_id)
    ├── committee_transaction_summaries (source_cmte_id, dest_cmte_id)
    ├── committee_to_candidate_summaries (cmte_id)
    ├── expenditures_by_category (cmte_id)
    └── expenditures_by_state (cmte_id)
```

---

## Data Quality Notes

### Exclusions Applied (Transaction Tables)

To prevent double-counting, these were excluded during aggregation:

- Memo transactions (`memo_cd = 'X'`) - subtransactions
- Amended filings (`amndt_ind != 'N'`) - superseded records
- Duplicate `sub_id` values - same transaction reported twice

### Known Limitations

1. **Double-counting in candidate summaries**: Candidates with multiple authorized committees may have inflated totals. Subtract `trans_from_auth` and `trans_to_auth` for accuracy.
2. **Historical data quality**: Older cycles (1980s-1990s) may have more missing or inconsistent data.
3. **Name variations**: Same person may appear with different name formats across cycles.

---

## Common Queries

### Find top fundraising candidates in a cycle

```sql
SELECT cand_id, cand_name, ttl_receipts
FROM all_candidate_summaries
WHERE election_cycle = 2024
ORDER BY ttl_receipts DESC
LIMIT 10
```

### Get PAC contributions to a candidate

```sql
SELECT cmte_name, SUM(total_amount) as total
FROM committee_to_candidate_summaries
WHERE cand_id = 'H8CA05035'
GROUP BY cmte_name
ORDER BY total DESC
```

### Join candidate with Bioguide ID

```sql
SELECT c.*, b.bioguide_id
FROM candidate_registrations c
LEFT JOIN cand_id_bioguide_crosswalk b ON c.cand_id = b.cand_id
WHERE c.election_cycle = 2024
```
