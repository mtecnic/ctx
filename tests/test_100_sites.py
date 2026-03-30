#!/usr/bin/env python3
"""CTX 100-site stress test.

Tests the CTX converter across 100 diverse real-world websites,
captures pass/fail/partial/error results, and generates a report.

Usage:
    cd /home/dev-ai/ctx
    venv/bin/python tests/test_100_sites.py
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
import traceback
from pathlib import Path

import httpx

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ctx.converter.pipeline import convert
from ctx.parser import parse

# ---------------------------------------------------------------------------
# Test sites: 100 URLs across 10 categories
# ---------------------------------------------------------------------------

SITES: list[tuple[str, str, str]] = [
    # --- News (10) ---
    ("https://www.cnn.com", "news", "CNN"),
    ("https://www.bbc.com/news", "news", "BBC News"),
    ("https://www.reuters.com", "news", "Reuters"),
    ("https://apnews.com", "news", "AP News"),
    ("https://www.npr.org", "news", "NPR"),
    ("https://www.aljazeera.com", "news", "Al Jazeera"),
    ("https://www.theguardian.com/us", "news", "The Guardian"),
    ("https://www.nytimes.com", "news", "NY Times"),
    ("https://www.washingtonpost.com", "news", "Washington Post"),
    ("https://abcnews.go.com", "news", "ABC News"),

    # --- Sports (10) ---
    ("https://www.espn.com", "sports", "ESPN"),
    ("https://www.mlb.com", "sports", "MLB.com"),
    ("https://www.nba.com", "sports", "NBA.com"),
    ("https://www.nfl.com", "sports", "NFL.com"),
    ("https://www.bbc.com/sport", "sports", "BBC Sport"),
    ("https://sports.yahoo.com", "sports", "Yahoo Sports"),
    ("https://bleacherreport.com", "sports", "Bleacher Report"),
    ("https://www.cbssports.com", "sports", "CBS Sports"),
    ("https://www.si.com", "sports", "Sports Illustrated"),
    ("https://www.espncricinfo.com", "sports", "ESPNcricinfo"),

    # --- Search/Apps (10) ---
    ("https://www.google.com/search?q=CTX+format", "search", "Google Search"),
    ("https://www.bing.com/search?q=CTX+format", "search", "Bing Search"),
    ("https://duckduckgo.com/?q=CTX+format", "search", "DuckDuckGo"),
    ("https://en.wikipedia.org/wiki/Main_Page", "search", "Wikipedia Main"),
    ("https://www.reddit.com/r/programming/", "search", "Reddit r/programming"),
    ("https://stackoverflow.com/questions/tagged/python", "search", "Stack Overflow"),
    ("https://github.com/torvalds/linux", "search", "GitHub Repo"),
    ("https://news.ycombinator.com", "search", "Hacker News"),
    ("https://www.producthunt.com", "search", "Product Hunt"),
    ("https://www.craigslist.org", "search", "Craigslist"),

    # --- Entertainment (10) ---
    ("https://www.imdb.com/title/tt1375666/", "entertainment", "IMDb: Inception"),
    ("https://www.rottentomatoes.com/m/the_shawshank_redemption", "entertainment", "Rotten Tomatoes"),
    ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "entertainment", "YouTube Video"),
    ("https://open.spotify.com/artist/06HL4z0CvFAxyc27GXpf02", "entertainment", "Spotify Artist"),
    ("https://www.twitch.tv", "entertainment", "Twitch"),
    ("https://www.goodreads.com/book/show/11127.The_Hitchhiker_s_Guide_to_the_Galaxy", "entertainment", "Goodreads Book"),
    ("https://letterboxd.com/film/parasite-2019/", "entertainment", "Letterboxd Film"),
    ("https://variety.com", "entertainment", "Variety"),
    ("https://www.billboard.com/charts/hot-100/", "entertainment", "Billboard Hot 100"),
    ("https://www.metacritic.com", "entertainment", "Metacritic"),

    # --- E-Commerce (10) ---
    ("https://www.amazon.com/dp/B0D1XD1ZV3", "ecommerce", "Amazon Product"),
    ("https://www.ebay.com", "ecommerce", "eBay"),
    ("https://www.etsy.com", "ecommerce", "Etsy"),
    ("https://www.bestbuy.com", "ecommerce", "Best Buy"),
    ("https://www.walmart.com", "ecommerce", "Walmart"),
    ("https://www.target.com", "ecommerce", "Target"),
    ("https://www.newegg.com", "ecommerce", "Newegg"),
    ("https://www.wayfair.com", "ecommerce", "Wayfair"),
    ("https://www.homedepot.com", "ecommerce", "Home Depot"),
    ("https://www.zappos.com", "ecommerce", "Zappos"),

    # --- Tech/Docs (10) ---
    ("https://developer.mozilla.org/en-US/docs/Web/HTML", "tech", "MDN Web Docs"),
    ("https://docs.python.org/3/tutorial/index.html", "tech", "Python Docs"),
    ("https://doc.rust-lang.org/book/", "tech", "Rust Book"),
    ("https://go.dev/doc/", "tech", "Go Docs"),
    ("https://react.dev", "tech", "React Docs"),
    ("https://www.typescriptlang.org/docs/", "tech", "TypeScript Docs"),
    ("https://arstechnica.com", "tech", "Ars Technica"),
    ("https://www.theverge.com", "tech", "The Verge"),
    ("https://techcrunch.com", "tech", "TechCrunch"),
    ("https://www.wired.com", "tech", "Wired"),

    # --- Finance (10) ---
    ("https://finance.yahoo.com/quote/AAPL/", "finance", "Yahoo Finance: AAPL"),
    ("https://www.marketwatch.com", "finance", "MarketWatch"),
    ("https://www.bloomberg.com", "finance", "Bloomberg"),
    ("https://www.investopedia.com", "finance", "Investopedia"),
    ("https://www.cnbc.com", "finance", "CNBC"),
    ("https://seekingalpha.com", "finance", "Seeking Alpha"),
    ("https://www.morningstar.com", "finance", "Morningstar"),
    ("https://www.google.com/finance/quote/AAPL:NASDAQ", "finance", "Google Finance"),
    ("https://www.wsj.com", "finance", "WSJ"),
    ("https://www.fool.com", "finance", "Motley Fool"),

    # --- Government (10) ---
    ("https://www.usa.gov", "government", "USA.gov"),
    ("https://www.whitehouse.gov", "government", "White House"),
    ("https://www.cdc.gov", "government", "CDC"),
    ("https://www.who.int", "government", "WHO"),
    ("https://www.nasa.gov", "government", "NASA"),
    ("https://www.nih.gov", "government", "NIH"),
    ("https://www.irs.gov", "government", "IRS"),
    ("https://www.congress.gov", "government", "Congress.gov"),
    ("https://data.gov", "government", "Data.gov"),
    ("https://www.noaa.gov", "government", "NOAA"),

    # --- Marketing (10) ---
    ("https://blog.hubspot.com", "marketing", "HubSpot Blog"),
    ("https://mailchimp.com", "marketing", "Mailchimp"),
    ("https://www.salesforce.com", "marketing", "Salesforce"),
    ("https://www.shopify.com/blog", "marketing", "Shopify Blog"),
    ("https://neilpatel.com", "marketing", "Neil Patel"),
    ("https://buffer.com", "marketing", "Buffer"),
    ("https://moz.com", "marketing", "Moz"),
    ("https://www.semrush.com", "marketing", "Semrush"),
    ("https://www.canva.com", "marketing", "Canva"),
    ("https://www.wix.com", "marketing", "Wix"),

    # --- Edge Cases (10) ---
    ("https://example.com", "edge", "example.com (minimal)"),
    ("https://httpbin.org/status/404", "edge", "404 page"),
    ("https://httpbin.org/html", "edge", "httpbin HTML (Moby Dick)"),
    ("https://en.wikipedia.org/wiki/Large_language_model", "edge", "Wikipedia: LLM (long page)"),
    ("https://httpbin.org/image/png", "edge", "PNG image (non-HTML)"),
    ("https://httpbin.org/redirect/3", "edge", "Triple redirect"),
    ("https://ja.wikipedia.org/wiki/%E5%A4%A7%E8%B0%B7%E7%BF%94%E5%B9%B3", "edge", "Japanese Wikipedia"),
    ("https://ar.wikipedia.org/wiki/%D8%A7%D9%84%D8%B5%D9%81%D8%AD%D8%A9_%D8%A7%D9%84%D8%B1%D8%A6%D9%8A%D8%B3%D9%8A%D8%A9", "edge", "Arabic Wikipedia (RTL)"),
    ("https://httpbin.org/xml", "edge", "XML feed (non-HTML)"),
    ("https://httpbin.org/delay/25", "edge", "Slow page (25s, should timeout)"),
]

# ---------------------------------------------------------------------------
# Fetch helper (for raw HTML size comparison)
# ---------------------------------------------------------------------------

async def fetch_html_size(url: str, timeout: float = 20.0) -> int:
    """Fetch raw HTML and return byte count. Returns 0 on failure."""
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            max_redirects=5,
            timeout=timeout,
            verify=False,
            headers={"User-Agent": "CTX-TestSuite/1.0"},
        ) as client:
            resp = await client.get(url)
            return len(resp.content)
    except Exception:
        return 0

# ---------------------------------------------------------------------------
# Per-site test
# ---------------------------------------------------------------------------

async def test_site(
    url: str, category: str, name: str, sem: asyncio.Semaphore
) -> dict:
    result = {
        "url": url,
        "name": name,
        "category": category,
        "status": "unknown",
        "fetch_ok": False,
        "has_content": False,
        "has_sections": False,
        "has_refs": False,
        "content_type": "",
        "html_bytes": 0,
        "ctx_bytes": 0,
        "ctx_lines": 0,
        "reduction_pct": 0.0,
        "paragraph_count": 0,
        "section_count": 0,
        "ref_count": 0,
        "skip_block_count": 0,
        "error": "",
        "warnings": [],
        "duration_ms": 0,
        "ctx_preview": "",
    }

    async with sem:
        t0 = time.monotonic()
        try:
            # Fetch raw HTML size (parallel with conversion would be nice,
            # but keep it simple)
            html_size = await fetch_html_size(url)
            result["html_bytes"] = html_size

            # Run converter
            ctx_text = await asyncio.wait_for(
                convert(url, tier="fast", strip_skip=True),
                timeout=20.0,
            )
            result["fetch_ok"] = True
            result["ctx_bytes"] = len(ctx_text.encode("utf-8"))
            result["ctx_lines"] = len(ctx_text.splitlines())
            result["ctx_preview"] = ctx_text[:500]

            # Reduction
            if html_size > 0:
                result["reduction_pct"] = round(
                    (1 - result["ctx_bytes"] / html_size) * 100, 1
                )

            # Parse the output (round-trip check)
            try:
                doc = parse(ctx_text)
                result["content_type"] = doc.header.attributes.get("type", "")
                result["ref_count"] = len(doc.refs)
                result["has_refs"] = len(doc.refs) > 0

                # Count blocks
                def _count_blocks(blocks, counts):
                    for b in blocks:
                        if b.block_type == "p":
                            counts["paragraphs"] += 1
                        elif b.block_type == "section":
                            counts["sections"] += 1
                        elif b.block_type == "skip":
                            counts["skips"] += 1
                        elif b.block_type == "content":
                            counts["has_content"] = True
                        _count_blocks(b.children, counts)

                counts = {
                    "paragraphs": 0,
                    "sections": 0,
                    "skips": 0,
                    "has_content": False,
                }
                _count_blocks(doc.content, counts)
                result["paragraph_count"] = counts["paragraphs"]
                result["section_count"] = counts["sections"]
                result["skip_block_count"] = counts["skips"]
                result["has_content"] = counts["has_content"]
                result["has_sections"] = counts["sections"] > 0

            except Exception as e:
                result["warnings"].append(f"parse_error: {e}")

            # --- Warnings ---
            if not doc.header.attributes.get("title"):
                result["warnings"].append("no_title")
            if result["paragraph_count"] == 0:
                result["warnings"].append("no_paragraphs")
            if result["section_count"] == 0:
                result["warnings"].append("no_sections")
            if result["ref_count"] == 0:
                result["warnings"].append("no_refs")
            if result["skip_block_count"] > result["paragraph_count"] and result["paragraph_count"] > 0:
                result["warnings"].append("too_many_skip")
            if html_size > 0 and result["reduction_pct"] < 50:
                result["warnings"].append("low_reduction")
            if html_size > 0 and result["ctx_bytes"] > html_size:
                result["warnings"].append("negative_reduction")
            if result["has_content"] and result["paragraph_count"] == 0 and result["section_count"] == 0:
                result["warnings"].append("empty_content")

            # --- Score ---
            has_title = bool(doc.header.attributes.get("title"))
            has_summary = doc.summary is not None and bool(doc.summary.text)

            if (
                result["has_content"]
                and result["paragraph_count"] >= 1
                and (result["reduction_pct"] > 50 or html_size == 0)
            ):
                result["status"] = "pass"
            elif result["has_content"] and (
                result["paragraph_count"] > 0 or result["section_count"] > 0
            ):
                result["status"] = "partial"
            elif result["fetch_ok"] and (has_title or has_summary):
                # SPA/metadata-only: title + description extracted = partial
                result["status"] = "partial"
            elif result["fetch_ok"]:
                result["status"] = "fail"
            else:
                result["status"] = "error"

        except asyncio.TimeoutError:
            result["status"] = "error"
            result["error"] = "Timeout (20s)"
        except httpx.HTTPStatusError as e:
            result["status"] = "error"
            result["error"] = f"HTTP {e.response.status_code}"
        except httpx.ConnectError as e:
            result["status"] = "error"
            result["error"] = f"Connection error: {e}"
        except Exception as e:
            result["status"] = "error"
            result["error"] = f"{type(e).__name__}: {e}"
            result["warnings"].append(f"traceback: {traceback.format_exc()[-300:]}")

        result["duration_ms"] = round((time.monotonic() - t0) * 1000)

    return result

# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(results: list[dict]) -> str:
    lines = []
    lines.append("# CTX 100-Site Test Report")
    lines.append("")
    lines.append(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Tier**: fast (DOM rules only)")
    lines.append(f"**Total sites**: {len(results)}")
    lines.append("")

    # --- Overall summary ---
    status_counts = {}
    for r in results:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1

    lines.append("## Overall Results")
    lines.append("")
    total = len(results)
    for status in ["pass", "partial", "fail", "error", "unknown"]:
        count = status_counts.get(status, 0)
        pct = round(count / total * 100, 1) if total else 0
        icon = {"pass": "+", "partial": "~", "fail": "-", "error": "!", "unknown": "?"}.get(status, "?")
        lines.append(f"  [{icon}] {status:8s}: {count:3d} ({pct}%)")
    lines.append("")

    # --- Per-category breakdown ---
    lines.append("## Per-Category Breakdown")
    lines.append("")
    lines.append(f"| {'Category':<15s} | {'Pass':>5s} | {'Partial':>7s} | {'Fail':>5s} | {'Error':>5s} | {'Avg Reduction':>14s} |")
    lines.append(f"|{'-'*17}|{'-'*7}|{'-'*9}|{'-'*7}|{'-'*7}|{'-'*16}|")

    categories = sorted(set(r["category"] for r in results))
    for cat in categories:
        cat_results = [r for r in results if r["category"] == cat]
        p = sum(1 for r in cat_results if r["status"] == "pass")
        pa = sum(1 for r in cat_results if r["status"] == "partial")
        f = sum(1 for r in cat_results if r["status"] == "fail")
        e = sum(1 for r in cat_results if r["status"] == "error")
        reductions = [r["reduction_pct"] for r in cat_results if r["reduction_pct"] > 0]
        avg_red = f"{sum(reductions)/len(reductions):.1f}%" if reductions else "N/A"
        lines.append(f"| {cat:<15s} | {p:>5d} | {pa:>7d} | {f:>5d} | {e:>5d} | {avg_red:>14s} |")

    lines.append("")

    # --- All results table ---
    lines.append("## All Results")
    lines.append("")
    lines.append(f"| {'Status':<8s} | {'Category':<12s} | {'Name':<30s} | {'HTML':>8s} | {'CTX':>8s} | {'Reduct':>7s} | {'Para':>4s} | {'Refs':>4s} | {'ms':>6s} | {'Warnings/Error':<40s} |")
    lines.append(f"|{'-'*10}|{'-'*14}|{'-'*32}|{'-'*10}|{'-'*10}|{'-'*9}|{'-'*6}|{'-'*6}|{'-'*8}|{'-'*42}|")

    for r in sorted(results, key=lambda x: ({"pass": 0, "partial": 1, "fail": 2, "error": 3}.get(x["status"], 4), x["category"])):
        html_s = f"{r['html_bytes']//1024}K" if r["html_bytes"] > 1024 else f"{r['html_bytes']}B"
        ctx_s = f"{r['ctx_bytes']//1024}K" if r["ctx_bytes"] > 1024 else f"{r['ctx_bytes']}B"
        red_s = f"{r['reduction_pct']}%" if r["reduction_pct"] else "-"
        warn_str = r["error"] if r["error"] else ", ".join(r["warnings"][:3])
        lines.append(
            f"| {r['status']:<8s} | {r['category']:<12s} | {r['name']:<30s} "
            f"| {html_s:>8s} | {ctx_s:>8s} | {red_s:>7s} "
            f"| {r['paragraph_count']:>4d} | {r['ref_count']:>4d} | {r['duration_ms']:>6d} "
            f"| {warn_str:<40s} |"
        )

    lines.append("")

    # --- Errors detail ---
    errors = [r for r in results if r["status"] == "error"]
    if errors:
        lines.append("## Errors (Detail)")
        lines.append("")
        for r in errors:
            lines.append(f"### {r['name']} ({r['category']})")
            lines.append(f"- **URL**: {r['url']}")
            lines.append(f"- **Error**: {r['error']}")
            if r["warnings"]:
                for w in r["warnings"]:
                    if w.startswith("traceback:"):
                        lines.append(f"- **Traceback**: `{w[10:].strip()}`")
            lines.append("")

    # --- Failures detail ---
    failures = [r for r in results if r["status"] == "fail"]
    if failures:
        lines.append("## Failures (Detail)")
        lines.append("")
        for r in failures:
            lines.append(f"### {r['name']} ({r['category']})")
            lines.append(f"- **URL**: {r['url']}")
            lines.append(f"- **Warnings**: {', '.join(r['warnings'])}")
            lines.append(f"- **CTX bytes**: {r['ctx_bytes']}")
            lines.append(f"- **Paragraphs**: {r['paragraph_count']}, Sections: {r['section_count']}")
            if r["ctx_preview"]:
                lines.append(f"- **Preview**:")
                lines.append(f"```")
                lines.append(r["ctx_preview"][:300])
                lines.append(f"```")
            lines.append("")

    # --- Warning frequency ---
    lines.append("## Warning Frequency")
    lines.append("")
    all_warnings = []
    for r in results:
        for w in r["warnings"]:
            tag = w.split(":")[0] if ":" in w else w
            all_warnings.append(tag)

    warn_counts = {}
    for w in all_warnings:
        warn_counts[w] = warn_counts.get(w, 0) + 1

    for w, count in sorted(warn_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- **{w}**: {count} sites")

    lines.append("")

    # --- Recommended fixes ---
    lines.append("## Recommended Fixes (Auto-Generated)")
    lines.append("")

    fix_map = {
        "no_paragraphs": "Extractor: Broaden paragraph detection beyond `<p>` tags (some sites use `<div>`, `<span>`, `<article>` for body text)",
        "no_sections": "Annotator: Generate a synthetic `§1` from page title when no headings are found",
        "no_refs": "Annotator: Broaden link detection — check `<li>`, `<span>`, `<div>` containers, not just `<p>`",
        "no_title": "Extractor: Fall back to `<h1>` text or URL-derived title when `<title>` and OG tags are missing",
        "low_reduction": "Pipeline: Investigate pages where CTX is >50% of HTML — likely minimal-markup pages or text-heavy content",
        "negative_reduction": "Pipeline: CTX output should never exceed HTML input — check for extraction bloat or repeated content",
        "too_many_skip": "Extractor: Cap skip blocks at 5 per document, merge duplicates",
        "empty_content": "Extractor: When readability produces empty content, fall back to full `<body>` text extraction",
        "parse_error": "Parser/Emitter: Fix round-trip failures — the emitter is producing output the parser can't read",
        "traceback": "Pipeline: Add try-except around each pipeline stage to produce `§error` blocks instead of crashing",
    }

    for w, count in sorted(warn_counts.items(), key=lambda x: -x[1]):
        if w in fix_map:
            lines.append(f"- **{w}** ({count} sites): {fix_map[w]}")

    error_types = {}
    for r in results:
        if r["error"]:
            tag = r["error"].split(":")[0].strip()
            error_types[tag] = error_types.get(tag, 0) + 1

    if error_types:
        lines.append("")
        lines.append("### Error Types")
        for et, count in sorted(error_types.items(), key=lambda x: -x[1]):
            lines.append(f"- **{et}**: {count} sites")

    lines.append("")
    lines.append("---")
    lines.append("*Generated by CTX test suite v1.0*")

    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    print(f"CTX 100-Site Test Suite")
    print(f"{'='*60}")
    print(f"Testing {len(SITES)} sites with fast tier...")
    print()

    sem = asyncio.Semaphore(10)  # max 10 concurrent requests
    tasks = [test_site(url, cat, name, sem) for url, cat, name in SITES]
    results = await asyncio.gather(*tasks)

    # Sort by category then name
    results = sorted(results, key=lambda r: (r["category"], r["name"]))

    # Print live summary
    status_counts = {}
    for r in results:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1
        icon = {"pass": "\u2713", "partial": "~", "fail": "\u2717", "error": "!"}.get(r["status"], "?")
        status_pad = f"{r['status']:<8s}"
        print(f"  {icon} {status_pad} {r['category']:<12s} {r['name']:<30s} {r['duration_ms']:>5d}ms  {r['error'] or ''}")

    print()
    print(f"{'='*60}")
    total = len(results)
    for s in ["pass", "partial", "fail", "error"]:
        c = status_counts.get(s, 0)
        print(f"  {s:<8s}: {c:3d} ({c/total*100:.0f}%)")

    # Write JSON results
    out_dir = Path(__file__).parent
    json_path = out_dir / "results_100.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults: {json_path}")

    # Generate and write report
    report = generate_report(results)
    report_path = out_dir / "REPORT_100.md"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"Report:  {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
