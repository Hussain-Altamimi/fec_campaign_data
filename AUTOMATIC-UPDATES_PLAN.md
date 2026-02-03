# FEC Campaign Finance Data Integration Background

This background document provides everything needed to integrate FEC (Federal Election Commission) campaign finance data into a Next.js React app with SQLite database. The app already has Congress members identified by Bioguide ID.

---

## Overview

### Data Source

Processed FEC bulk data covering 1980-2026 (581 MB total). Files are in `data/` with documentation in `data/metadata/`.

### Integration Goals

1. **Member pages**: Show full campaign finance details (totals, contribution sources, top committees, expenditure breakdown)
2. **Committee/PAC pages**: Dedicated pages for PACs and committees with their activity
3. **Search/explore**: Search contributions by committee, candidate, amount, etc.

### Critical Integration Challenge

**The FEC uses `cand_id` (9-character code), NOT Bioguide ID.** You must create a mapping table.

---

## Part 1: Database Schema

### Core Tables to Create

```sql
-- Maps Bioguide IDs to FEC candidate IDs
CREATE TABLE fec_candidate_mapping (
  bioguide_id TEXT PRIMARY KEY,
  cand_id TEXT NOT NULL,
  FOREIGN KEY (bioguide_id) REFERENCES members(bioguide_id)
);
CREATE INDEX idx_cand_id ON fec_candidate_mapping(cand_id);

-- Candidate financial summaries per election cycle
CREATE TABLE fec_candidate_summaries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  cand_id TEXT NOT NULL,
  year INTEGER NOT NULL,                    -- Election cycle (even years)
  cand_name TEXT,
  cand_ici TEXT,                            -- I=Incumbent, C=Challenger, O=Open
  party_code TEXT,
  ttl_receipts REAL,                        -- Total money raised
  ttl_disb REAL,                            -- Total money spent
  coh_cop REAL,                             -- Cash on hand (end of period)
  ttl_indiv_contrib REAL,                   -- From individuals
  other_pol_cmte_contrib REAL,              -- From PACs
  pol_pty_contrib REAL,                     -- From party committees
  cand_contrib REAL,                        -- Self-funding
  cand_loans REAL,                          -- Self-loans
  debts_owed_by REAL,
  trans_from_auth REAL,                     -- Transfers between candidate's committees
  trans_to_auth REAL,
  cvg_end_dt TEXT,
  UNIQUE(cand_id, year)
);
CREATE INDEX idx_candidate_summaries_cand_id ON fec_candidate_summaries(cand_id);
CREATE INDEX idx_candidate_summaries_year ON fec_candidate_summaries(year);

-- Committee registrations
CREATE TABLE fec_committees (
  cmte_id TEXT NOT NULL,
  year INTEGER NOT NULL,
  cmte_nm TEXT,
  cmte_tp TEXT,                             -- Committee type code
  cmte_dsgn TEXT,                           -- A=Authorized, P=Principal, etc.
  cmte_pty_affiliation TEXT,
  connected_org_nm TEXT,
  cand_id TEXT,                             -- For candidate committees
  PRIMARY KEY(cmte_id, year)
);
CREATE INDEX idx_committees_cand_id ON fec_committees(cand_id);
CREATE INDEX idx_committees_type ON fec_committees(cmte_tp);

-- PAC/Party committee financial summaries
CREATE TABLE fec_pac_summaries (
  cmte_id TEXT NOT NULL,
  year INTEGER NOT NULL,
  cmte_nm TEXT,
  cmte_tp TEXT,
  ttl_receipts REAL,
  ttl_disb REAL,
  coh_cop REAL,
  indv_contrib REAL,
  other_pol_cmte_contrib REAL,
  contrib_to_other_cmte REAL,
  ind_exp REAL,                             -- Independent expenditures
  PRIMARY KEY(cmte_id, year)
);

-- Committee contributions TO candidates (aggregated)
CREATE TABLE fec_committee_to_candidate (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  election_cycle INTEGER NOT NULL,
  transaction_year INTEGER NOT NULL,
  cmte_id TEXT NOT NULL,
  cmte_name TEXT,
  cand_id TEXT NOT NULL,
  transaction_tp TEXT,                      -- 24K=direct, 24E=independent exp, etc.
  total_amount REAL,
  transaction_count INTEGER
);
CREATE INDEX idx_ctc_cand_id ON fec_committee_to_candidate(cand_id);
CREATE INDEX idx_ctc_cmte_id ON fec_committee_to_candidate(cmte_id);
CREATE INDEX idx_ctc_cycle ON fec_committee_to_candidate(election_cycle);

-- Committee-to-committee transactions (aggregated)
CREATE TABLE fec_committee_transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  election_cycle INTEGER NOT NULL,
  transaction_year INTEGER NOT NULL,
  source_cmte_id TEXT NOT NULL,
  dest_cmte_id TEXT NOT NULL,
  dest_name TEXT,
  transaction_tp TEXT,
  total_amount REAL,
  transaction_count INTEGER
);
CREATE INDEX idx_ct_source ON fec_committee_transactions(source_cmte_id);
CREATE INDEX idx_ct_dest ON fec_committee_transactions(dest_cmte_id);

-- Expenditures by category
CREATE TABLE fec_expenditures_by_category (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  election_cycle INTEGER NOT NULL,
  transaction_year INTEGER NOT NULL,
  cmte_id TEXT NOT NULL,
  category TEXT,                            -- 001-012, 101-107
  category_desc TEXT,
  total_amount REAL,
  transaction_count INTEGER
);
CREATE INDEX idx_exp_cat_cmte ON fec_expenditures_by_category(cmte_id);

-- Expenditures by state
CREATE TABLE fec_expenditures_by_state (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  election_cycle INTEGER NOT NULL,
  transaction_year INTEGER NOT NULL,
  cmte_id TEXT NOT NULL,
  state TEXT,
  total_amount REAL,
  transaction_count INTEGER
);
CREATE INDEX idx_exp_state_cmte ON fec_expenditures_by_state(cmte_id);
```

