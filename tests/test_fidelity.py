#!/usr/bin/env python3
"""CTX content fidelity test.

Fetches 10 text-heavy pages, converts to CTX, extracts plain text from
both the original HTML and the CTX output, and compares them side-by-side
to verify no meaningful content is lost.

Usage:
    cd /home/dev-ai/ctx
    venv/bin/python tests/test_fidelity.py
"""

from __future__ import annotations

import asyncio
import re
import sys
import warnings
from pathlib import Path

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from readability import Document as ReadabilityDoc

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ctx.converter.fetcher import fetch
from ctx.converter.pipeline import convert
from ctx.models import CTXBlock, CTXDocument
from ctx.parser import parse

# ── Test pages: text-heavy, publicly accessible, passed 100-site test ──

PAGES: list[tuple[str, str]] = [
    # Long-form tech docs
    ("https://go.dev/doc/effective_go", "Go Docs: Effective Go"),
    ("https://docs.python.org/3/tutorial/controlflow.html", "Python Docs: Control Flow"),
    ("https://doc.rust-lang.org/book/ch03-00-common-programming-concepts.html", "Rust Book: Ch 3"),
    ("https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Functions", "MDN: JS Functions"),
    # Finance/reference articles
    ("https://www.investopedia.com/terms/s/stockmarket.asp", "Investopedia: Stock Market"),
    ("https://www.investopedia.com/terms/b/blockchain.asp", "Investopedia: Blockchain"),
    # Government/reference content
    ("https://www.cdc.gov/flu/about/index.html", "CDC: About Flu"),
    ("https://www.whitehouse.gov/about-the-white-house/", "White House: About"),
    # Marketing/blog articles
    ("https://blog.hubspot.com/marketing/beginner-inbound-lead-generation-guide-ht", "HubSpot: Lead Gen Guide"),
    ("https://moz.com/beginners-guide-to-seo", "Moz: SEO Guide"),
]


