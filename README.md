# FEC Bulk Data

This repository contains bulk data files downloaded from the Federal Election Commission (FEC). The data covers federal campaign finance records from 1980 to 2026.

**Total size: 581 MB**

---

## Data Preparation Steps

The following steps were taken to prepare this dataset:

1. Downloaded all `.zip` files from the FEC bulk data page (https://www.fec.gov/data/browse-data/?tab=bulk-data)
2. Extracted zip files into category-based folders
3. Flattened extracted contents, removing intermediate directories
4. Deleted the original `.zip` files after extraction
5. Renamed files from `weball00.txt` format to `2000_weball.txt` format
6. Created `metadata/` subfolder in each directory
7. Downloaded `header.csv` files from FEC for each category
8. Downloaded data description pages from FEC and saved as `description.md`
9. Converted all pipe-delimited `.txt` files to proper CSV format
10. Prepended header rows to CSV files
11. For categories missing header files, extracted column names from `description.md`
12. Ran audit to verify CSV conversion integrity
13. Deleted original `.txt` files after successful CSV conversion
14. Combined individual year CSVs into single files for directories under 500 MB
15. Deleted individual year files from combined directories
16. Created summarized committee_transactions file (excludes memos, amendments, duplicates)
17. Deleted original committee_transactions year files
18. Created summarized contributions_from_committees file
19. Deleted original contributions_from_committees year files
20. Created two summarized operating_expenditures files (by category and by state)
21. Deleted original operating_expenditures year files
22. Converted all CSV headers to snake_case
23. Flattened directory structure: moved all CSVs to `data/` root, consolidated metadata

---

## File Structure

```
data/
├── all_candidate_summaries_1980-2026.csv           8.5 MB
├── candidate_committee_links_2000-2026.csv         3.6 MB
├── candidate_registrations_1980-2026.csv           13 MB
├── committee_registrations_1980-2026.csv           38 MB
├── committee_to_candidate_summaries_1980-2026.csv  202 MB
├── committee_transaction_summaries_1980-2026.csv   271 MB
├── expenditures_by_category_2004-2026.csv          6.1 MB
├── expenditures_by_state_2004-2026.csv             9.3 MB
├── house_senate_campaign_summaries_1996-2026.csv   4.3 MB
├── pac_party_summaries_1996-2026.csv               17 MB
└── metadata/
    ├── all_candidate_summaries.md
    ├── candidate_committee_links.md
    ├── candidate_registrations.md
    ├── committee_registrations.md
    ├── committee_to_candidate_summaries.md
    ├── committee_transaction_summaries.md
    ├── house_senate_campaign_summaries.md
    ├── operating_expenditures.md
    └── pac_party_summaries.md
```

---

## Data Files

### Combined Files

These files combine all election cycles with a `year` column added:

| File | Years | Rows | Description |
|------|-------|------|-------------|
| `all_candidate_summaries_1980-2026.csv` | 1980-2026 | 69,349 | Financial summaries for all candidates |
| `candidate_registrations_1980-2026.csv` | 1980-2026 | 129,198 | Basic candidate registration info |
| `candidate_committee_links_2000-2026.csv` | 2000-2026 | 81,275 | Links between candidates and committees |
| `committee_registrations_1980-2026.csv` | 1980-2026 | 295,946 | Basic committee registration info |
| `house_senate_campaign_summaries_1996-2026.csv` | 1996-2026 | 32,192 | House/Senate campaign financials |
| `pac_party_summaries_1996-2026.csv` | 1996-2026 | 139,884 | PAC and party committee financials |

### Aggregated Transaction Files

These files summarize itemized transactions with strict deduplication:

| File | Years | Rows | Description |
|------|-------|------|-------------|
| `committee_transaction_summaries_1980-2026.csv` | 1980-2026 | 3,752,745 | Committee-to-committee transactions |
| `committee_to_candidate_summaries_1980-2026.csv` | 1980-2026 | 2,793,458 | Committee contributions to candidates |
| `expenditures_by_category_2004-2026.csv` | 2004-2026 | 129,311 | Spending by disbursement category |
| `expenditures_by_state_2004-2026.csv` | 2004-2026 | 318,655 | Spending by payee state |

**Exclusions to prevent double-counting:**
- Memo transactions (`memo_cd = 'X'`)
- Amended filings (`amndt_ind != 'N'`)
- Duplicate `sub_id` values

---

## File Descriptions

### all_candidate_summaries_1980-2026.csv

Financial summaries for each candidate who raised or spent money. Includes total receipts, disbursements, cash-on-hand, loans, debts, and contributions.

### candidate_registrations_1980-2026.csv

Basic info for each registered candidate: ID, name, party, office sought, district, incumbent/challenger status, principal campaign committee.

### candidate_committee_links_2000-2026.csv

Links candidates to their authorized committees with committee type and designation.

### committee_registrations_1980-2026.csv

Basic info for each registered committee: ID, name, treasurer, address, type, designation, filing frequency, connected organization.

### house_senate_campaign_summaries_1996-2026.csv

Financial summaries specifically for House and Senate campaign committees.

### pac_party_summaries_1996-2026.csv

Financial summaries for PACs and party committees, including contributions, transfers, independent expenditures.

### committee_transaction_summaries_1980-2026.csv

Aggregated committee-to-committee transactions grouped by election cycle, transaction year, source committee, destination committee, and transaction type.

### committee_to_candidate_summaries_1980-2026.csv

Aggregated committee-to-candidate contributions grouped by election cycle, transaction year, committee, candidate, and transaction type.

### expenditures_by_category_2004-2026.csv

Committee spending aggregated by disbursement category (advertising, payroll, travel, etc.).

### expenditures_by_state_2004-2026.csv

Committee spending aggregated by payee state for geographic analysis.

---

## Metadata

Each CSV file has a corresponding markdown file in `data/metadata/` with:
- Source URL
- Column definitions
- Notes on data exclusions and aggregation methodology

---

## Source

All data downloaded from: https://www.fec.gov/data/browse-data/?tab=bulk-data

## Notes

- All CSV headers are in `snake_case` format
- Combined files include a `year` or `election_cycle` column to identify the reporting period
- Aggregated files include `transaction_year` (actual year from transaction date)
- See `metadata/*.md` files for full column definitions
- Some financial data may be double-counted when candidates have multiple authorized committees
