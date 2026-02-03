# FEC Campaign Finance Data Dictionary

This document describes all tables in the FEC campaign finance dataset. Use this as context when querying or analyzing the data.

## Quick Reference

| Table                              | Description                                    | Period    | Rows  | Key Columns                      |
| ---------------------------------- | ---------------------------------------------- | --------- | ----- | -------------------------------- |
| `candidate_registrations`          | Candidate info (name, party, office)           | 1980-2026 | ~130K | `cand_id`                        |
| `committee_registrations`          | Committee info (name, type, treasurer)         | 1980-2026 | ~300K | `cmte_id`                        |
| `all_candidate_summaries`          | Candidate financials (receipts, disbursements) | 1980-2026 | ~70K  | `cand_id`                        |
| `house_senate_campaign_summaries`  | House/Senate campaign financials               | 1996-2026 | ~32K  | `cand_id`                        |
| `pac_party_summaries`              | PAC/party committee financials                 | 1996-2026 | ~140K | `cmte_id`                        |
| `candidate_committee_links`        | Candidate-to-committee relationships           | 2000-2026 | ~81K  | `cand_id`, `cmte_id`             |
| `committee_transaction_summaries`  | Committee-to-committee money flow              | 1980-2026 | ~3.8M | `source_cmte_id`, `dest_cmte_id` |
| `committee_to_candidate_summaries` | Committee contributions to candidates          | 1980-2026 | ~2.8M | `cmte_id`, `cand_id`             |
| `expenditures_by_category`         | Spending by disbursement type                  | 2004-2026 | ~130K | `cmte_id`, `category`            |
| `expenditures_by_state`            | Spending by payee state                        | 2004-2026 | ~320K | `cmte_id`, `state`               |

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
  - Example: `H8CA05035` = House candidate, registered in 1988, California, district 05, sequence 035
  - Consistent across cycles for same candidate/office
- **`cmte_id`**: 9 characters, starts with C
  - Example: `C00401224`
  - Consistent across cycles for same committee

### Election Cycles

- **`year`** / **`election_cycle`**: 2-year period (even years: 1980, 1982, ... 2026)
- **`transaction_year`**: Actual calendar year of transaction (may differ from cycle)
- **`cand_election_yr`**: Year candidate is up for election
- **`fec_election_yr`**: Active 2-year reporting period

### Data Quality Notes

- **Double-counting**: Some candidate summaries may double-count if they have multiple authorized committees. Subtract `trans_from_auth` and `trans_to_auth` for accuracy.
- **Memo transactions excluded**: Transactions with `memo_cd = 'X'` removed to prevent double-counting
- **Amended filings excluded**: Only filings with `amndt_ind = 'N'` (new/original) included

---

## Table Schemas

### candidate_registrations_1980-2026.csv

Basic information for each candidate registered with the FEC. Includes candidates who filed a Statement of Candidacy, have active campaign committees, or are referenced by draft/nonconnected committees.

**Source**: https://www.fec.gov/campaign-finance-data/candidate-master-file-description/

| Column                 | Type   | Description                                                                           |
| ---------------------- | ------ | ------------------------------------------------------------------------------------- |
| `year`                 | int    | Election cycle (added during consolidation)                                           |
| `cand_id`              | string | Candidate identification (9-character code, consistent across cycles for same office) |
| `cand_name`            | string | Candidate name                                                                        |
| `cand_pty_affiliation` | string | Party affiliation code                                                                |
| `cand_election_yr`     | int    | Year of election                                                                      |
| `cand_office_st`       | string | State (House=state of race, Senate=state of race, President=US)                       |
| `cand_office`          | string | Office sought (H=House, P=President, S=Senate)                                        |
| `cand_office_district` | string | Congressional district (00 for at-large, Senate, Presidential)                        |
| `cand_ici`             | string | Incumbent/challenger status (C=Challenger, I=Incumbent, O=Open Seat)                  |
| `cand_status`          | string | Candidate status (C=Statutory, F=Future, N=Not yet, P=Prior cycle)                    |
| `cand_pcc`             | string | Principal campaign committee ID                                                       |
| `cand_st1`             | string | Mailing address - street                                                              |
| `cand_st2`             | string | Mailing address - street 2                                                            |
| `cand_city`            | string | Mailing address - city                                                                |
| `cand_st`              | string | Mailing address - state                                                               |
| `cand_zip`             | string | Mailing address - ZIP code                                                            |

