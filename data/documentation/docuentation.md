# FEC Campaign Finance Data Documentation

Consolidated documentation for FEC campaign finance data files (1980-2026).

---

## Table of Contents

1. [Candidate Data](#candidate-data)
   - [Candidate Registrations](#candidate-registrations-1980-2026)
   - [All Candidate Summaries](#all-candidate-summaries-1980-2026)
   - [House & Senate Campaign Summaries](#house--senate-campaign-summaries-1996-2026)
   - [Candidate-Committee Links](#candidate-committee-links-2000-2026)
2. [Committee Data](#committee-data)
   - [Committee Registrations](#committee-registrations-1980-2026)
   - [PAC & Party Summaries](#pac--party-summaries-1996-2026)
3. [Contribution Data](#contribution-data)
   - [Individual Contributions](#individual-contributions-1980-2026)
   - [Candidate Individual Contribution Summaries](#candidate-individual-contribution-summaries-1980-2026)
   - [Committee to Candidate Summaries](#committee-to-candidate-summaries-1980-2026)
   - [Committee Transaction Summaries](#committee-transaction-summaries-1980-2026)
4. [Expenditure Data](#expenditure-data)
   - [Operating Expenditures](#operating-expenditures-2004-2026)
5. [Reference Data](#reference-data)
   - [Bioguide Crosswalk](#bioguide-crosswalk)

---

# Candidate Data

## Candidate Registrations (1980-2026)

Source: https://www.fec.gov/campaign-finance-data/candidate-master-file-description/

**File:** `candidate_registrations_1980-2026.csv`

Basic information for each candidate registered with the FEC, including candidates who filed a Statement of Candidacy, have active campaign committees, or are referenced by draft/nonconnected committees.

### Columns

| Column | Description |
|--------|-------------|
| `election_cycle` | 2-year FEC reporting period (added during consolidation) |
| `cand_id` | Candidate identification (9-character code, consistent across cycles for same office) |
| `cand_name` | Candidate name |
| `cand_pty_affiliation` | Party affiliation code |
| `cand_election_yr` | Year of election |
| `cand_office_st` | State (House=state of race, Senate=state of race, President=US) |
| `cand_office` | Office sought (H=House, P=President, S=Senate) |
| `cand_office_district` | Congressional district (00 for at-large, Senate, Presidential) |
| `cand_ici` | Incumbent/challenger status (C=Challenger, I=Incumbent, O=Open Seat) |
| `cand_status` | Candidate status (C=Statutory, F=Future, N=Not yet, P=Prior cycle) |
| `cand_pcc` | Principal campaign committee ID |
| `cand_st1` | Mailing address - street |
| `cand_st2` | Mailing address - street 2 |
| `cand_city` | Mailing address - city |
| `cand_st` | Mailing address - state |
| `cand_zip` | Mailing address - ZIP code |

---

## All Candidate Summaries (1980-2026)

Source: https://www.fec.gov/campaign-finance-data/all-candidates-file-description/

**File:** `all_candidate_summaries_1980-2026.csv`

Summary financial information for each candidate who raised or spent money during the period, regardless of when they are up for election. One record per candidate per election cycle.

### Columns

| Column | Description |
|--------|-------------|
| `election_cycle` | 2-year FEC reporting period (added during consolidation) |
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

### Notes

- A candidate's financial summary may have double-counted activity if they have multiple authorized committees
- Subtract `trans_from_auth` and `trans_to_auth` from totals for more accurate values

---

## House & Senate Campaign Summaries (1996-2026)

Source: https://www.fec.gov/campaign-finance-data/current-campaigns-house-and-senate-file-description/

**File:** `house_senate_campaign_summaries_1996-2026.csv`

Summary financial information for House and Senate campaign committees only. One record per campaign committee per election cycle.

### Columns

| Column | Description |
|--------|-------------|
| `election_cycle` | 2-year FEC reporting period (added during consolidation) |
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

### Notes

- Election result data (spec_election, prim_election, etc.) only included in 1996-2006 files
- Double-counting may occur if candidate has multiple authorized committees

---

## Candidate-Committee Links (2000-2026)

Source: https://www.fec.gov/campaign-finance-data/candidate-committee-linkage-file-description/

**File:** `candidate_committee_links_2000-2026.csv`

Links candidates to their authorized committees, showing the relationship between candidate IDs and committee IDs.

### Columns

| Column | Description |
|--------|-------------|
| `election_cycle` | 2-year FEC reporting period (added during consolidation) |
| `cand_id` | Candidate identification (9-character code) |
| `cand_election_yr` | Candidate's election year |
| `fec_election_yr` | Active 2-year period |
| `cmte_id` | Committee identification (9-character code) |
| `cmte_tp` | Committee type code |
| `cmte_dsgn` | Committee designation (A=Authorized, B=Lobbyist/Registrant PAC, D=Leadership PAC, J=Joint fundraiser, P=Principal campaign committee, U=Unauthorized) |
| `linkage_id` | Unique link ID |

---

# Committee Data

## Committee Registrations (1980-2026)

Source: https://www.fec.gov/campaign-finance-data/committee-master-file-description/

**File:** `committee_registrations_1980-2026.csv`

Basic information for each committee registered with the FEC, including PACs, party committees, and campaign committees.

### Columns

| Column | Description |
|--------|-------------|
| `election_cycle` | 2-year FEC reporting period (added during consolidation) |
| `cmte_id` | Committee identification (9-character code, consistent across cycles) |
| `cmte_nm` | Committee name |
| `tres_nm` | Treasurer's name |
| `cmte_st1` | Street address |
| `cmte_st2` | Street address 2 |
| `cmte_city` | City |
| `cmte_st` | State |
| `cmte_zip` | ZIP code |
| `cmte_dsgn` | Designation (A=Authorized, B=Lobbyist PAC, D=Leadership PAC, J=Joint fundraiser, P=Principal, U=Unauthorized) |
| `cmte_tp` | Committee type code |
| `cmte_pty_affiliation` | Party affiliation code |
| `cmte_filing_freq` | Filing frequency (A=Terminated, D=Debt, M=Monthly, Q=Quarterly, T=Terminated, W=Waived) |
| `org_tp` | Interest group category (C=Corporation, L=Labor, M=Membership, T=Trade, V=Cooperative, W=Corp without stock) |
| `connected_org_nm` | Connected organization's name |
| `cand_id` | Candidate ID (for H, S, or P committee types) |

---

## PAC & Party Summaries (1996-2026)

Source: https://www.fec.gov/campaign-finance-data/pac-and-party-summary-file-description/

**File:** `pac_party_summaries_1996-2026.csv`

Summary financial information for PACs and party committees. One record per committee per election cycle.

### Columns

| Column | Description |
|--------|-------------|
| `election_cycle` | 2-year FEC reporting period (added during consolidation) |
| `cmte_id` | Committee identification |
| `cmte_nm` | Committee name |
| `cmte_tp` | Committee type |
| `cmte_dsgn` | Committee designation |
| `cmte_filing_freq` | Filing frequency |
| `ttl_receipts` | Total receipts |
| `trans_from_aff` | Transfers from affiliates |
| `indv_contrib` | Contributions from individuals |
| `other_pol_cmte_contrib` | Contributions from other political committees |
| `cand_contrib` | Contributions from candidate (not applicable) |
| `cand_loans` | Candidate loans (not applicable) |
| `ttl_loans_received` | Total loans received |
| `ttl_disb` | Total disbursements |
| `tranf_to_aff` | Transfers to affiliates |
| `indv_refunds` | Refunds to individuals |
| `other_pol_cmte_refunds` | Refunds to other political committees |
| `cand_loan_repay` | Candidate loan repayments (not applicable) |
| `loan_repay` | Loan repayments |
| `coh_bop` | Cash beginning of period |
| `coh_cop` | Cash close of period |
| `debts_owed_by` | Debts owed by |
| `nonfed_trans_received` | Nonfederal transfers received |
| `contrib_to_other_cmte` | Contributions to other committees |
| `ind_exp` | Independent expenditures |
| `pty_coord_exp` | Party coordinated expenditures |
| `nonfed_share_exp` | Nonfederal share expenditures |
| `cvg_end_dt` | Coverage end date |

---

# Contribution Data

## Individual Contributions (1980-2026)

Source: https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/

**Directory:** `individual_contributions/`

Itemized contributions from individuals to federal political committees. Files are split by election cycle (e.g., `1980_individual_contributions.csv`).

### Columns

| Column | Description |
|--------|-------------|
| `election_cycle` | 2-year FEC reporting period (added during processing) |
| `transaction_year` | Year extracted from transaction date (added during processing) |
| `cmte_id` | 9-character committee ID receiving the contribution |
| `amndt_ind` | Amendment indicator: N=New, A=Amended, T=Termination |
| `rpt_tp` | Report type (e.g., M3=March monthly, Q1=1st quarter, 12G=general pre-election) |
| `transaction_pgi` | Election type: P=Primary, G=General, O=Other, C=Convention, R=Runoff, S=Special, E=Recount |
| `image_num` | Microfilm/document reference number (11-digit legacy or 18-digit from June 2015+) |
| `transaction_tp` | Transaction type code (see below) |
| `entity_tp` | Entity type: IND=Individual, CAN=Candidate, CCM=Candidate Committee, COM=Committee, ORG=Organization, PAC=PAC, PTY=Party (electronic filings only, post-April 2002) |
| `name` | Contributor name (format: LAST, FIRST) |
| `city` | Contributor city |
| `state` | Contributor 2-letter state code |
| `zip_code` | Contributor ZIP code (5 or 9 digits) |
| `employer` | Contributor's employer |
| `occupation` | Contributor's occupation |
| `transaction_dt` | Transaction date (MMDDYYYY format) |
| `transaction_amt` | Contribution amount in dollars |
| `other_id` | For earmarked contributions: FEC ID of the recipient committee |
| `tran_id` | Unique transaction identifier (electronic filings only) |
| `file_num` | Unique report/filing number |
| `memo_cd` | X=Transaction is a memo (subtransaction or earmark detail) |
| `memo_text` | Additional description (often shows earmark destination) |
| `sub_id` | Unique FEC record identifier |

### Common Transaction Types

| Code | Description |
|------|-------------|
| 10 | Non-Federal Receipt from Persons |
| 10J | Memo: Non-Federal Receipt from Persons |
| 11 | Tribal Contribution |
| 15 | Contribution |
| 15C | Contribution from Candidate |
| 15E | Earmarked Contribution |
| 15J | Memo: Contribution to Joint Fundraising Committee |
| 20Y | Nonfederal Refund |
| 22Y | Refund to Individual |
| 24I | Earmarked Intermediary In |
| 24T | Earmarked Intermediary Out (pass-through) |
| 30 | Convention Registration Fee (2016+) |
| 30T | Memo: Convention Registration Fee (2016+) |
| 31 | Convention Host Registration Fee (2016+) |
| 31T | Memo: Convention Host Registration Fee (2016+) |
| 32 | Convention Account Donation (2016+) |
| 32T | Memo: Convention Account Donation (2016+) |

### Itemization Thresholds

Contributions are only itemized (included in this file) above certain thresholds:

| Period | Threshold | Calculation |
|--------|-----------|-------------|
| 2015–present | >$200 | Election cycle-to-date (candidates) or calendar year-to-date (PACs/parties) |
| 1989–2014 | ≥$200 | Per reporting period |
| 1975–1988 | ≥$500 | Per reporting period |

Smaller contributions are reported only as aggregate unitemized totals in committee summary filings.

### Data Quality Notes

- **Entity type (`entity_tp`)**: Only populated for electronic filings after April 2002; blank in older records
- **Employer/occupation**: More consistently reported in recent years; often blank or generic in 1980s data
- **ZIP codes**: May be incomplete (sometimes just "0") in early years
- **Memo transactions**: Records with `memo_cd = 'X'` are subtransactions that should not be summed with regular transactions to avoid double-counting

### File Statistics

| Cycle | Rows | File Size |
|-------|------|-----------|
| 1980 | 309K | 38 MB |
| 1982 | 169K | 21 MB |
| 1984 | 259K | 31 MB |
| 1986 | 279K | 34 MB |
| 1988 | 433K | 53 MB |
| 1990 | 530K | 65 MB |
| 1992 | 888K | 107 MB |
| 1994 | 839K | 102 MB |
| 1996 | 1.2M | 149 MB |
| 1998 | 1.0M | 123 MB |
| 2000 | 1.7M | 208 MB |
| 2002 | 1.4M | 182 MB |
| 2004 | 2.5M | 368 MB |
| 2006 | 1.8M | 285 MB |
| 2008 | 3.4M | 535 MB |
| 2010 | 2.1M | 338 MB |
| 2012 | 3.4M | 544 MB |
| 2014 | 2.2M | 368 MB |
| 2016 | 20.5M | 3.7 GB |
| 2018 | 21.7M | 4.1 GB |
| 2020 | 69.4M | 13 GB |
| 2022 | 63.9M | 12 GB |
| 2024 | 58.2M | 11 GB |
| 2026 | 13.2M | 2.4 GB |

**Total:** ~271M rows, 49 GB

The dramatic increase in 2016+ reflects the rise of small-dollar online fundraising platforms like ActBlue and WinRed. The 2020 cycle shows an exceptional surge in individual contributions during a high-turnout presidential election.

---

## Candidate Individual Contribution Summaries (1980-2026)

**File:** `data/candidate_individual_contribution_summaries_1980-2026.csv`

Aggregated individual contributions per candidate, grouped by election cycle and transaction year. For the 2026 cycle, data is further grouped by month to enable tracking of in-progress fundraising.

### Data Flow

```
individual_contributions (cmte_id)
    ↓ join on cmte_id + election_cycle
committee_registrations (cand_id)
    ↓ group by cand_id
candidate_individual_contribution_summaries (output)
```

Only candidate committees (types H, S, P) have a `cand_id`. Contributions to PACs and party committees are not included in this summary.

### Columns

| Column | Description |
|--------|-------------|
| `election_cycle` | 2-year FEC reporting period |
| `transaction_year` | Year extracted from transaction date |
| `transaction_month` | Month (1-12) for 2026 cycle only; NULL for all other cycles |
| `cand_id` | FEC candidate ID |
| `bioguide_id` | Congressional Bioguide ID, expanded via name matching (NULL if candidate never served in Congress) |
| `total_raised` | Sum of contribution amounts in dollars |
| `transaction_count` | Number of individual contributions |

### Filtering Applied

The following filters are applied to avoid double-counting:

- **Memos excluded**: Records with `memo_cd = 'X'` are subtransactions
- **Amendments excluded**: Only records with `amndt_ind = 'N'` (new) are included
- **Deduplicated**: Unique by `sub_id` to prevent counting the same transaction twice

### Usage Notes

- Join with `candidate_registrations_1980-2026.csv` on `cand_id` to get candidate names and party
- Join with `cand_id_bioguide_crosswalk.csv` on `cand_id` to link to Congressional Bioguide IDs
- The 2026 cycle includes monthly breakdowns (`transaction_month`) for tracking ongoing fundraising
- For historical cycles (1980-2024), `transaction_month` is NULL

### Example Queries

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

### Relationship to Other Files

- **Source data**: `individual_contributions/*.csv` (itemized contributions)
- **Committee mapping**: `committee_registrations_1980-2026.csv` (cmte_id → cand_id)
- **Candidate details**: `candidate_registrations_1980-2026.csv` (names, party, state)
- **Financial summaries**: `all_candidate_summaries_1980-2026.csv` (broader financial data including PAC contributions)

---

## Committee to Candidate Summaries (1980-2026)

Source: https://www.fec.gov/campaign-finance-data/contributions-committees-candidates-file-description/

**File:** `committee_to_candidate_summaries_1980-2026.csv`

Aggregated contributions and independent expenditures from committees (PACs, party committees, candidate committees) to candidates.

### Columns

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

### Transaction Types

Includes types: 24A, 24C, 24E, 24F, 24H, 24K, 24N, 24P, 24R, 24Z

### Exclusions

To prevent double-counting:
- Memo transactions (`memo_cd = 'X'`) — 88.5K rows excluded
- Amended filings (`amndt_ind != 'N'`) — 2.9M rows excluded

---

## Committee Transaction Summaries (1980-2026)

Source: https://www.fec.gov/campaign-finance-data/any-transaction-one-committee-another-file-description/

**File:** `committee_transaction_summaries_1980-2026.csv`

Aggregated transactions from one committee to another, including contributions, transfers, and independent expenditures between PACs, party committees, and candidate committees.

### Columns

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

### Transaction Types

Includes types: 10J, 11J, 13, 15J, 15Z, 16C, 16F, 16G, 16R, 17R, 17Z, 18G, 18J, 18K, 18U, 19J, 20, 20C, 20F, 20G, 20R, 22H, 22Z, 23Y, 24A, 24C, 24E, 24F, 24G, 24H, 24K, 24N, 24P, 24R, 24U, 24Z, 29, and (from 2016) 30F, 30G, 30J, 30K, 31F, 31G, 31J, 31K, 32F, 32G, 32J, 32K, 40, 40Z, 41, 41Z, 42, 42Z.

### Exclusions

To prevent double-counting:
- Memo transactions (`memo_cd = 'X'`) — 34.6M rows excluded
- Amended filings (`amndt_ind != 'N'`) — 5.2M rows excluded
- Duplicate `sub_id` values — 2 rows excluded

---

# Expenditure Data

## Operating Expenditures (2004-2026)

Source: https://www.fec.gov/campaign-finance-data/operating-expenditures-file-description/

Two summary files aggregating committee spending:

### expenditures_by_category_2004-2026.csv

Spending aggregated by disbursement category.

| Column | Description |
|--------|-------------|
| `election_cycle` | 2-year FEC reporting period |
| `transaction_year` | Actual year from transaction date |
| `cmte_id` | Committee making the expenditure |
| `category` | Disbursement category code (001-012, 101-107) |
| `category_desc` | Category description |
| `total_amount` | Sum of transaction amounts |
| `transaction_count` | Number of transactions aggregated |

#### Category Codes

The FEC defines two sets of disbursement category codes: standard codes (001-012) for non-presidential filers and presidential codes (101-107) for presidential campaign committees.

##### Standard Codes (001-012) — Non-Presidential Filers

| Code | Description |
|------|-------------|
| 001 | Administrative/Salary/Overhead Expenses |
| 002 | Travel Expenses |
| 003 | Solicitation and Fundraising Expenses |
| 004 | Advertising Expenses |
| 005 | Polling Expenses |
| 006 | Campaign Materials |
| 007 | Campaign Event Expenses |
| 008 | Transfers |
| 009 | Loan Repayments |
| 010 | Refunds of Contributions |
| 011 | Political Contributions |
| 012 | Donations |

##### Presidential Codes (101-107) — Presidential Filers

| Code | Description |
|------|-------------|
| 101 | Non-Allocable Expenses |
| 102 | Media Expenditures |
| 103 | Mass Mailings and Campaign Materials |
| 104 | State Office Overhead Expenses |
| 105 | Special Telephone Program Expenditures |
| 106 | Public Opinion Poll Expenditures |
| 107 | Fundraising Expenditures |

##### Other Codes Found in Data

The following codes appear in the source data but are not officially documented by the FEC. Most represent data entry errors, truncated codes, or legacy values with minimal transaction volume:

| Code | Notes |
|------|-------|
| 000 | Unclassified or missing category (~$3.7M total) |
| 100 | Likely intended as 101-107 series (~$1,600 total) |
| 013-029 | Non-standard codes, minimal amounts (<$150K combined) |
| 061-079 | Non-standard codes, minimal amounts (<$3K combined) |
| 211, 216, 266, 333 | Non-standard codes, minimal amounts (<$28K combined) |
| 601, 603, 700 | Non-standard codes, minimal amounts (<$1K combined) |
| Single/double digit codes (0-12, 00-07, etc.) | Truncated versions of standard codes |

**Note:** The `category_desc` field is empty for non-standard codes. For analysis purposes, these can generally be grouped with code 012 (Donations/Other) or excluded as data quality issues.

### expenditures_by_state_2004-2026.csv

Spending aggregated by payee state (geographic distribution).

| Column | Description |
|--------|-------------|
| `election_cycle` | 2-year FEC reporting period |
| `transaction_year` | Actual year from transaction date |
| `cmte_id` | Committee making the expenditure |
| `state` | State where payee is located |
| `total_amount` | Sum of transaction amounts |
| `transaction_count` | Number of transactions aggregated |

### Exclusions

To prevent double-counting:
- Memo transactions (`memo_cd = 'X'`) — 5.1M rows excluded
- Amended filings (`amndt_ind != 'N'`) — 6.5M rows excluded

---

# Reference Data

## Bioguide Crosswalk

Links FEC candidate IDs (`cand_id`) to Congressional Bioguide IDs (`bioguide_id`) for candidates who served in Congress.

### Source

Data sourced from: https://github.com/unitedstates/congress-legislators

The `@unitedstates/congress-legislators` repository is a community-maintained dataset of all U.S. Congress members since 1789, including their Bioguide IDs and FEC candidate IDs.

### Column Definitions

| Column | Description |
|--------|-------------|
| `cand_id` | FEC candidate ID (e.g., `H8CA05035`) |
| `bioguide_id` | Congressional Bioguide ID (e.g., `P000197`) |
| `match_method` | How the match was established |
| `confidence` | Confidence level of the match |

#### match_method values

| Value | Description |
|-------|-------------|
| `authoritative` | FEC ID from congress-legislators data, verified against FEC registrations |
| `authoritative_unverified` | FEC ID from congress-legislators data, not found in current FEC registrations (may be historical or contain typos) |

#### confidence values

| Value | Description |
|-------|-------------|
| `high` | Match verified against FEC candidate registration data |
| `medium` | Match from authoritative source but not verified in current FEC data |

### Important Notes

- **One bioguide_id can map to multiple cand_ids**: Members who served in both House and Senate (e.g., Ron Wyden) have separate FEC candidate IDs for each office
- **Only covers members who served in Congress**: Candidates who ran but never won do not have Bioguide IDs
- **Coverage**: ~1,700 cand_id mappings covering ~1,500 unique Congress members

### Usage Example

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

### Regenerating the Crosswalk

To update the crosswalk with the latest data:

```bash
python scripts/create_bioguide_crosswalk.py
```

The script fetches the current legislators data from GitHub and validates against FEC registrations.