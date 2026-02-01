# FEC Bulk Data Processing Guide

This document explains how to download and process FEC bulk campaign finance data, including the reasoning behind each decision and what to expect at each step.

---

## Overview

### What is this data?

The FEC (Federal Election Commission) publishes bulk data files containing federal campaign finance records. This includes:
- **Candidate information** - Who is running for office
- **Committee information** - PACs, party committees, campaign committees
- **Financial summaries** - How much candidates/committees raised and spent
- **Transaction details** - Individual contributions and expenditures

### Why process it?

The raw FEC data has several issues:
1. **Pipe-delimited format** - Not standard CSV, harder to work with
2. **Separate files per election cycle** - 24+ files per category spanning 1980-2026
3. **No headers in data files** - Headers are in separate files
4. **Inconsistent naming** - Files named `weball00.txt` instead of `2000_weball.txt`
5. **Double-counting risk** - Memo transactions and amendments can inflate totals
6. **Large file sizes** - Transaction files are 1-8 GB each

### What's the goal?

Transform 13 GB of raw data into 581 MB of clean, analysis-ready CSVs:
- Standard CSV format with snake_case headers
- Combined/summarized files with year identification
- Deduplicated transaction data
- Flat folder structure with documentation

---

## Understanding the Data

### Data Categories

| Category | What it contains | Size | Years |
|----------|------------------|------|-------|
| all_candidates | Financial summaries for every candidate | Small | 1980-2026 |
| candidate_master | Basic candidate registration info | Small | 1980-2026 |
| candidate_committee_linkages | Which committees support which candidates | Small | 2000-2026 |
| committee_master | Basic committee registration info | Medium | 1980-2026 |
| house_senate_current_campaigns | House/Senate campaign financials | Small | 1996-2026 |
| pac_summary | PAC and party committee financials | Small | 1996-2026 |
| committee_transactions | Every committee-to-committee transaction | **Large (8 GB)** | 1980-2026 |
| contributions_from_committees | Committee contributions to candidates | **Large (1.3 GB)** | 1980-2026 |
| operating_expenditures | Itemized committee spending | **Large (3.4 GB)** | 2004-2026 |

### Why some data needs summarization

The three large datasets contain **itemized transactions** - one row per contribution or expenditure. This creates problems:

1. **File size** - Too large to load into memory or share easily
2. **Double-counting** - The same transaction may appear multiple times:
   - `memo_cd = 'X'` flags transactions that are breakdowns of larger amounts
   - `amndt_ind = 'A'` flags amended filings (corrections to previous reports)
   - Same `sub_id` can appear in multiple files

**Solution:** Aggregate transactions by grouping (committee, recipient, year, type) and summing amounts, after excluding duplicates.

### Why small data just needs combining

The six small datasets are **summary records** - one row per candidate/committee per cycle. These don't have double-counting issues, they just need to be merged across years with a `year` column added.

---

## The Optimized Process

### Step 1: Download & Extract

**What happens:**
- Downloads ~220 zip files from FEC website
- Extracts contents with proper year-prefix naming
- Removes nested directories created during extraction
- Deletes zip files to save space

**Why year-prefix naming:**
FEC names files like `weball00.txt` (last 2 digits of year). This causes collisions when extracting multiple zips. Renaming to `2000_weball.txt` makes the year explicit and prevents overwrites.

**What to expect:**
- Download time: ~20-30 minutes (depends on connection)
- Extracted size: ~13 GB
- File count: ~180 text files across 9 categories

**Potential issues:**
- FEC website may be slow or timeout - add retry logic
- Some zip files have nested folders - need to flatten
- Years 1980-1998 use 2-digit year format in filenames

```python
# Pseudo-code
for category in CATEGORIES:
    for year in YEARS:
        zip_url = get_fec_url(category, year)
        download(zip_url)
        extract_with_year_prefix(zip_file, year)
        flatten_nested_dirs()
        delete(zip_file)
```

### Step 2: Fetch Metadata

**What happens:**
- Downloads `header.csv` files from FEC (column names)
- Downloads data description pages (full documentation)
- For categories missing headers, parses columns from description

**Why this matters:**
The raw `.txt` files have no headers. FEC provides separate header files, but not for all categories. Without headers, the data is unusable.

**What to expect:**
- Most categories have header files available
- 3 categories (all_candidates, house_senate_current_campaigns, pac_summary) may return 404 - parse from description instead
- Description pages are HTML that needs conversion to markdown

**Potential issues:**
- FEC URLs may change - verify URLs before running
- Some descriptions have malformed markdown tables
- Header column counts should match data column counts (verify!)