---

## Part 2: Data Files Reference

### File → Table Mapping

| CSV File                                         | Target Table                 | Rows | Notes          |
| ------------------------------------------------ | ---------------------------- | ---- | -------------- |
| `all_candidate_summaries_1980-2026.csv`          | fec_candidate_summaries      | 69K  | All candidates |
| `committee_registrations_1980-2026.csv`          | fec_committees               | 296K | All committees |
| `pac_party_summaries_1996-2026.csv`              | fec_pac_summaries            | 140K | PACs only      |
| `committee_to_candidate_summaries_1980-2026.csv` | fec_committee_to_candidate   | 2.8M | **Large file** |
| `committee_transaction_summaries_1980-2026.csv`  | fec_committee_transactions   | 3.8M | **Large file** |
| `expenditures_by_category_2004-2026.csv`         | fec_expenditures_by_category | 129K |                |
| `expenditures_by_state_2004-2026.csv`            | fec_expenditures_by_state    | 319K |                |

### Files NOT Needed for Initial Import

- `candidate_registrations_1980-2026.csv` - Redundant with candidate_summaries
- `candidate_committee_links_2000-2026.csv` - Can derive from committee_registrations
- `house_senate_campaign_summaries_1996-2026.csv` - Subset of all_candidate_summaries

---

## Part 3: Bioguide to FEC ID Mapping

**This is the most critical step.** FEC uses `cand_id`, your app uses `bioguide_id`.

### FEC Candidate ID Format

- 9 characters: `H|S|P` + 2-digit state + 5-digit sequence
- Example: `H8CA05035` = House, California, candidate #05035
- **Stays consistent across election cycles for same office**

### Mapping Strategy

**Option A: FEC API Lookup (Recommended)**

