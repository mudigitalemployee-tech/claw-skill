#!/usr/bin/env python3
"""
SEC 10-K Report Fetcher & Parser
Given a company name, fetches the latest 10-K filing from SEC EDGAR,
parses it into structured JSON, and saves to ~/Music/10k_reports/<company>/
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import warnings
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

HEADERS = {
    "User-Agent": "OpenClaw SEC Research Agent contact@openclaw.ai",
    "Accept-Encoding": "gzip, deflate",
}

BASE_URL = "https://efts.sec.gov/LATEST"
EDGAR_ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
EDGAR_FILINGS = "https://efts.sec.gov/LATEST/search-index?q=%22{cik}%22&dateRange=custom&startdt={start}&enddt={end}&forms=10-K"

# Standard 10-K sections
SECTION_PATTERNS = {
    "item_1_business": r"(?:item\s*1[\.\s:]+business)",
    "item_1a_risk_factors": r"(?:item\s*1a[\.\s:]+risk\s*factors)",
    "item_1b_unresolved_staff_comments": r"(?:item\s*1b[\.\s:]+unresolved\s*staff\s*comments)",
    "item_1c_cybersecurity": r"(?:item\s*1c[\.\s:]+cybersecurity)",
    "item_2_properties": r"(?:item\s*2[\.\s:]+properties)",
    "item_3_legal_proceedings": r"(?:item\s*3[\.\s:]+legal\s*proceedings)",
    "item_4_mine_safety": r"(?:item\s*4[\.\s:]+mine\s*safety)",
    "item_5_market": r"(?:item\s*5[\.\s:]+market\s*for)",
    "item_6_selected_financial": r"(?:item\s*6[\.\s:]+(?:selected\s*financial|\[reserved\]))",
    "item_7_md_and_a": r"(?:item\s*7[\.\s:]+management)",
    "item_7a_market_risk": r"(?:item\s*7a[\.\s:]+quantitative)",
    "item_8_financial_statements": r"(?:item\s*8[\.\s:]+financial\s*statements)",
    "item_9_disagreements": r"(?:item\s*9[\.\s:]+changes\s*in\s*and\s*disagreements)",
    "item_9a_controls": r"(?:item\s*9a[\.\s:]+controls)",
    "item_9b_other": r"(?:item\s*9b[\.\s:]+other\s*information)",
    "item_10_directors": r"(?:item\s*10[\.\s:]+directors)",
    "item_11_executive_compensation": r"(?:item\s*11[\.\s:]+executive\s*compensation)",
    "item_12_security_ownership": r"(?:item\s*12[\.\s:]+security\s*ownership)",
    "item_13_relationships": r"(?:item\s*13[\.\s:]+certain\s*relationships)",
    "item_14_accountant_fees": r"(?:item\s*14[\.\s:]+principal\s*account)",
    "item_15_exhibits": r"(?:item\s*15[\.\s:]+exhibit)",
}


def search_company(name: str) -> dict:
    """Search EDGAR for a company by name, return CIK and company info."""
    url = f"https://efts.sec.gov/LATEST/search-index?q=%22{name}%22&forms=10-K&dateRange=custom"
    
    # Use the full-text search API
    url = f"https://efts.sec.gov/LATEST/search-index?q=%22{name}%22&forms=10-K"
    
    # Better approach: use company search endpoint
    search_url = "https://efts.sec.gov/LATEST/search-index"
    
    # Actually, let's use the proper EDGAR full-text search
    search_url = f"https://efts.sec.gov/LATEST/search-index?q=%22{name}%22&forms=10-K"
    
    # Use the company tickers JSON for lookup
    tickers_url = "https://www.sec.gov/files/company_tickers.json"
    resp = requests.get(tickers_url, headers=HEADERS)
    resp.raise_for_status()
    tickers = resp.json()
    
    name_lower = name.lower().strip()
    matches = []
    for entry in tickers.values():
        title = entry.get("title", "").lower()
        ticker = entry.get("ticker", "").lower()
        if name_lower in title or name_lower == ticker:
            matches.append(entry)
    
    if not matches:
        # Try partial match
        for entry in tickers.values():
            title = entry.get("title", "").lower()
            if any(word in title for word in name_lower.split()):
                matches.append(entry)
    
    if not matches:
        print(f"ERROR: No company found matching '{name}'")
        print("Try using the ticker symbol (e.g., AAPL, MSFT) or exact company name.")
        sys.exit(1)
    
    # Sort by relevance — exact ticker match first, then exact name match
    def score(entry):
        t = entry.get("ticker", "").lower()
        n = entry.get("title", "").lower()
        if t == name_lower:
            return 0
        if n == name_lower:
            return 1
        if name_lower in n:
            return 2
        return 3
    
    matches.sort(key=score)
    best = matches[0]
    
    cik = str(best["cik_str"]).zfill(10)
    print(f"Found: {best['title']} (Ticker: {best['ticker']}, CIK: {cik})")
    
    if len(matches) > 1:
        print(f"  ({len(matches)} matches total — using best match)")
    
    return {"cik": cik, "ticker": best["ticker"], "title": best["title"]}


def get_latest_10k(cik: str) -> dict:
    """Get the latest 10-K filing metadata from EDGAR."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    
    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    dates = recent.get("filingDate", [])
    primary_docs = recent.get("primaryDocument", [])
    
    for i, form in enumerate(forms):
        if form == "10-K":
            accession = accessions[i].replace("-", "")
            return {
                "accession": accessions[i],
                "accession_clean": accession,
                "filing_date": dates[i],
                "primary_document": primary_docs[i],
                "cik": cik,
                "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary_docs[i]}",
                "index_url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/",
                "company_name": data.get("name", ""),
                "sic": data.get("sic", ""),
                "sic_description": data.get("sicDescription", ""),
                "state": data.get("addresses", {}).get("business", {}).get("stateOrCountry", ""),
                "fiscal_year_end": data.get("fiscalYearEnd", ""),
            }
    
    print("ERROR: No 10-K filing found for this company.")
    sys.exit(1)


