#!/usr/bin/env python3
"""
Tavily Search & Extract CLI
Usage:
  # Basic web search
  python tavily_search.py "latest AI news"

  # Deep search (higher quality, slower)
  python tavily_search.py "quantum computing breakthroughs 2026" --deep

  # News-specific search
  python tavily_search.py "OpenAI announcements" --topic news

  # Finance search
  python tavily_search.py "AAPL stock analysis" --topic finance

  # Control results count
  python tavily_search.py "Python best practices" --max 10

  # Recency filter (last N days)
  python tavily_search.py "tech layoffs" --days 7

  # Domain filtering
  python tavily_search.py "machine learning" --include-domains arxiv.org,nature.com
  python tavily_search.py "reviews" --exclude-domains reddit.com

  # Extract content from URLs
  python tavily_search.py --extract "https://example.com" "https://another.com"

  # JSON output (for piping / programmatic use)
  python tavily_search.py "query" --json
"""

import argparse
import json
import sys
import textwrap
from tavily_client import TavilyClient


def format_search_results(data: dict, verbose: bool = False) -> str:
    """Pretty-print search results for terminal."""
    lines = []

    # Answer summary
    answer = data.get("answer")
    if answer:
        lines.append("━" * 80)
        lines.append("📝 AI ANSWER")
        lines.append("━" * 80)
        wrapped = textwrap.fill(answer, width=78)
        lines.append(wrapped)
        lines.append("")

    # Results
    results = data.get("results", [])
    if results:
        lines.append("━" * 80)
        lines.append(f"🔍 SEARCH RESULTS ({len(results)} found)")
        lines.append("━" * 80)
        for i, r in enumerate(results, 1):
            lines.append(f"\n  [{i}] {r.get('title', 'No title')}")
            lines.append(f"      🔗 {r.get('url', '')}")
            score = r.get("score")
            if score:
                lines.append(f"      📊 Relevance: {score:.3f}")
            content = r.get("content", "")
            if content:
                snippet = textwrap.fill(
                    content[:500] + ("..." if len(content) > 500 else ""),
                    width=74,
                    initial_indent="      ",
                    subsequent_indent="      ",
                )
                lines.append(snippet)
            if verbose and r.get("raw_content"):
                lines.append(f"      [Raw content: {len(r['raw_content'])} chars]")

    # Images
    images = data.get("images", [])
    if images:
        lines.append(f"\n🖼️  IMAGES ({len(images)})")
        for img in images[:5]:
            if isinstance(img, dict):
                lines.append(f"  • {img.get('url', img)}")
            else:
                lines.append(f"  • {img}")

    # Metadata
    lines.append("")
    lines.append("─" * 80)
    resp_time = data.get("response_time")
    if resp_time:
        lines.append(f"⏱️  Response time: {resp_time:.2f}s")

    return "\n".join(lines)


def format_extract_results(data: dict) -> str:
    """Pretty-print extract results."""
    lines = []
    results = data.get("results", [])
    failed = data.get("failed_results", [])

    if results:
        lines.append("━" * 80)
        lines.append(f"📄 EXTRACTED CONTENT ({len(results)} pages)")
        lines.append("━" * 80)
        for i, r in enumerate(results, 1):
            lines.append(f"\n  [{i}] {r.get('url', 'Unknown')}")
            lines.append("  " + "─" * 76)
            raw = r.get("raw_content", "")
            # Show first 2000 chars per page
            preview = raw[:2000] + ("..." if len(raw) > 2000 else "")
            wrapped = textwrap.fill(
                preview, width=74, initial_indent="  ", subsequent_indent="  "
            )
            lines.append(wrapped)
            lines.append(f"  [{len(raw)} chars total]")

    if failed:
        lines.append(f"\n⚠️  FAILED ({len(failed)})")
        for f_item in failed:
            lines.append(f"  ✗ {f_item.get('url', 'Unknown')}: {f_item.get('error', 'Unknown error')}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Tavily Search & Extract CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Mode
    parser.add_argument("query", nargs="*", help="Search query (or URLs with --extract)")
    parser.add_argument("--extract", action="store_true", help="Extract mode: pass URLs instead of a query")

    # Search options
    parser.add_argument("--deep", action="store_true", help="Deep search (advanced depth, slower but better)")
    parser.add_argument("--topic", choices=["general", "news", "finance"], default="general")
    parser.add_argument("--max", type=int, default=5, help="Max results (default: 5)")
    parser.add_argument("--days", type=int, help="Only results from last N days")
    parser.add_argument("--include-domains", help="Comma-separated domains to include")
    parser.add_argument("--exclude-domains", help="Comma-separated domains to exclude")
    parser.add_argument("--no-answer", action="store_true", help="Skip AI answer generation")
    parser.add_argument("--images", action="store_true", help="Include image results")
    parser.add_argument("--raw", action="store_true", help="Include raw page content")

    # Output
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--timeout", type=int, default=60, help="Request timeout in seconds")

    args = parser.parse_args()

    if not args.query:
        parser.print_help()
        sys.exit(1)

    try:
        client = TavilyClient()
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.extract:
            # Extract mode — args.query contains URLs
            data = client.extract(args.query, timeout=args.timeout)
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print(format_extract_results(data))
        else:
            # Search mode
            query = " ".join(args.query)
            kwargs = {
                "search_depth": "advanced" if args.deep else "basic",
                "topic": args.topic,
                "max_results": args.max,
                "include_answer": not args.no_answer,
                "include_raw_content": args.raw,
                "include_images": args.images,
                "timeout": args.timeout,
            }
            if args.days:
                kwargs["days"] = args.days
            if args.include_domains:
                kwargs["include_domains"] = [d.strip() for d in args.include_domains.split(",")]
            if args.exclude_domains:
                kwargs["exclude_domains"] = [d.strip() for d in args.exclude_domains.split(",")]

            data = client.search(query, **kwargs)

            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print(format_search_results(data, verbose=args.verbose))

    except RuntimeError as e:
        print(f"❌ API Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