---

### committee_registrations_1980-2026.csv

Basic information for each committee registered with the FEC, including PACs, party committees, and campaign committees.

**Source**: https://www.fec.gov/campaign-finance-data/committee-master-file-description/

| Column                 | Type   | Description                                                                                                   |
| ---------------------- | ------ | ------------------------------------------------------------------------------------------------------------- |
| `year`                 | int    | Election cycle (added during consolidation)                                                                   |
| `cmte_id`              | string | Committee identification (9-character code, consistent across cycles)                                         |
| `cmte_nm`              | string | Committee name                                                                                                |
| `tres_nm`              | string | Treasurer's name                                                                                              |
| `cmte_st1`             | string | Street address                                                                                                |
| `cmte_st2`             | string | Street address 2                                                                                              |
| `cmte_city`            | string | City                                                                                                          |
| `cmte_st`              | string | State                                                                                                         |
| `cmte_zip`             | string | ZIP code                                                                                                      |
| `cmte_dsgn`            | string | Designation (A=Authorized, B=Lobbyist PAC, D=Leadership PAC, J=Joint fundraiser, P=Principal, U=Unauthorized) |
| `cmte_tp`              | string | Committee type code                                                                                           |
| `cmte_pty_affiliation` | string | Party affiliation code                                                                                        |
| `cmte_filing_freq`     | string | Filing frequency (A=Terminated, D=Debt, M=Monthly, Q=Quarterly, T=Terminated, W=Waived)                       |
| `org_tp`               | string | Interest group category (C=Corporation, L=Labor, M=Membership, T=Trade, V=Cooperative, W=Corp without stock)  |
| `connected_org_nm`     | string | Connected organization's name                                                                                 |
| `cand_id`              | string | Candidate ID (for H, S, or P committee types)                                                                 |

---

### all_candidate_summaries_1980-2026.csv

Summary financial information for each candidate who raised or spent money during the period, regardless of when they are up for election. One record per candidate per election cycle.

**Source**: https://www.fec.gov/campaign-finance-data/all-candidates-file-description/

| Column                   | Type    | Description                                   |
| ------------------------ | ------- | --------------------------------------------- |
| `year`                   | int     | Election cycle (added during consolidation)   |
| `cand_id`                | string  | Candidate identification (9-character code)   |
| `cand_name`              | string  | Candidate name                                |
| `cand_ici`               | string  | Incumbent/challenger status (I/C/O)           |
| `pty_cd`                 | string  | Party code                                    |
| `cand_pty_affiliation`   | string  | Party affiliation                             |
| `ttl_receipts`           | decimal | Total receipts                                |
| `trans_from_auth`        | decimal | Transfers from authorized committees          |
| `ttl_disb`               | decimal | Total disbursements                           |
| `trans_to_auth`          | decimal | Transfers to authorized committees            |
| `coh_bop`                | decimal | Cash on hand - beginning of period            |
| `coh_cop`                | decimal | Cash on hand - close of period                |
| `cand_contrib`           | decimal | Contributions from candidate                  |
| `cand_loans`             | decimal | Loans from candidate                          |
| `other_loans`            | decimal | Other loans                                   |
| `cand_loan_repay`        | decimal | Candidate loan repayments                     |
| `other_loan_repay`       | decimal | Other loan repayments                         |
| `debts_owed_by`          | decimal | Debts owed by committee                       |
| `ttl_indiv_contrib`      | decimal | Total individual contributions                |
| `cand_office_st`         | string  | Candidate state                               |
| `cand_office_district`   | string  | Candidate district                            |
| `spec_election`          | string  | Special election status                       |
| `prim_election`          | string  | Primary election status                       |
| `run_election`           | string  | Runoff election status                        |
| `gen_election`           | string  | General election status                       |
| `gen_election_precent`   | decimal | General election percentage                   |
| `other_pol_cmte_contrib` | decimal | Contributions from other political committees |
| `pol_pty_contrib`        | decimal | Contributions from party committees           |
| `cvg_end_dt`             | date    | Coverage end date                             |
| `indiv_refunds`          | decimal | Refunds to individuals                        |
| `cmte_refunds`           | decimal | Refunds to committees                         |

**Note**: A candidate's financial summary may have double-counted activity if they have multiple authorized committees. Subtract `trans_from_auth` and `trans_to_auth` from totals for more accurate values.

---

### house_senate_campaign_summaries_1996-2026.csv

