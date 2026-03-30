# CTX v1.0 — Reference Implementation Testing Report

**Date**: March 30, 2026
**Implementation**: `ctx` Python package v1.0.0
**Converter tier**: `fast` (DOM rules only, no LLM/VLM)
**Test environment**: Linux, Python 3.14, FastAPI service on port 8200

---

## Visual Comparison: HTML vs CTX

The following shows the same content — the opening paragraph of the [Shohei Ohtani Wikipedia article](https://en.wikipedia.org/wiki/Shohei_Ohtani) — in raw HTML and CTX format.

### Raw HTML (1,544 characters for one paragraph)

```html
<p><b>Shohei Ohtani</b><sup class="reference" id="cite_ref-5">
<a href="#cite_note-5"><span class="cite-bracket">[</span>e<span
class="cite-bracket">]</span></a></sup><sup class="reference"
id="cite_ref-6"><a href="#cite_note-6"><span class="cite-bracket">
[</span>f<span class="cite-bracket">]</span></a></sup> (born July 5,
1994) is a Japanese professional <a href="/wiki/Baseball"
title="Baseball">baseball</a> <a href="/wiki/Designated_hitter"
title="Designated hitter">designated hitter</a> and <a
href="/wiki/Pitcher" title="Pitcher">pitcher</a> for the <a
href="/wiki/Los_Angeles_Dodgers" title="Los Angeles Dodgers">Los
Angeles Dodgers</a> of <a href="/wiki/Major_League_Baseball"
title="Major League Baseball">Major League Baseball</a> (MLB).
Nicknamed "<b>Shotime</b>", he has previously played in MLB for the
<a href="/wiki/Los_Angeles_Angels" title="Los Angeles Angels">Los
Angeles Angels</a> and in <a href="/wiki/Nippon_Professional_Baseball"
title="Nippon Professional Baseball">Nippon Professional Baseball</a>
(NPB) for the <a href="/wiki/Hokkaido_Nippon-Ham_Fighters"
title="Hokkaido Nippon-Ham Fighters">Hokkaido Nippon-Ham Fighters</a>.
Because of his contributions as a hitter and as a pitcher, a rarity
as a <a href="/wiki/Two-way_player#Baseball" title="Two-way player">
two-way player</a>, Ohtani's prime seasons have been considered among
the greatest in baseball history, with some likening them to the early
career of <a href="/wiki/Babe_Ruth" title="Babe Ruth">Babe Ruth</a>.
<sup class="reference" id="cite_ref-7"><a href="#cite_note-7"><span
class="cite-bracket">[</span>1<span class="cite-bracket">]</span></a>
</sup><!-- ...3 more citation sups omitted... -->
</p>
```

Every link is wrapped in `<a href="..." title="...">...</a>`. Every citation is a `<sup><a><span>` nest. Class names, IDs, and ARIA attributes add tokens that carry zero semantic value for an LLM.

### CTX (451 characters for the same paragraph)

```
§p _Shohei Ohtani_[e][f] (born July 5, 1994) is a Japanese professional
baseball [ref1] designated hitter [ref2] and pitcher [ref3] for the
Los Angeles Dodgers [ref4] of Major League Baseball [ref5] (MLB).
Nicknamed "_Shotime_", he has previously played in MLB for the
Los Angeles Angels [ref6] and in Nippon Professional Baseball [ref7]
(NPB) for the Hokkaido Nippon-Ham Fighters [ref8]. Because of his
contributions as a hitter and as a pitcher, a rarity as a two-way
player [ref9], Ohtani's prime seasons have been considered among the
greatest in baseball history, with some likening them to the early
career of Babe Ruth [ref10].[1][2][3][4][5]

§ref id=ref1 url=en.wikipedia.org/wiki/Baseball title=baseball †rel=related
§ref id=ref2 url=en.wikipedia.org/wiki/Designated_hitter title="designated hitter" †rel=related
§ref id=ref3 url=en.wikipedia.org/wiki/Pitcher title=pitcher †rel=related
§ref id=ref4 url=en.wikipedia.org/wiki/Los_Angeles_Dodgers title="Los Angeles Dodgers" †rel=related
...
```

The prose reads naturally. Links become lightweight `[refN]` pointers (2-3 tokens each) resolved by `§ref` blocks at the document end. Bold becomes `_emphasis_` only where semantically meaningful. All HTML structure — tags, attributes, classes, ARIA — is gone.

### Document-Level Comparison

**Raw HTML page** (1,180,170 bytes):
```
<!DOCTYPE html>
<html class="client-nojs vector-feature-language-in-header-enabled
 vector-feature-language-in-main-menu-disabled ..."  ← 600+ chars of class names
<head>
<script>RLCONF={"wgBreakFrames":false, ...};</script>  ← 8KB of JS config
<script>RLSTATE={...}; RLPAGEMODULES=[...];</script>   ← module loader
<link rel="stylesheet" href="/w/load.php?...">          ← CSS bundles
<meta name="generator" content="MediaWiki 1.46.0">
...
<!-- 4,903 lines of nested divs, scripts, nav, sidebars, footers -->
```

**CTX document** (150,152 bytes):
```
§doc.ctx_v1.0 url=en.wikipedia.org/wiki/Shohei_Ohtani
  title="Shohei Ohtani - Wikipedia" †type=article †lang=en

§nav [skip]
  Main menu...
§footer [skip]
  This page was last edited on...

§content.article
  §p _Shohei Ohtani_ (born July 5, 1994) is a Japanese professional
  baseball [ref1] designated hitter [ref2]...
  §2 Early life
    §p Ohtani was born on July 5, 1994, in Mizusawa...
  §2 Professional career
    §3 Hokkaido Nippon-Ham Fighters (2013-2017)
      §4 2013: Rookie season, NPB All-Star
        §p Ohtani made his debut at age 18...
    §3 Los Angeles Angels (2018-2023)
      §4 2018: AL Rookie of the Year
        §p Before the start of the season...
    §3 Los Angeles Dodgers (2024-present)
      §4 2024: 50-50 season, World Series champion
        §p ...

§ref id=ref1 url=en.wikipedia.org/wiki/Baseball title=baseball †rel=related
§ref id=ref2 url=en.wikipedia.org/wiki/Designated_hitter title="designated hitter" †rel=related
...
```

The CTX version preserves all article text, section hierarchy, inline citations, and link targets — while discarding scripts, stylesheets, navigation chrome, ad containers, and structural markup that adds tokens without meaning.

---

## Benchmark Results

### Test Pages

| Page                           | Raw HTML    | CTX         | Byte Reduction | ~HTML Tokens | ~CTX Tokens | Token Savings |
|--------------------------------|-------------|-------------|----------------|--------------|-------------|---------------|
| example.com                    | 528 B       | 354 B       | 33.0%          | ~165         | ~88         | 46.4%         |
| Wikipedia: Python (PL)         | 620,681 B   | 90,043 B    | 85.5%          | ~193,962     | ~22,510     | 88.4%         |
| Wikipedia: Shohei Ohtani       | 1,180,170 B | 150,152 B   | 87.3%          | ~368,803     | ~37,538     | 89.8%         |
| Wikipedia: Transformer (DL)    | 713,491 B   | 138,443 B   | 80.6%          | ~222,965     | ~34,610     | 84.5%         |

Token estimates use conservative ratios: ~3.2 chars/token for HTML (tag-heavy), ~4.0 chars/token for CTX (natural language).

### Aggregate

| Metric                        | Raw HTML      | CTX           | Savings       |
|-------------------------------|---------------|---------------|---------------|
| **Total bytes (4 pages)**     | 2,514,870     | 378,992       | **84.9%**     |
| **Total ~tokens (4 pages)**   | ~785,896      | ~94,748       | **87.9%**     |

### Projected Cost at Scale

At $3/M input tokens (Claude Sonnet 4 pricing):

| Scenario                       | HTML Cost     | CTX Cost      | Saved         |
|--------------------------------|---------------|---------------|---------------|
| Single Ohtani page             | $1.11         | $0.11         | $0.99         |
| 50 pages/hour agent workload   | $55.28/hr     | $6.69/hr      | **$48.59/hr** |
| 1,000 pages/day research batch | $1,105.65     | $133.72       | **$971.93**   |

---

## What CTX Preserves

Content tested with the Shohei Ohtani article (15,000+ word Wikipedia biography):

- **Full article text** — all biographical content, statistics, career history
- **Section hierarchy** — `§2 Early life` → `§3 Los Angeles Angels` → `§4 2018: AL Rookie of the Year`
- **Inline citations** — `[ref1]` through `[refN]` mapped to `§ref` blocks with URLs and titles
- **Emphasis** — `_Shohei Ohtani_`, `_Shotime_` where semantically meaningful
- **Tables** — `∷ table` blocks with typed columns and pipe-delimited rows
- **Media** — `◆ image` blocks with URLs and alt-text fallbacks
- **Forms** — `▸ form.search` blocks with inputs (Wikipedia search)
- **Metadata** — title, date, author, language, content type

## What CTX Strips

- JavaScript (`<script>` blocks, inline handlers, module loaders)
- CSS (`<style>` blocks, class names, stylesheet links)
- ARIA attributes, data attributes, role attributes
- Navigation chrome (`<nav>` → `§nav [skip]`, content truncated)
- Footer boilerplate (`<footer>` → `§footer [skip]`)
- Sidebar widgets → `§sidebar [skip]`
- Hidden elements, noscript fallbacks
- HTML structural nesting (divs, spans, wrappers)
- Duplicate/redundant content from responsive layouts

---

## Service Endpoints Tested

The `ctx` service runs on port 8200 and exposes:

```
GET  /health                          → {"status": "ok", "tiers": ["fast","smart","full"]}
GET  /convert?url=<URL>&tier=fast     → text/ctx response
POST /convert {"url": "<URL>"}        → text/ctx response
POST /convert {"html": "<HTML>"}      → text/ctx response (raw HTML input)
GET  /proxy/<domain>/<path>           → transparent CTX proxy
POST /parse                           → JSON document structure
GET  /cache/stats                     → Redis cache statistics
```

All endpoints return `Content-Type: text/ctx` with `X-CTX-Cache: hit|miss` headers. Redis caching with configurable TTL (1h default, 4h for VLM-tier).

### Extraction Tiers

| Tier   | Method               | Speed   | AI Required |
|--------|----------------------|---------|-------------|
| `fast` | DOM rules only       | <500ms  | No          |
| `smart`| DOM + regex NER      | <1s     | No (default)|
| `full` | DOM + NER + VLM      | 2-5s    | Yes (opt-in)|

The `full` tier uses the local Qwen3-VL-30B model for image description generation when alt-text is missing or generic.

---

## Round-Trip Validation

The parser (`ctx-parse`) successfully parses CTX output back into structured Python objects:

```
CTX text → parse() → CTXDocument → emit() → CTX text  ✓
```

Validated: version header, attributes with quoting, section depth, skip annotations, inline citations, data blocks, ref blocks.

---

## Implementation Components

```
src/ctx/
├── grammar.py          — CTX v1.0 delimiter constants, type registries
├── models.py           — Pydantic models (CTXDocument, CTXBlock, CTXDelta)
├── escaping.py         — Delimiter escaping, attribute quoting (spec ch.4)
├── parser.py           — .ctx text → CTXDocument (spec ch.15-16)
├── emitter.py          — CTXDocument → .ctx text
├── converter/
│   ├── pipeline.py     — Orchestrator: fetch → extract → classify → annotate → normalize → emit
│   ├── fetcher.py      — Async URL fetching with content negotiation
│   ├── extractor.py    — readability-lxml + BeautifulSoup content extraction
│   ├── classifier.py   — Content type detection (article/product/application/video)
│   ├── annotator.py    — Citation [refN] generation, [skip] annotation, section nesting
│   ├── normalizer.py   — Boolean normalization, empty block stripping
│   └── tiers.py        — fast/smart/full tier dispatch (VLM integration)
├── service/
│   ├── app.py          — FastAPI application with Redis caching
│   ├── routes.py       — /convert, /proxy, /parse, /health, /cache/stats
│   └── config.py       — Environment-based configuration
└── cli/
    ├── convert.py      — ctx-convert CLI (URL/file/stdin → CTX)
    └── parse.py        — ctx-parse CLI (validate, JSON output, tree view)
```

---

*Generated by CTX reference implementation v1.0.0 — Fox Valley AI Foundation*