```python
# Pseudo-code
for category in CATEGORIES:
    try:
        download(f"{FEC_BASE}/header_{category}.csv")
    except 404:
        headers = parse_headers_from_description(category)
        write_header_csv(headers)

    download_description_page(category)
```

### Step 3: Process & Transform

This is the main step where all data transformation happens.

**What happens:**

For **small datasets** (combine strategy):
1. Read each year's pipe-delimited file
2. Add header row (snake_case)
3. Prepend `year` column with election cycle
4. Concatenate all years into single output file
5. Delete source files

For **large datasets** (summarize strategy):
1. Read each year's pipe-delimited file
2. Skip rows where `memo_cd = 'X'` (memo transactions)
3. Skip rows where `amndt_ind != 'N'` (amendments)
4. Track `sub_id` values to skip duplicates
5. Group by key fields (committee, recipient, year, type)
6. Sum transaction amounts and count transactions
7. Write aggregated output
8. Delete source files

**Why exclude memo transactions:**
When a committee receives a lump sum (e.g., from joint fundraising), they must itemize how it breaks down by original contributor. These itemizations are marked `memo_cd = 'X'` and should NOT be added to totals - the lump sum already counts them.

**Why exclude amendments:**
When a committee files an amended report, both the original and amendment may exist in the data. Keeping only `amndt_ind = 'N'` (new filings) avoids counting the same transaction twice.

**Why dedupe by sub_id:**
Each transaction has a unique `sub_id`. In rare cases, the same transaction appears in multiple files. Tracking seen IDs prevents double-counting.

**What to expect:**

| Dataset | Input Size | Output Size | Reduction |
|---------|------------|-------------|-----------|
| all_candidates | 8 MB | 8.5 MB | +6% (year column added) |
| candidate_master | 12 MB | 13 MB | +8% |
| candidate_committee_linkages | 3.3 MB | 3.6 MB | +9% |
| committee_master | 37 MB | 38 MB | +3% |
| house_senate_current_campaigns | 4.2 MB | 4.3 MB | +2% |
| pac_summary | 17 MB | 17 MB | 0% |
| committee_transactions | 8.0 GB | 271 MB | **97% reduction** |
| contributions_from_committees | 1.3 GB | 202 MB | **85% reduction** |
| operating_expenditures | 3.4 GB | 15 MB | **99.6% reduction** |

**Processing time:** ~90 minutes (mostly reading large files)

**Potential issues:**
- Memory usage for large files - process row by row, don't load entire file
- Malformed rows (wrong column count) - skip and log
- Encoding issues - use `errors='replace'` when reading

```python
DATASET_CONFIG = {
    "all_candidates": {
        "type": "combine",
        "output": "all_candidate_summaries_1980-2026.csv",
        "add_year_column": True,
    },
    "committee_transactions": {
        "type": "summarize",
        "output": "committee_transaction_summaries_1980-2026.csv",
        "group_by": ["election_cycle", "transaction_year", "source_cmte_id",
                     "dest_cmte_id", "transaction_tp"],
        "sum_field": "transaction_amt",
        "exclude_memo": True,
        "exclude_amendments": True,
        "dedupe_by_sub_id": True,
    },
    # ... etc
}

for dataset, config in DATASET_CONFIG.items():
    if config["type"] == "combine":
        combine_years(dataset, config)
    elif config["type"] == "summarize":
        summarize_transactions(dataset, config)
```

### Step 4: Generate Documentation

**What happens:**
- Creates a markdown file for each output CSV
- Includes source URL, column definitions, row counts
- Documents any exclusions or transformations applied

**Why this matters:**
Without documentation, users won't know what columns mean or why row counts differ from raw FEC data.

**What to expect:**
- 9 markdown files in `data/metadata/`
- Each file maps to one or more output CSVs
- Operating expenditures share one doc (covers both by-category and by-state)

### Step 5: Verify

**What happens:**
- Counts rows in each output file
- Validates no null values in required fields
- Spot-checks random samples
- Compares totals against expected ranges

**Why this matters:**
Processing errors can silently corrupt data. Verification catches issues before the data is used.

**What to expect:**
- All files should have headers matching expected column count
- Transaction amounts should be reasonable (no $999 trillion values)
- Year/cycle values should be within expected ranges

---

## Comparison: Original vs Optimized

### Original Process (23 steps)

The original process evolved iteratively as we discovered issues:

| Phase | Steps | What happened |
|-------|-------|---------------|
| Download & Extract | 1-5 | Downloaded, extracted, discovered naming collision, re-extracted with renaming |
| Metadata | 6-8 | Created folders, downloaded headers, discovered some 404s, parsed from descriptions |
| CSV Conversion | 9-13 | Converted to CSV, added headers, audited, deleted originals |
| Combine Small | 14-15 | Combined small datasets, deleted year files |
| Summarize Large | 16-21 | Summarized each large dataset separately, discovered deduplication needs mid-process |
| Finalize | 22-23 | Renamed headers to snake_case, flattened folder structure |