Summary financial information for House and Senate campaign committees only. One record per campaign committee per election cycle.

**Source**: https://www.fec.gov/campaign-finance-data/current-campaigns-house-and-senate-file-description/

| Column                   | Type    | Description                                   |
| ------------------------ | ------- | --------------------------------------------- |
| `year`                   | int     | Election cycle (added during consolidation)   |
| `cand_id`                | string  | Candidate identification                      |
| `cand_name`              | string  | Candidate name                                |
| `cand_ici`               | string  | Incumbent/challenger status                   |
| `pty_cd`                 | string  | Party code                                    |
| `cand_pty_affiliation`   | string  | Party affiliation                             |
| `ttl_receipts`           | decimal | Total receipts                                |
| `trans_from_auth`        | decimal | Transfers from authorized committees          |
| `ttl_disb`               | decimal | Total disbursements                           |
| `trans_to_auth`          | decimal | Transfers to authorized committees            |
| `coh_bop`                | decimal | Cash on hand - beginning of period            |
| `coh_cop`                | decimal | Cash on hand - close of period                |
| `cand_contrib`           | decimal | Contributions from candidate                  |
| `cand_loans`             | decimal | Loans from candidate                          |
| `other_loans`            | decimal | Other loans                                   |
| `cand_loan_repay`        | decimal | Candidate loan repayments                     |
| `other_loan_repay`       | decimal | Other loan repayments                         |
| `debts_owed_by`          | decimal | Debts owed by                                 |
| `ttl_indiv_contrib`      | decimal | Total individual contributions                |
| `cand_office_st`         | string  | Candidate state                               |
| `cand_office_district`   | string  | Candidate district                            |
| `spec_election`          | string  | Special election status                       |
| `prim_election`          | string  | Primary election status                       |
| `run_election`           | string  | Runoff election status                        |
| `gen_election`           | string  | General election status                       |
| `gen_election_precent`   | decimal | General election percentage                   |
| `other_pol_cmte_contrib` | decimal | Contributions from other political committees |
| `pol_pty_contrib`        | decimal | Contributions from party committees           |
| `cvg_end_dt`             | date    | Coverage end date                             |
| `indiv_refunds`          | decimal | Refunds to individuals                        |
| `cmte_refunds`           | decimal | Refunds to committees                         |

**Note**: Election result data (spec_election, prim_election, etc.) only included in 1996-2006 files. Double-counting may occur if candidate has multiple authorized committees.

---

### pac_party_summaries_1996-2026.csv

Summary financial information for PACs and party committees. One record per committee per election cycle.

**Source**: https://www.fec.gov/campaign-finance-data/pac-and-party-summary-file-description/

| Column                   | Type    | Description                                   |
| ------------------------ | ------- | --------------------------------------------- |
| `year`                   | int     | Election cycle (added during consolidation)   |
| `cmte_id`                | string  | Committee identification                      |
| `cmte_nm`                | string  | Committee name                                |
| `cmte_tp`                | string  | Committee type                                |
| `cmte_dsgn`              | string  | Committee designation                         |
| `cmte_filing_freq`       | string  | Filing frequency                              |
| `ttl_receipts`           | decimal | Total receipts                                |
| `trans_from_aff`         | decimal | Transfers from affiliates                     |
| `indv_contrib`           | decimal | Contributions from individuals                |
| `other_pol_cmte_contrib` | decimal | Contributions from other political committees |
| `cand_contrib`           | decimal | Contributions from candidate (not applicable) |
| `cand_loans`             | decimal | Candidate loans (not applicable)              |
| `ttl_loans_received`     | decimal | Total loans received                          |
| `ttl_disb`               | decimal | Total disbursements                           |
| `tranf_to_aff`           | decimal | Transfers to affiliates                       |
| `indv_refunds`           | decimal | Refunds to individuals                        |
| `other_pol_cmte_refunds` | decimal | Refunds to other political committees         |
| `cand_loan_repay`        | decimal | Candidate loan repayments (not applicable)    |
| `loan_repay`             | decimal | Loan repayments                               |
| `coh_bop`                | decimal | Cash beginning of period                      |
| `coh_cop`                | decimal | Cash close of period                          |
| `debts_owed_by`          | decimal | Debts owed by                                 |
| `nonfed_trans_received`  | decimal | Nonfederal transfers received                 |
| `contrib_to_other_cmte`  | decimal | Contributions to other committees             |
| `ind_exp`                | decimal | Independent expenditures                      |
| `pty_coord_exp`          | decimal | Party coordinated expenditures                |
| `nonfed_share_exp`       | decimal | Nonfederal share expenditures                 |
| `cvg_end_dt`             | date    | Coverage end date                             |