```javascript
// Use FEC API to search by name and state
const response = await fetch(
  `https://api.open.fec.gov/v1/candidates/search/?name=${encodeURIComponent(name)}&state=${state}&api_key=${FEC_API_KEY}`,
);
```

**Option B: Manual matching from candidate_registrations**
Match on: `cand_name` (fuzzy), `cand_office_st`, `cand_office` (H/S), `cand_election_yr`

**Option C: Use existing mapping service**

- OpenSecrets provides CRP ID ↔ FEC ID mappings
- ProPublica Congress API includes FEC IDs

### Mapping Table Population

```javascript
// Example: After obtaining mappings
await db.run(
  `
  INSERT INTO fec_candidate_mapping (bioguide_id, cand_id)
  VALUES (?, ?)
`,
  [member.bioguide_id, fecCandidateId],
);
```

---

## Part 4: Data Import Scripts

### Import Order (Dependencies)

1. `fec_committees` (no dependencies)
2. `fec_candidate_summaries` (no dependencies)
3. `fec_pac_summaries` (no dependencies)
4. `fec_candidate_mapping` (requires existing members table + manual/API work)
5. `fec_committee_to_candidate` (depends on #1, #2)
6. `fec_committee_transactions` (depends on #1)
7. `fec_expenditures_by_category` (depends on #1)
8. `fec_expenditures_by_state` (depends on #1)

### CSV Import Pattern

```javascript
import { createReadStream } from "fs";
import csv from "csv-parser";
import Database from "better-sqlite3";

async function importCSV(filePath, tableName, columnMap) {
  const db = new Database("your-database.db");
  const insert = db.prepare(`
    INSERT INTO ${tableName} (${Object.values(columnMap).join(", ")})
    VALUES (${Object.values(columnMap)
      .map(() => "?")
      .join(", ")})
  `);

  const insertMany = db.transaction((rows) => {
    for (const row of rows)
      insert.run(...Object.keys(columnMap).map((k) => row[k]));
  });

  let batch = [];
  const BATCH_SIZE = 10000;

  return new Promise((resolve, reject) => {
    createReadStream(filePath)
      .pipe(csv())
      .on("data", (row) => {
        batch.push(row);
        if (batch.length >= BATCH_SIZE) {
          insertMany(batch);
          batch = [];
        }
      })
      .on("end", () => {
        if (batch.length > 0) insertMany(batch);
        resolve();
      })
      .on("error", reject);
  });
}
```

### Large File Handling

For `committee_to_candidate_summaries` (2.8M rows) and `committee_transaction_summaries` (3.8M rows):

- Use streaming CSV parser (don't load entire file)
- Insert in batches of 10,000 rows
- Use transactions for batch inserts
- Consider filtering to only recent cycles (e.g., 2010-2026) for initial load

---

## Part 5: Key Queries for Features

### Member Page: Financial Summary

```sql
SELECT
  cs.year,
  cs.ttl_receipts,
  cs.ttl_disb,
  cs.coh_cop,
  cs.ttl_indiv_contrib,
  cs.other_pol_cmte_contrib,
  cs.pol_pty_contrib,
  cs.cand_contrib + cs.cand_loans as self_funding
FROM fec_candidate_summaries cs
JOIN fec_candidate_mapping m ON cs.cand_id = m.cand_id
WHERE m.bioguide_id = ?
ORDER BY cs.year DESC;
```

### Member Page: Top Contributing Committees

```sql
SELECT
  ctc.cmte_name,
  SUM(ctc.total_amount) as total_contributed,
  SUM(ctc.transaction_count) as num_transactions
FROM fec_committee_to_candidate ctc
JOIN fec_candidate_mapping m ON ctc.cand_id = m.cand_id
WHERE m.bioguide_id = ?
  AND ctc.election_cycle = ?
  AND ctc.transaction_tp IN ('24K', '24E')  -- Direct + Independent
GROUP BY ctc.cmte_id, ctc.cmte_name
ORDER BY total_contributed DESC
LIMIT 20;
```

### Member Page: Expenditure Breakdown

```sql
-- Get the candidate's principal committee first
SELECT cmte_id FROM fec_committees
WHERE cand_id = (SELECT cand_id FROM fec_candidate_mapping WHERE bioguide_id = ?)
  AND cmte_dsgn = 'P'  -- Principal campaign committee
  AND year = ?;

-- Then get expenditure breakdown
SELECT
  category_desc,
  SUM(total_amount) as total_spent
