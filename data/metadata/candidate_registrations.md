Source: https://www.fec.gov/campaign-finance-data/candidate-master-file-description/

# Candidate Registrations (1980-2026)

**File:** `candidate_registrations_1980-2026.csv`

Basic information for each candidate registered with the FEC, including candidates who filed a Statement of Candidacy, have active campaign committees, or are referenced by draft/nonconnected committees.

## Columns

| Column | Description |
|--------|-------------|
| `year` | Election cycle (added during consolidation) |
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