def extract_readable_text(html: str) -> str:
    """Extract readable text from HTML using the same pipeline as the converter:
    readability for content isolation, then BeautifulSoup for text extraction."""
    if not html or not html.strip():
        return ""

    # Use readability to isolate main content (same as extractor.py)
    try:
        rdoc = ReadabilityDoc(html)
        content_html = rdoc.summary()
    except Exception:
        content_html = html

    soup = BeautifulSoup(content_html, "html.parser")

    # Remove script/style tags
    for tag in soup.find_all(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_ctx_text(ctx_raw: str) -> str:
    """Extract plain text directly from raw CTX output.

    Strips structural delimiters and skip blocks, keeping only content text.
    Works on the raw string to avoid parser limitations with multi-line blocks.
    """
    lines = ctx_raw.splitlines()
    texts: list[str] = []
    in_skip = False
    skip_indent = 0

    for line in lines:
        stripped = line.lstrip()

        # Track skip blocks
        if "[skip]" in stripped:
            in_skip = True
            skip_indent = len(line) - len(stripped)
            continue

        # Exit skip block when indent returns to skip level or less
        if in_skip:
            current_indent = len(line) - len(stripped)
            if stripped and current_indent <= skip_indent and not stripped.startswith(" "):
                in_skip = False
            else:
                continue

        # Skip structural lines (delimiters, metadata, refs, errors)
        if stripped.startswith(("§doc.", "§nav", "§footer", "§sidebar", "§ad",
                                "§cookie", "§auth", "§error", "§ref ", "§delta",
                                "§toast", "§update", "§summary",
                                "†", "∷", "::/", "∷/")):
            continue

        # Skip section/block markers but keep their title text
        if re.match(r"§\d\s", stripped):
            title = re.sub(r"§\d\s+", "", stripped)
            title = re.sub(r"\s+id=\S+", "", title)
            if title:
                texts.append(title)
            continue

        # Skip leaf block markers but keep content on same line
        if stripped.startswith(("§p ", "§code ", "§quote ", "§aside ")):
            content = re.sub(r"^§\w+\s*", "", stripped)
            if content:
                texts.append(content)
            continue

        # Skip bare block markers
        if re.match(r"^§(p|code|quote|aside|content\.\w+)$", stripped):
            continue

        # Data block markers
        if stripped.startswith(("∷ ", ":: ")):
            continue

        # Everything else is content text
        if stripped:
            texts.append(stripped)

    combined = " ".join(texts)
    combined = re.sub(r"\s+", " ", combined).strip()
    # Strip citation markers for cleaner comparison
    combined = re.sub(r"\[ref\d+\]", "", combined)
    combined = re.sub(r"\s+", " ", combined).strip()
    return combined


def normalize_for_comparison(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace for fuzzy matching."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_sentences(text: str) -> list[str]:
    """Split text into sentence-like chunks for overlap comparison."""
    # Split on sentence-ending punctuation followed by space or end
    raw = re.split(r"(?<=[.!?])\s+", text)
    # Filter out very short fragments (< 20 chars)
    return [s.strip() for s in raw if len(s.strip()) >= 20]


def compute_overlap(html_text: str, ctx_text: str) -> dict:
    """Compare HTML-extracted text vs CTX-extracted text."""
    html_words = normalize_for_comparison(html_text).split()
    ctx_words = normalize_for_comparison(ctx_text).split()

    html_word_count = len(html_words)
    ctx_word_count = len(ctx_words)
    word_ratio = ctx_word_count / html_word_count if html_word_count > 0 else 0

    # Sentence-level overlap
    html_sentences = split_sentences(html_text)
    ctx_sentences = split_sentences(ctx_text)

    # Normalize sentences for matching
    html_sent_set = {normalize_for_comparison(s) for s in html_sentences}
    ctx_sent_set = {normalize_for_comparison(s) for s in ctx_sentences}

    # How many HTML sentences appear in CTX (using substring matching for flexibility)
    matched = 0
    for hs in html_sent_set:
        # Check if the sentence (or most of it) appears in the CTX text
        # Use first 60 chars as a fingerprint to handle minor reformatting
        fingerprint = hs[:60]
        if fingerprint in normalize_for_comparison(ctx_text):
            matched += 1

    sentence_overlap = matched / len(html_sent_set) if html_sent_set else 0

    # Find a few example missing sentences
    missing = []
    for hs in html_sent_set:
        fingerprint = hs[:60]
        if fingerprint not in normalize_for_comparison(ctx_text):
            # Get original (non-normalized) version
            for orig in html_sentences:
                if normalize_for_comparison(orig)[:60] == fingerprint:
                    missing.append(orig[:80] + "..." if len(orig) > 80 else orig)
                    break
            if len(missing) >= 3:
                break

    # Determine verdict
    if sentence_overlap >= 0.9 and word_ratio >= 0.85:
        verdict = "PASS"
    elif sentence_overlap >= 0.7 or word_ratio >= 0.7:
        verdict = "PARTIAL"
    else:
        verdict = "FAIL"

    return {
        "html_words": html_word_count,
        "ctx_words": ctx_word_count,
        "word_ratio": word_ratio,
        "html_sentences": len(html_sent_set),
        "ctx_sentences": len(ctx_sent_set),
        "matched_sentences": matched,
        "sentence_overlap": sentence_overlap,
        "missing_examples": missing,
        "verdict": verdict,
    }


async def test_page(url: str, name: str) -> dict | None:
    """Run fidelity test on a single page."""
    print(f"\n{'=' * 60}")
    print(f"  {name}")
    print(f"  {url}")
    print(f"{'=' * 60}")

    # Fetch raw HTML once
    try:
        result = await fetch(url)
        if result.error or not result.html:
            print(f"  SKIP: fetch failed ({result.error})")
            return None
        html = result.html
        fetched_url = result.url or url
    except Exception as e:
        print(f"  SKIP: fetch exception ({e})")
        return None

    # Extract readable text from HTML
    html_text = extract_readable_text(html)
    if len(html_text) < 100:
        print(f"  SKIP: readability extracted too little text ({len(html_text)} chars)")
        return None

    # Convert to CTX by passing raw HTML (avoids double-fetch and 403s)
    ctx_output = await convert(html, tier="fast", source_url=fetched_url)

    # Extract text from raw CTX output
    ctx_text = extract_ctx_text(ctx_output)
    if not ctx_text:
        print(f"  SKIP: no text extracted from CTX output")
        return None

    # Compare
    comparison = compute_overlap(html_text, ctx_text)

    # Print results
    wr = comparison["word_ratio"]
    so = comparison["sentence_overlap"]
    print(f"  HTML text:  {comparison['html_words']:,} words")
    print(f"  CTX text:   {comparison['ctx_words']:,} words ({wr:.1%} of HTML)")
    print(f"  Sentences:  {comparison['html_sentences']} HTML / {comparison['ctx_sentences']} CTX "
          f"({comparison['matched_sentences']} matched, {so:.1%} overlap)")
    if comparison["missing_examples"]:
        print(f"  Missing:    {comparison['missing_examples'][0]}")
        for m in comparison["missing_examples"][1:]:
            print(f"              {m}")
    print(f"  Verdict:    {comparison['verdict']}")

    comparison["name"] = name
    comparison["url"] = url
    return comparison


async def main():
    print("CTX Content Fidelity Test")
    print("=" * 60)
    print(f"Testing {len(PAGES)} text-heavy pages")
    print("Comparing readable text from HTML vs CTX output\n")

    results = []
    for url, name in PAGES:
        r = await test_page(url, name)
        if r:
            results.append(r)

    # Summary table
    print("\n\n")
    print("=" * 80)
    print("  SUMMARY")
    print("=" * 80)
    print(f"{'Page':<35} {'Words':>12} {'Word %':>8} {'Sent %':>8} {'Verdict':>8}")
    print("-" * 80)

    verdicts = {"PASS": 0, "PARTIAL": 0, "FAIL": 0}
    for r in results:
        verdicts[r["verdict"]] += 1
        ctx_w = f"{r['ctx_words']:,}/{r['html_words']:,}"
        print(f"{r['name']:<35} {ctx_w:>12} {r['word_ratio']:>7.1%} "
              f"{r['sentence_overlap']:>7.1%} {r['verdict']:>8}")

    print("-" * 80)
    total = len(results)
    print(f"\nTested: {total}  |  "
          f"PASS: {verdicts['PASS']}  |  "
          f"PARTIAL: {verdicts['PARTIAL']}  |  "
          f"FAIL: {verdicts['FAIL']}")

    if total > 0:
        avg_word = sum(r["word_ratio"] for r in results) / total
        avg_sent = sum(r["sentence_overlap"] for r in results) / total
        print(f"Avg word preservation: {avg_word:.1%}")
        print(f"Avg sentence overlap:  {avg_sent:.1%}")


if __name__ == "__main__":
    asyncio.run(main())
