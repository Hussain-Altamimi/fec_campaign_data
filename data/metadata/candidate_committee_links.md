Source: https://www.fec.gov/campaign-finance-data/candidate-committee-linkage-file-description/

# Candidate-Committee Links (2000-2026)

**File:** `candidate_committee_links_2000-2026.csv`

Links candidates to their authorized committees, showing the relationship between candidate IDs and committee IDs.

## Columns

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
