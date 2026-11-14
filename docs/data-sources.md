# Data sources

## D1: NFHS-6 India and State/UT Fact Sheets (2023-24)

- Publisher: International Institute for Population Sciences (IIPS), Mumbai,
  for the Ministry of Health and Family Welfare
- Official page: <<paste the official page URL you downloaded from>>
- Accessed: <<2026-11-12, change if different>>
- Local file: `data/raw/nfhs6_factsheets.pdf` (182 pages, NOT committed to Git)
- SHA-256 of the file: <<paste the hash from Get-FileHash>>
- Used for: blood sugar (indicators 78-83) and blood pressure (indicators 84-89)

Anyone can reproduce the dataset: download the same file, check that its
SHA-256 matches, then run the commands in "How the dataset is built" below.

## What the rows measure

- Adults aged 15 years and over, women and men separately
- Columns on each sheet: Urban, Rural, Total (NFHS-6, 2023-24), then Total
  (NFHS-5, 2019-21)
- Blood sugar is **random** blood glucose, not fasting (footnote 16: "Random
  blood sugar measurement.")
- Indicators:

| No. | Topic | Group | Category |
|---|---|---|---|
| 78 | blood sugar | women | high (141-160 mg/dl) |
| 79 | blood sugar | women | very high (>160 mg/dl) |
| 80 | blood sugar | women | high or very high (>140 mg/dl) or on medicine |
| 81-83 | blood sugar | men | same three categories as 78-80 |
| 84 | blood pressure | women | mildly elevated (systolic 140-159 and/or diastolic 90-99) |
| 85 | blood pressure | women | moderately or severely elevated (systolic 160 or more and/or diastolic 100 or more) |
| 86 | blood pressure | women | elevated (140/90 or more) or on medicine |
| 87-89 | blood pressure | men | same three categories as 84-86 |

## Layout facts (checked)

- The compiled PDF has 36 sheets: India plus 27 states and 8 UTs. Manipur is
  not covered by NFHS-6.
- PDF page number = printed page number + 22 on every sheet (Maharashtra: PDF
  page 85, printed page 63).
- Each state sheet starts with the title "<State> - Key Indicators".
- PDF page 177 (printed page 155) matches the blood sugar heading text but is
  an appendix page, not a state sheet; the extractor ignores it.
- The text layer of the PDF has quirks that the extractor handles: stray spaces
  inside names ("Ha ryana"), no space after the row number on some sheets
  ("78.Blood"), and labels wrapped over several lines with the numbers on the
  middle line.

## Maharashtra (hand-checked reference sheet)

- Fieldwork: 19 June 2023 to 30 January 2024
- Sample (appendix, as read from the columns): 30,929 households, 30,408
  women, 5,025 men. The men's sample is much smaller, so men's state-level
  estimates are less precise.
- All 12 rows were compared with the printed page by eye and saved as
  `tests/data/maharashtra_answer_key.csv`. The extractor must reproduce this
  file exactly; a test enforces it.
- A copy mistake was caught on this sheet while checking: row 84 (women,
  mildly elevated) was first typed with values from other rows. The correct
  values (12.8 / 13.5 / 13.2) come from the printed page.

## Source anomalies (reviewed)

- **Chhattisgarh (PDF page 49) and Goa (PDF page 53), indicator 86:** the
  printed label repeats "Mildly elevated blood pressure" from row 84. I
  confirmed this by eye on both pages. The values are larger than rows 84 and
  85 combined, so they fit "elevated or taking medication". Treated as typos in
  the fact sheet and kept as indicator 86. These are the only entries in
  `LABEL_EXCEPTIONS` in `src/dhadkan/analytics/nfhs.py`. The consistency checks
  still apply to them, so the values must exceed their two parts.
- This is an inference from the numbers and the row position, not a statement
  by the publisher. If IIPS or a clinician says otherwise, change it.

## Values in parentheses and asterisks

The fact sheet's own note says:

- `( )` a value in parentheses is based on 25-49 unweighted cases
- `*` a percentage is not shown because it is based on fewer than 25 unweighted
  cases
- Readers should be cautious when interpreting and comparing trends because of
  smaller sample sizes
- Major indicators are highlighted in grey

How we handle them:

- Parenthesised values are **kept** and flagged in the `caution` column of the
  processed CSV (for example `rural`). Charts must mark them.
- Example: Chandigarh, indicator 78, rural, is printed as (7.2).
- An asterisk in one of the 12 rows we use makes the extractor stop with an
  error instead of guessing. None has appeared so far.
- Chandigarh: the whole rural column (all 12 rows) is printed in parentheses,
so its rural estimates rest on 25-49 cases. Charts must mark them.

## How the dataset is built

```powershell
uv run python scripts\dump_nfhs_text.py data\raw\nfhs6_factsheets.pdf   # caches the sheet text
uv run python scripts\check_cached_text.py                              # fast check, writes a report
uv run dhadkan nfhs-extract data\raw\nfhs6_factsheets.pdf               # builds the CSV (about 5 minutes)
```

Output: `data/processed/nfhs6_indicators.csv` (36 sheets x 12 rows = 432 rows),
committed to Git so CI can check it without the PDF.

Columns: survey, state, indicator_no, topic, sex, category, urban, rural,
total, nfhs5_total, source_page, caution.

## Checks every row must pass (`src/dhadkan/analytics/validation.py`)

- Every value is between 0 and 100 (including the NFHS-5 reference value)
- Total lies between the urban and rural values (tolerance 0.2 for rounding)
- Parts do not add up to more than the whole: 78 + 79 is at most 80, 81 + 82 is
  at most 83, 84 + 85 is at most 86, 87 + 88 is at most 89 (urban, rural and
  total)
- All 12 indicators present per sheet, no duplicates, labels match
- All 36 sheets present
- If any check fails, nothing is written

## Limits (must appear on charts and in the README)

- Random blood glucose, not fasting. This is not a diabetes diagnosis rate.
- Adults aged 15 and over. It does not describe the 23-56 age group alone.
- Manipur is not covered.
- Men's samples are smaller than women's; state estimates carry sampling error.
- The NFHS-5 column is stored for reference only. No trend claims are made in
  v1, because the surveys' designs differ.
- The fact sheets are the first stage of NFHS-6 release; a fuller report is
  expected.
- BMI and waist-to-hip rows are not used.

## Still to verify

- [x] Hand-checked India (PDF p.28), Uttar Pradesh (p.129), Lakshadweep (p.163):all 12 rows x 4 values match the PDF. Together with Maharashtra, 4 of 36
sheets are verified by eye; the automated checks cover all 36. PDF; record the result here
- [ ] Whether the document uses the word "provisional"
- [ ] That PDF page 177 is the India standard-error appendix
- [ ] Footnote numbering ("16") matches in the processed notes