FROM fec_expenditures_by_category
WHERE cmte_id = ?
  AND election_cycle = ?
GROUP BY category, category_desc
ORDER BY total_spent DESC;
```

### Committee Page: Activity Summary

```sql
-- Incoming money (as destination)
SELECT
  SUM(total_amount) as received,
  SUM(transaction_count) as num_transactions
FROM fec_committee_transactions
WHERE dest_cmte_id = ? AND election_cycle = ?;

-- Outgoing to candidates
SELECT
  c.cand_name,
  m.bioguide_id,  -- Link to member page if exists
  SUM(ctc.total_amount) as contributed
FROM fec_committee_to_candidate ctc
JOIN fec_candidate_summaries c ON ctc.cand_id = c.cand_id AND ctc.election_cycle = c.year
LEFT JOIN fec_candidate_mapping m ON c.cand_id = m.cand_id
WHERE ctc.cmte_id = ? AND ctc.election_cycle = ?
GROUP BY ctc.cand_id
ORDER BY contributed DESC;
```

### Search: Find Contributions

```sql
-- Search by committee name
SELECT DISTINCT
  cmte_id,
  cmte_nm,
  cmte_tp,
  MAX(year) as latest_year
FROM fec_committees
WHERE cmte_nm LIKE '%' || ? || '%'
GROUP BY cmte_id
ORDER BY latest_year DESC
LIMIT 50;

-- Find all contributions over $X in a cycle
SELECT
  ctc.cmte_name,
  cs.cand_name,
  ctc.total_amount
FROM fec_committee_to_candidate ctc
JOIN fec_candidate_summaries cs ON ctc.cand_id = cs.cand_id
  AND ctc.election_cycle = cs.year
WHERE ctc.election_cycle = ?
  AND ctc.total_amount >= ?
ORDER BY ctc.total_amount DESC;
```

---

## Part 6: Important Data Notes

### Preventing Double-Counting

**Already handled in the source data**, but understand why:

- Memo transactions excluded (breakdowns of larger amounts)
- Amendments excluded (corrections to previous filings)
- Duplicate transaction IDs excluded

### Calculating Accurate Totals

For candidate totals, subtract inter-committee transfers:

```javascript
const netReceipts = ttl_receipts - trans_from_auth;
const netDisbursements = ttl_disb - trans_to_auth;
```

### Committee Type Codes

| Code | Type                                             |
| ---- | ------------------------------------------------ |
| C    | Communication cost                               |
| D    | Delegate committee                               |
| E    | Electioneering communication                     |
| H    | **House campaign**                               |
| I    | Independent expenditor (person or group)         |
| N    | PAC - Nonqualified                               |
| O    | Independent expenditure-only (Super PACs)        |
| P    | **Presidential campaign**                        |
| Q    | PAC - Qualified                                  |
| S    | **Senate campaign**                              |
| U    | Single candidate independent expenditure         |
| V    | PAC with non-contribution account                |
| W    | PAC with non-contribution account - Nonqualified |
| X    | Party - Nonqualified                             |
| Y    | Party - Qualified                                |
| Z    | National party nonfederal account                |

### Committee Designation Codes

| Code | Designation                  |
| ---- | ---------------------------- |
| A    | Authorized by a candidate    |
| B    | Lobbyist/Registrant PAC      |
| D    | Leadership PAC               |
| J    | Joint fundraiser             |
| P    | Principal campaign committee |
| U    | Unauthorized                 |

### Transaction Type Codes (Key Ones)

| Code | Description                               |
| ---- | ----------------------------------------- |
| 24A  | Independent expenditure AGAINST candidate |
| 24E  | Independent expenditure FOR candidate     |
| 24K  | Direct contribution to candidate          |
| 24N  | Communication cost FOR candidate          |

---

## Part 7: React Components Structure

### Suggested Component Hierarchy

```
/pages/members/[bioguide_id]/
  └── finance/                    # Campaign finance section
      ├── page.tsx                # Overview with key stats
      ├── contributions/page.tsx  # Top contributors list
      └── expenditures/page.tsx   # Spending breakdown

