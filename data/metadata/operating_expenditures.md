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
| 010 | Refunds |
| 011 | Contributions |
| 012 | Other Expenses |

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