---

### candidate_committee_links_2000-2026.csv

Links candidates to their authorized committees, showing the relationship between candidate IDs and committee IDs.

**Source**: https://www.fec.gov/campaign-finance-data/candidate-committee-linkage-file-description/

| Column             | Type   | Description                                                                                                                                           |
| ------------------ | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `year`             | int    | Election cycle (added during consolidation)                                                                                                           |
| `cand_id`          | string | Candidate identification (9-character code)                                                                                                           |
| `cand_election_yr` | int    | Candidate's election year                                                                                                                             |
| `fec_election_yr`  | int    | Active 2-year period                                                                                                                                  |
| `cmte_id`          | string | Committee identification (9-character code)                                                                                                           |
| `cmte_tp`          | string | Committee type code                                                                                                                                   |
| `cmte_dsgn`        | string | Committee designation (A=Authorized, B=Lobbyist/Registrant PAC, D=Leadership PAC, J=Joint fundraiser, P=Principal campaign committee, U=Unauthorized) |
| `linkage_id`       | string | Unique link ID                                                                                                                                        |

---

### committee_transaction_summaries_1980-2026.csv

Aggregated transactions from one committee to another, including contributions, transfers, and independent expenditures between PACs, party committees, and candidate committees.

**Source**: https://www.fec.gov/campaign-finance-data/any-transaction-one-committee-another-file-description/

| Column              | Type    | Description                                 |
| ------------------- | ------- | ------------------------------------------- |
| `election_cycle`    | int     | 2-year FEC reporting period (from filename) |
| `transaction_year`  | int     | Actual year from transaction date           |
| `source_cmte_id`    | string  | Committee making the transaction            |
| `dest_cmte_id`      | string  | Committee receiving the transaction         |
| `dest_name`         | string  | Name of receiving committee                 |
| `transaction_tp`    | string  | Transaction type code                       |
| `total_amount`      | decimal | Sum of transaction amounts                  |
| `transaction_count` | int     | Number of transactions aggregated           |

**Transaction Types**: 10J, 11J, 13, 15J, 15Z, 16C, 16F, 16G, 16R, 17R, 17Z, 18G, 18J, 18K, 18U, 19J, 20, 20C, 20F, 20G, 20R, 22H, 22Z, 23Y, 24A, 24C, 24E, 24F, 24G, 24H, 24K, 24N, 24P, 24R, 24U, 24Z, 29, and (from 2016) 30F, 30G, 30J, 30K, 31F, 31G, 31J, 31K, 32F, 32G, 32J, 32K, 40, 40Z, 41, 41Z, 42, 42Z

**Exclusions**:

- Memo transactions (`memo_cd = 'X'`) — 34.6M rows excluded
- Amended filings (`amndt_ind != 'N'`) — 5.2M rows excluded
- Duplicate `sub_id` values — 2 rows excluded

---

### committee_to_candidate_summaries_1980-2026.csv

Aggregated contributions and independent expenditures from committees (PACs, party committees, candidate committees) to candidates.

**Source**: https://www.fec.gov/campaign-finance-data/contributions-committees-candidates-file-description/

| Column              | Type    | Description                                 |
| ------------------- | ------- | ------------------------------------------- |
| `election_cycle`    | int     | 2-year FEC reporting period (from filename) |
| `transaction_year`  | int     | Actual year from transaction date           |
| `cmte_id`           | string  | Committee making the contribution           |
| `cmte_name`         | string  | Name of the committee                       |
| `cand_id`           | string  | Candidate receiving the contribution        |
| `transaction_tp`    | string  | Transaction type code                       |
| `total_amount`      | decimal | Sum of transaction amounts                  |
| `transaction_count` | int     | Number of transactions aggregated           |

**Transaction Types**: 24A, 24C, 24E, 24F, 24H, 24K, 24N, 24P, 24R, 24Z

**Exclusions**:

- Memo transactions (`memo_cd = 'X'`) — 88.5K rows excluded
- Amended filings (`amndt_ind != 'N'`) — 2.9M rows excluded

---

### expenditures_by_category_2004-2026.csv

Committee spending aggregated by disbursement category.