**Problems:**
- Multiple passes over same data (convert → combine → rename headers)
- Created intermediate files that were later deleted
- Discovered requirements mid-process (deduplication rules, folder structure)
- Not easily reproducible (many manual decisions)

### Optimized Process (5 steps)

| Step | What happens | Time |
|------|--------------|------|
| 1. Download & Extract | Get all data with proper naming | ~30 min |
| 2. Fetch Metadata | Get headers and descriptions | ~10 min |
| 3. Process & Transform | Single-pass conversion/combining/summarization | ~90 min |
| 4. Generate Documentation | Create metadata files | ~5 min |
| 5. Verify | Audit output integrity | ~5 min |

**Improvements:**
- Single pass per file (no re-reading)
- No intermediate files (source → output directly)
- Config-driven (all rules defined upfront)
- Fully scriptable (reproducible)

### Summary

| Aspect | Original | Optimized |
|--------|----------|-----------|
| Steps | 23 | 5 |
| Scripts | 8+ ad-hoc | 5 planned |
| Data passes | Multiple | Single |
| Intermediate files | Many | None |
| Total time | ~3.5 hours | ~2 hours |
| Reproducible | No | Yes |

---

## Final Output

### File Structure

```
data/
├── all_candidate_summaries_1980-2026.csv           8.5 MB   (69K rows)
├── candidate_committee_links_2000-2026.csv         3.6 MB   (81K rows)
├── candidate_registrations_1980-2026.csv           13 MB    (129K rows)
├── committee_registrations_1980-2026.csv           38 MB    (296K rows)
├── committee_to_candidate_summaries_1980-2026.csv  202 MB   (2.8M rows)
├── committee_transaction_summaries_1980-2026.csv   271 MB   (3.8M rows)
├── expenditures_by_category_2004-2026.csv          6.1 MB   (129K rows)
├── expenditures_by_state_2004-2026.csv             9.3 MB   (319K rows)
├── house_senate_campaign_summaries_1996-2026.csv   4.3 MB   (32K rows)
├── pac_party_summaries_1996-2026.csv               17 MB    (140K rows)
└── metadata/
    └── *.md (9 documentation files)
```

**Total: 581 MB** (down from 13 GB raw)

### What you can do with this data

1. **Track candidate fundraising over time** - Use all_candidate_summaries to see how much each candidate raised per cycle

2. **Analyze PAC spending patterns** - Use committee_transaction_summaries to see which PACs fund which other PACs

3. **See who funds candidates** - Use committee_to_candidate_summaries to see which committees support which candidates

4. **Geographic spending analysis** - Use expenditures_by_state to see where campaign money flows

5. **Spending category breakdown** - Use expenditures_by_category to see what campaigns spend money on

---

## Quick Reference

### Deduplication Rules (for transaction data)

```python
# EXCLUDE rows where:
memo_cd == 'X'           # Memo = breakdown of larger transaction (already counted)
amndt_ind != 'N'         # Amendment = correction to previous filing (would double-count)
sub_id in seen_ids       # Duplicate = same transaction in multiple files
```

### Processing Strategy by Dataset

| Dataset | Strategy | Why |
|---------|----------|-----|
| all_candidates | Combine | Summary data, no duplicates |
| candidate_master | Combine | Registration data, no duplicates |
| candidate_committee_linkages | Combine | Link data, no duplicates |
| committee_master | Combine | Registration data, no duplicates |
| house_senate_current_campaigns | Combine | Summary data, no duplicates |
| pac_summary | Combine | Summary data, no duplicates |
| committee_transactions | Summarize | Itemized transactions, needs deduplication |
| contributions_from_committees | Summarize | Itemized transactions, needs deduplication |
| operating_expenditures | Summarize (x2) | Itemized transactions, useful grouped by category AND state |

### Column Naming Convention

All headers converted to `snake_case`:
- `CAND_ID` → `cand_id`
- `TRANSACTION_AMT` → `transaction_amt`
- `TTL_RECEIPTS` → `ttl_receipts`

### Added Columns

| Column | Added to | Purpose |
|--------|----------|---------|
| `year` | Combined files | Identifies election cycle (from filename) |
| `election_cycle` | Summarized files | 2-year FEC reporting period |
| `transaction_year` | Summarized files | Actual year from transaction date |
| `total_amount` | Summarized files | Sum of transaction amounts |
| `transaction_count` | Summarized files | Number of transactions aggregated |
