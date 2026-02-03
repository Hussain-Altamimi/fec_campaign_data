Source: https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/

# Individual Contributions (1980-2026)

**Directory:** `individual_contributions/`

Itemized contributions from individuals to federal political committees. Files are split by election cycle (e.g., `1980_individual_contributions.csv`).

## Columns

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

## Common Transaction Types

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

## Itemization Thresholds

Contributions are only itemized (included in this file) above certain thresholds:

| Period | Threshold | Calculation |
|--------|-----------|-------------|
| 2015–present | >$200 | Election cycle-to-date (candidates) or calendar year-to-date (PACs/parties) |
| 1989–2014 | ≥$200 | Per reporting period |
| 1975–1988 | ≥$500 | Per reporting period |

Smaller contributions are reported only as aggregate unitemized totals in committee summary filings.

## Data Quality Notes

- **Entity type (`entity_tp`)**: Only populated for electronic filings after April 2002; blank in older records
- **Employer/occupation**: More consistently reported in recent years; often blank or generic in 1980s data
- **ZIP codes**: May be incomplete (sometimes just "0") in early years
- **Memo transactions**: Records with `memo_cd = 'X'` are subtransactions that should not be summed with regular transactions to avoid double-counting

## File Statistics

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