**Source**: https://www.fec.gov/campaign-finance-data/operating-expenditures-file-description/

| Column              | Type    | Description                                   |
| ------------------- | ------- | --------------------------------------------- |
| `election_cycle`    | int     | 2-year FEC reporting period                   |
| `transaction_year`  | int     | Actual year from transaction date             |
| `cmte_id`           | string  | Committee making the expenditure              |
| `category`          | string  | Disbursement category code (001-012, 101-107) |
| `category_desc`     | string  | Category description                          |
| `total_amount`      | decimal | Sum of transaction amounts                    |
| `transaction_count` | int     | Number of transactions aggregated             |

**Exclusions**:

- Memo transactions (`memo_cd = 'X'`) — 5.1M rows excluded
- Amended filings (`amndt_ind != 'N'`) — 6.5M rows excluded

---

### expenditures_by_state_2004-2026.csv

Committee spending aggregated by payee state (geographic distribution).

**Source**: https://www.fec.gov/campaign-finance-data/operating-expenditures-file-description/

| Column              | Type    | Description                       |
| ------------------- | ------- | --------------------------------- |
| `election_cycle`    | int     | 2-year FEC reporting period       |
| `transaction_year`  | int     | Actual year from transaction date |
| `cmte_id`           | string  | Committee making the expenditure  |
| `state`             | string  | State where payee is located      |
| `total_amount`      | decimal | Sum of transaction amounts        |
| `transaction_count` | int     | Number of transactions aggregated |

**Exclusions**:

- Memo transactions (`memo_cd = 'X'`) — 5.1M rows excluded
- Amended filings (`amndt_ind != 'N'`) — 6.5M rows excluded

---

## Reference Data

### Expenditure Category Codes

| Code | Description                             |
| ---- | --------------------------------------- |
| 001  | Administrative/Salary/Overhead Expenses |
| 002  | Travel Expenses                         |
| 003  | Solicitation and Fundraising Expenses   |
| 004  | Advertising Expenses                    |
| 005  | Polling Expenses                        |
| 006  | Campaign Materials                      |
| 007  | Campaign Event Expenses                 |
| 008  | Transfers                               |
| 009  | Loan Repayments                         |
| 010  | Refunds                                 |
| 011  | Contributions                           |
| 012  | Other Expenses                          |

### Committee Type Codes (`cmte_tp`)

| Code | Description                                      |
| ---- | ------------------------------------------------ |
| C    | Communication Cost                               |
| D    | Delegate Committee                               |
| E    | Electioneering Communication                     |
| H    | House                                            |
| I    | Independent Expenditure (Not a Committee)        |
| N    | PAC - Nonqualified                               |
| O    | Independent Expenditure-Only (Super PAC)         |
| P    | Presidential                                     |
| Q    | PAC - Qualified                                  |
| S    | Senate                                           |
| U    | Single Candidate Independent Expenditure         |
| V    | PAC with Non-Contribution Account - Nonqualified |
| W    | PAC with Non-Contribution Account - Qualified    |
| X    | Party - Nonqualified                             |
| Y    | Party - Qualified                                |
| Z    | National Party Nonfederal Account                |

### Committee Designation Codes (`cmte_dsgn`)

| Code | Description                  |
| ---- | ---------------------------- |
| A    | Authorized by a candidate    |
| B    | Lobbyist/Registrant PAC      |
| D    | Leadership PAC               |
| J    | Joint fundraiser             |
| P    | Principal campaign committee |
| U    | Unauthorized                 |

### Party Codes

| Code | Party              |
| ---- | ------------------ |
| DEM  | Democratic Party   |
| REP  | Republican Party   |
| IND  | Independent        |
| LIB  | Libertarian Party  |
| GRE  | Green Party        |
| CON  | Constitution Party |
| REF  | Reform Party       |

### Incumbent/Challenger Status (`cand_ici`)

| Code | Status     |
| ---- | ---------- |
| I    | Incumbent  |
| C    | Challenger |
| O    | Open Seat  |

### Office Codes (`cand_office`)

| Code | Office    |
| ---- | --------- |
| H    | House     |
| S    | Senate    |
| P    | President |

---

## Data Sources

All data sourced from the Federal Election Commission (FEC):

- Main site: https://www.fec.gov/
- Bulk data: https://www.fec.gov/data/browse-data/
- API: https://api.open.fec.gov/developers/

**Last Updated**: Data covers election cycles 1980-2026 (varies by table)