/pages/committees/[cmte_id]/
  ├── page.tsx                    # Committee overview
  ├── contributions/page.tsx      # Who they gave to
  └── received/page.tsx           # Who gave to them

/pages/finance/
  ├── page.tsx                    # Search/explore landing
  └── search/page.tsx             # Full search interface
```

### API Routes

```
/api/fec/candidate/[cand_id]/summary
/api/fec/candidate/[cand_id]/contributors
/api/fec/candidate/[cand_id]/expenditures
/api/fec/committee/[cmte_id]/summary
/api/fec/committee/[cmte_id]/contributions
/api/fec/search/committees?q=
/api/fec/search/contributions?cycle=&min_amount=
```

---

## Part 8: Implementation Checklist

### Phase 1: Database Setup

- [ ] Create all FEC tables with indexes
- [ ] Import fec_committees from committee_registrations CSV
- [ ] Import fec_candidate_summaries from all_candidate_summaries CSV
- [ ] Import fec_pac_summaries from pac_party_summaries CSV

### Phase 2: ID Mapping (Critical)

- [ ] Obtain FEC API key from https://api.open.fec.gov/developers/
- [ ] Build script to map bioguide_id → cand_id for all members
- [ ] Populate fec_candidate_mapping table
- [ ] Verify mapping accuracy (spot-check 20+ members)

### Phase 3: Large Data Import

- [ ] Import committee_to_candidate_summaries (2.8M rows) - use batching
- [ ] Import committee_transaction_summaries (3.8M rows) - use batching
- [ ] Import expenditures_by_category
- [ ] Import expenditures_by_state

### Phase 4: API Development

- [ ] Create candidate summary endpoint
- [ ] Create top contributors endpoint
- [ ] Create expenditure breakdown endpoint
- [ ] Create committee detail endpoints
- [ ] Create search endpoints

### Phase 5: UI Development

- [ ] Add finance section to member pages
- [ ] Create committee detail pages
- [ ] Build search/explore interface
- [ ] Add data visualizations (charts for spending breakdown, etc.)

---

## Appendix: Column Definitions by File

### all_candidate_summaries_1980-2026.csv

| Column                 | Description                                   |
| ---------------------- | --------------------------------------------- |
| year                   | Election cycle (added during consolidation)   |
| cand_id                | Candidate identification (9-character code)   |
| cand_name              | Candidate name                                |
| cand_ici               | Incumbent/challenger status (I/C/O)           |
| pty_cd                 | Party code                                    |
| cand_pty_affiliation   | Party affiliation                             |
| ttl_receipts           | Total receipts                                |
| trans_from_auth        | Transfers from authorized committees          |
| ttl_disb               | Total disbursements                           |
| trans_to_auth          | Transfers to authorized committees            |
| coh_bop                | Cash on hand - beginning of period            |
| coh_cop                | Cash on hand - close of period                |
| cand_contrib           | Contributions from candidate                  |
| cand_loans             | Loans from candidate                          |
| other_loans            | Other loans                                   |
| cand_loan_repay        | Candidate loan repayments                     |
| other_loan_repay       | Other loan repayments                         |
| debts_owed_by          | Debts owed by committee                       |
| ttl_indiv_contrib      | Total individual contributions                |
| cand_office_st         | Candidate state                               |
| cand_office_district   | Candidate district                            |
| spec_election          | Special election status                       |
| prim_election          | Primary election status                       |
| run_election           | Runoff election status                        |
| gen_election           | General election status                       |
| gen_election_precent   | General election percentage                   |
| other_pol_cmte_contrib | Contributions from other political committees |
| pol_pty_contrib        | Contributions from party committees           |
| cvg_end_dt             | Coverage end date                             |
| indiv_refunds          | Refunds to individuals                        |
| cmte_refunds           | Refunds to committees                         |

### committee_registrations_1980-2026.csv

| Column               | Description                                   |
| -------------------- | --------------------------------------------- |
| year                 | Election cycle                                |
| cmte_id              | Committee identification (9-character code)   |
| cmte_nm              | Committee name                                |
| tres_nm              | Treasurer's name                              |
| cmte_st1             | Street address                                |
| cmte_st2             | Street address 2                              |
| cmte_city            | City                                          |
| cmte_st              | State                                         |
| cmte_zip             | ZIP code                                      |
| cmte_dsgn            | Designation (A/B/D/J/P/U)                     |
| cmte_tp              | Committee type code                           |
| cmte_pty_affiliation | Party affiliation code                        |
| cmte_filing_freq     | Filing frequency                              |
| org_tp               | Interest group category                       |
| connected_org_nm     | Connected organization's name                 |
| cand_id              | Candidate ID (for H, S, or P committee types) |

### committee_to_candidate_summaries_1980-2026.csv

| Column            | Description                          |
| ----------------- | ------------------------------------ |
| election_cycle    | 2-year FEC reporting period          |
| transaction_year  | Actual year from transaction date    |
| cmte_id           | Committee making the contribution    |
| cmte_name         | Name of the committee                |
| cand_id           | Candidate receiving the contribution |
| transaction_tp    | Transaction type code                |
| total_amount      | Sum of transaction amounts           |
| transaction_count | Number of transactions aggregated    |

### pac_party_summaries_1996-2026.csv

| Column                 | Description                                   |
| ---------------------- | --------------------------------------------- |
| year                   | Election cycle                                |
| cmte_id                | Committee identification                      |
| cmte_nm                | Committee name                                |
| cmte_tp                | Committee type                                |
| cmte_dsgn              | Committee designation                         |
| cmte_filing_freq       | Filing frequency                              |
| ttl_receipts           | Total receipts                                |
| trans_from_aff         | Transfers from affiliates                     |
| indv_contrib           | Contributions from individuals                |
| other_pol_cmte_contrib | Contributions from other political committees |
| ttl_disb               | Total disbursements                           |
| tranf_to_aff           | Transfers to affiliates                       |
| indv_refunds           | Refunds to individuals                        |
| coh_bop                | Cash beginning of period                      |
| coh_cop                | Cash close of period                          |
| debts_owed_by          | Debts owed by                                 |
| contrib_to_other_cmte  | Contributions to other committees             |
| ind_exp                | Independent expenditures                      |
| pty_coord_exp          | Party coordinated expenditures                |
| cvg_end_dt             | Coverage end date                             |

### expenditures_by_category_2004-2026.csv

| Column            | Description                          |
| ----------------- | ------------------------------------ |
| election_cycle    | 2-year FEC reporting period          |
| transaction_year  | Actual year from transaction date    |
| cmte_id           | Committee making the expenditure     |
| category          | Disbursement category code (001-012) |
| category_desc     | Category description                 |
| total_amount      | Sum of transaction amounts           |
| transaction_count | Number of transactions aggregated    |

**Category Codes:**

- 001: Administrative/Salary/Overhead
- 002: Travel
- 003: Solicitation and Fundraising
- 004: Advertising
- 005: Polling
- 006: Campaign Materials
- 007: Campaign Events
- 008: Transfers
- 009: Loan Repayments
- 010: Refunds
- 011: Contributions
- 012: Other

### expenditures_by_state_2004-2026.csv

| Column            | Description                       |
| ----------------- | --------------------------------- |
| election_cycle    | 2-year FEC reporting period       |
| transaction_year  | Actual year from transaction date |
| cmte_id           | Committee making the expenditure  |
| state             | State where payee is located      |
| total_amount      | Sum of transaction amounts        |
| transaction_count | Number of transactions aggregated |

### committee_transaction_summaries_1980-2026.csv

| Column            | Description                         |
| ----------------- | ----------------------------------- |
| election_cycle    | 2-year FEC reporting period         |
| transaction_year  | Actual year from transaction date   |
| source_cmte_id    | Committee making the transaction    |
| dest_cmte_id      | Committee receiving the transaction |
| dest_name         | Name of receiving committee         |
| transaction_tp    | Transaction type code               |
| total_amount      | Sum of transaction amounts          |
| transaction_count | Number of transactions aggregated   |
