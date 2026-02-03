Source: https://www.fec.gov/campaign-finance-data/operating-expenditures-file-description/

# Operating Expenditures (2004-2026)

Two summary files aggregating committee spending:

## expenditures_by_category_2004-2026.csv

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

### Category Codes

The FEC defines two sets of disbursement category codes: standard codes (001-012) for non-presidential filers and presidential codes (101-107) for presidential campaign committees.

#### Standard Codes (001-012) — Non-Presidential Filers

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

#### Presidential Codes (101-107) — Presidential Filers

| Code | Description |
|------|-------------|
| 101 | Non-Allocable Expenses |
| 102 | Media Expenditures |
| 103 | Mass Mailings and Campaign Materials |
| 104 | State Office Overhead Expenses |
| 105 | Special Telephone Program Expenditures |
| 106 | Public Opinion Poll Expenditures |
| 107 | Fundraising Expenditures |

#### Other Codes Found in Data

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

## expenditures_by_state_2004-2026.csv

Spending aggregated by payee state (geographic distribution).

| Column | Description |
|--------|-------------|
| `election_cycle` | 2-year FEC reporting period |
| `transaction_year` | Actual year from transaction date |
| `cmte_id` | Committee making the expenditure |
| `state` | State where payee is located |
| `total_amount` | Sum of transaction amounts |
| `transaction_count` | Number of transactions aggregated |

## Exclusions

To prevent double-counting:
- Memo transactions (`memo_cd = 'X'`) — 5.1M rows excluded
- Amended filings (`amndt_ind != 'N'`) — 6.5M rows excluded