def download_filing(url: str) -> str:
    """Download the 10-K filing HTML."""
    print(f"Downloading filing from: {url}")
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.text


def clean_text(text: str) -> str:
    """Clean extracted text — normalize whitespace, strip artifacts."""
    text = re.sub(r'\xa0', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text


def extract_tables(soup_section) -> list:
    """Extract tables from a BeautifulSoup section as list of dicts."""
    tables = []
    for table in soup_section.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [clean_text(td.get_text()) for td in tr.find_all(["td", "th"])]
            if any(c.strip() for c in cells):
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables


def parse_10k_sections(html: str) -> dict:
    """Parse the 10-K HTML into sections.
    
    Strategy: find ALL occurrences of each section header, then keep only
    the LAST occurrence (which is the actual content, not the TOC link).
    Only keep sections with meaningful content (>100 chars).
    """
    from bs4 import XMLParsedAsHTMLWarning
    import warnings
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
    
    soup = BeautifulSoup(html, "lxml")
    full_text = soup.get_text()
    
    # Find ALL occurrences of each section header — keep the LAST one
    # (TOC entries come first; actual content sections come later)
    section_positions = []
    for section_key, pattern in SECTION_PATTERNS.items():
        all_matches = list(re.finditer(pattern, full_text, re.IGNORECASE))
        if all_matches:
            # Use the last match (actual content, not TOC)
            match = all_matches[-1]
            section_positions.append({
                "key": section_key,
                "start": match.start(),
                "match_text": match.group()
            })
    
    # Sort by position in document
    section_positions.sort(key=lambda x: x["start"])
    
    # Extract text between section boundaries
    sections = {}
    for i, sp in enumerate(section_positions):
        start = sp["start"]
        end = section_positions[i + 1]["start"] if i + 1 < len(section_positions) else len(full_text)
        
        section_text = full_text[start:end]
        section_text = clean_text(section_text)
        
        # Skip trivially small sections (likely residual TOC artifacts)
        if len(section_text) < 100:
            continue
        
        # Truncate extremely long sections to first 100k chars (with note)
        truncated = False
        if len(section_text) > 100000:
            section_text = section_text[:100000]
            truncated = True
        
        sections[sp["key"]] = {
            "text": section_text,
            "char_count": len(section_text),
            "truncated": truncated,
        }
    
    return sections


def extract_filing_index(cik: str, accession_clean: str) -> list:
    """Get all documents in the filing."""
    url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/"
    # Use the index.json
    index_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    
    # Actually get the filing documents from the index page
    idx_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-K&dateb=&owner=include&count=1&search_text=&action=getcompany"
    
    # Simpler: just return the primary doc info
    return []


def build_output(company_info: dict, filing_info: dict, sections: dict, html: str) -> dict:
    """Build the final JSON output."""
    soup = BeautifulSoup(html, "lxml")
    
    # Extract all tables globally
    all_tables = extract_tables(soup)
    
    output = {
        "metadata": {
            "company_name": filing_info.get("company_name", company_info["title"]),
            "ticker": company_info["ticker"],
            "cik": company_info["cik"],
            "sic": filing_info.get("sic", ""),
            "sic_description": filing_info.get("sic_description", ""),
            "state": filing_info.get("state", ""),
            "fiscal_year_end": filing_info.get("fiscal_year_end", ""),
            "filing_date": filing_info["filing_date"],
            "accession_number": filing_info["accession"],
            "filing_url": filing_info["url"],
            "source": "SEC EDGAR",
            "parsed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        "sections": sections,
        "tables_count": len(all_tables),
        "tables": all_tables[:50],  # Cap at 50 tables to keep JSON manageable
        "full_text_chars": len(soup.get_text()),
    }
    
    return output


def main():
    parser = argparse.ArgumentParser(description="Fetch & parse SEC 10-K reports into JSON")
    parser.add_argument("company", help="Company name or ticker symbol (e.g., 'Apple' or 'AAPL')")
    parser.add_argument("--output-dir", default=os.path.expanduser("~/Music/10k_reports"),
                        help="Output directory (default: ~/Music/10k_reports)")
    parser.add_argument("--raw", action="store_true", help="Also save raw HTML filing")
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"  SEC 10-K Report Pipeline")
    print(f"  Company: {args.company}")
    print(f"{'='*60}\n")
    
    # Step 1: Find the company
    print("[1/5] Searching for company...")
    company_info = search_company(args.company)
    time.sleep(0.2)  # Rate limit courtesy
    
    # Step 2: Get latest 10-K filing info
    print(f"\n[2/5] Finding latest 10-K filing...")
    filing_info = get_latest_10k(company_info["cik"])
    print(f"  Filing date: {filing_info['filing_date']}")
    print(f"  Accession: {filing_info['accession']}")
    time.sleep(0.2)
    
    # Step 3: Download the filing
    print(f"\n[3/5] Downloading 10-K filing...")
    html = download_filing(filing_info["url"])
    print(f"  Downloaded {len(html):,} characters")
    time.sleep(0.2)
    
    # Step 4: Parse sections
    print(f"\n[4/5] Parsing 10-K sections...")
    sections = parse_10k_sections(html)
    print(f"  Found {len(sections)} sections:")
    for key in sections:
        chars = sections[key]["char_count"]
        trunc = " (truncated)" if sections[key]["truncated"] else ""
        print(f"    - {key}: {chars:,} chars{trunc}")
    
    # Step 5: Build output and save
    print(f"\n[5/5] Building JSON output...")
    output = build_output(company_info, filing_info, sections, html)
    
    # Create output directory
    company_slug = re.sub(r'[^a-zA-Z0-9]+', '_', company_info["title"]).strip('_').lower()
    out_dir = Path(args.output_dir) / company_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    json_path = out_dir / f"10k_{filing_info['filing_date']}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"  Saved JSON: {json_path}")
    print(f"  JSON size: {json_path.stat().st_size / 1024:.1f} KB")
    
    # Save metadata summary
    summary_path = out_dir / f"summary_{filing_info['filing_date']}.json"
    summary = {
        "metadata": output["metadata"],
        "sections_found": list(sections.keys()),
        "sections_char_counts": {k: v["char_count"] for k, v in sections.items()},
        "total_tables": output["tables_count"],
        "full_text_chars": output["full_text_chars"],
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"  Saved summary: {summary_path}")
    
    # Optionally save raw HTML
    if args.raw:
        raw_path = out_dir / f"10k_{filing_info['filing_date']}_raw.html"
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  Saved raw HTML: {raw_path}")
    
    print(f"\n{'='*60}")
    print(f"  ✅ Done! Files saved to: {out_dir}")
    print(f"{'='*60}\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
