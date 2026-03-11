---
name: sec-10k-pipeline
description: Fetch and parse SEC 10-K annual reports into structured JSON. Use when a user provides a company name or ticker and wants to download, parse, or analyze a 10-K filing. Triggers on "10-K", "10K report", "SEC filing", "annual report", "fetch 10-K for [company]". Outputs structured JSON with metadata, all 21 standard sections, and extracted tables to ~/Music/10k_reports/[company]/.
---

# SEC 10-K Report Pipeline

Fetch the latest 10-K filing from SEC EDGAR for any public US company, parse it into structured JSON with all standard sections and tables, and save locally.

## Usage

```bash
python3 scripts/fetch_10k.py "<company name or ticker>"
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--output-dir` | `~/Music/10k_reports` | Override output directory |
| `--raw` | off | Also save the raw HTML filing |

### Examples

```bash
python3 scripts/fetch_10k.py "Apple"
python3 scripts/fetch_10k.py "MSFT" --raw
python3 scripts/fetch_10k.py "Tesla" --output-dir /tmp/reports
```

## Output Structure

```
~/Music/10k_reports/<company_slug>/
├── 10k_<filing_date>.json      # Full parsed report
└── summary_<filing_date>.json  # Metadata + section index
```

### JSON Schema

- `metadata` — company name, ticker, CIK, SIC, state, fiscal year end, filing date, accession number, filing URL
- `sections` — dict keyed by standard 10-K item names (e.g., `item_1_business`, `item_7_md_and_a`), each with `text`, `char_count`, `truncated`
- `tables` — first 50 tables extracted from the filing (list of row arrays)
- `tables_count` — total tables found
- `full_text_chars` — total character count

### Standard Sections Parsed

Items 1–15 including sub-items (1A Risk Factors, 1B, 1C Cybersecurity, 7A Market Risk, 9A Controls, 9B Other).

## How It Works

1. Search SEC company tickers JSON for CIK by name/ticker
2. Query EDGAR submissions API for latest 10-K filing
3. Download the primary filing document (HTML)
4. Parse section boundaries using regex on full text (last occurrence = actual content, not TOC)
5. Extract tables via BeautifulSoup
6. Save structured JSON + summary

## Dependencies

- Python 3.7+
- `requests`, `beautifulsoup4`, `lxml`

## Notes

- SEC EDGAR rate limits: script includes 200ms delays between API calls
- Sections under 100 chars are skipped (TOC artifacts)
- Sections over 100k chars are truncated with `truncated: true` flag
- Company search is fuzzy — exact ticker match preferred, then name match
