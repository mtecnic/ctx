# CTX — Context Transfer Format

**Specification v1.0 Release Candidate 2**
**Published by Nic Wienandt, wAIve.online and the Fox Valley AI Foundation**
**March 2026**

---

## Abstract

CTX (Context Transfer Format) is a universal interchange format designed for optimal consumption by large language models. It replaces the current fragmented pipeline — where HTML, PDF, images, audio, and application content each require separate extraction and conversion tooling — with a single, token-efficient target format that any source can convert into.

CTX is not a rendering format. It does not replace HTML for browsers or PDF for print. It is the **content layer between the web and AI** — optimized for how transformers tokenize, attend, and reason.

**Repository**: github.com/mtecnic/ctx
**Contact**: foxfoundation.ai

---

## Quick Reference

```
§doc.ctx_v1.0 url=example.com/article title="How LLMs Read the Web" †date=2026-03-29 †type=article

§summary tokens=50
  Overview of token efficiency in AI web browsing and how CTX reduces overhead by ~24%.

§nav [skip]
  Home | Blog | Docs | About

§content.article
  §1 How LLMs Read the Web
    §p Every page an AI agent reads costs tokens. The CTX specification [ref1]
    solves this with single-token delimiters, semantic types, and skip annotations.

    ∷ table cols=Format,Tokens:int,Savings
      Raw HTML   | 45000 | —
      Markdown   | 4500  | 90%
      CTX        | 3400  | 92%
    ∷/

    §2 Related Articles [skip]
      §p Clickbait stripped at the section level.

    ▸ button.action id=btn_try label="Try CTX" action=GET:/playground

§footer [skip]
  Copyright, privacy, terms

§ref id=ref1 url=foxfoundation.ai/ctx title="CTX Specification" †rel=spec
```

---

## Table of Contents

1. Motivation
2. Design Principles
3. Format Specification
4. Escaping and Encoding
5. Content Type Conversion Examples
6. Token Efficiency Analysis
7. HTTP Content Negotiation
8. Commerce and Publisher Monetization
9. Authentication Challenge
10. Interaction Responses and State Deltas
11. Converter Architecture
12. Error Handling
13. Security Considerations
14. Format Comparison
15. Competitive Landscape
16. Canonical Parsing Algorithm
17. Formal Grammar (EBNF)
18. Reference Implementation Roadmap
19. Internationalization
20. Governance and Extensibility
21. Changelog
22. 100-Site Test Results

---

## 1. Motivation

Every content type on the internet goes through a lossy, expensive translation before an LLM can consume it. HTML gets stripped. PDFs get OCR'd. Images get captioned. Each translation is a different pipeline, different tooling, different failure mode.

A typical 2,000-word article arrives as ~45,000 tokens of raw HTML. Markdown conversion reduces this to ~4,500 — still carrying structural overhead that adds tokens without meaning.

CTX collapses the pipeline into one format: more token-efficient than markdown, more expressive than plain text, universally applicable across content types.

### What CTX Is

- A text-based document format optimized for transformer tokenization
- A universal conversion target for any content source
- A content negotiation format for AI agent / publisher interaction
- An open specification with no proprietary dependencies

### What CTX Is Not

- A replacement for HTML, a rendering format, a storage format, a protocol, or a collaboration format
- Agent-to-agent communication belongs in the orchestration layer; CTX documents are read-only

---

## 2. Design Principles

### 2.1 Single-Token Delimiters

| Delimiter | Purpose | Status |
|-----------|---------|--------|
| `§` | Block boundary | ✅ Verified |
| `†` | Metadata | ✅ Verified |
| `◆` | Media reference | ⚠️ Fallback: `<>` |
| `▸` | Interactive element | ⚠️ Fallback: `>>` |
| `∷` | Data block | ⚠️ Fallback: `::` |

Converters MUST auto-swap to ASCII fallbacks via `--target` flag.

### 2.2 Semantic Type Annotations

`§content.article`, `§content.product`, `§content.email`, `§content.video`, etc. Domain-specific subtypes allowed; unknown subtypes treated as `§content.reference`.

Skip containers: `§nav [skip]`, `§sidebar [skip]`, `§ad [skip]`, `§footer [skip]`, `§auth [skip]`, `§cookie [skip]`

### 2.3 Depth-Marked Hierarchy

`§1`-`§4` with mandatory depth markers. Leaf blocks inherit depth. Semantic containers exempt.

### 2.4 Skip Annotations

`[skip]` on containers and section blocks (`§2 Related [skip]`). Sections with `[skip]` strip the entire subtree. Converters strip by default.

### 2.5 Inline Semantic Annotations

`_underscore_` for meaning-critical emphasis only. Target: <10 per 1,000 words. Full Unicode body text.

### 2.6 Inline Citation Pointers (v1.0)

When body text references a linked resource, converters SHOULD insert a bracketed reference ID that matches a `§ref` block's `id=` attribute. This preserves the spatial relationship between prose and the URL it references without importing Markdown's `[text](url)` syntax.

```
§p The new KV cache standard [ref1] benchmarked significantly faster
than the legacy implementation [ref2], according to recent analysis [ref3].

§ref id=ref1 url=example.com/cache-spec title="Cache Standard" †rel=spec
§ref id=ref2 url=example.com/legacy title="Legacy Docs" †rel=related
§ref id=ref3 url=example.com/analysis title="Performance Analysis" †rel=source
```

**Rules**:
- Citation pointers are plain text `[refN]` in the body — they are not structural delimiters and require no escaping
- The `N` in `[refN]` MUST correspond to the `id=` attribute of a `§ref` block in the same document
- Citation IDs SHOULD be sequential: ref1, ref2, ref3, etc.
- Not all `§ref` blocks need to be cited inline; uncited refs remain valid navigational metadata
- Converters SHOULD generate citation pointers when an HTML `<a>` tag appears inline within article body text. Links in navigation, footers, and sidebars do NOT generate citations.

**Token cost**: `[ref1]` is typically 2-3 tokens. For an article with 10 inline links, this costs ~25 tokens — far less than Markdown's `[text](url)` at 4+ tokens per link, and it preserves the spatial context that a footer-only `§ref` block loses entirely.

### 2.7 Multimodal Through Typed References

Mandatory semantic fallback descriptions with provenance metadata on all media blocks.

### 2.8 Block Identifiers

`id=` on any block. Unique within document. `†id_namespace` for cross-document disambiguation.

### 2.9 Attribute Value Quoting

Values with spaces MUST be double-quoted. Escaping: `\"` for literal quote, `\\` for literal backslash, all other `\X` passes through unchanged. Values MUST NOT contain newlines; multiline content uses indented child blocks.

### 2.10 Custom Metadata Namespace (v1.0)

Publishers MAY include custom metadata fields in document headers and blocks. To prevent collisions with future CTX specification keywords, all custom or domain-specific metadata keys MUST be prefixed with `x-`:

```
§doc.ctx_v1.0 url=example.com/page †type=article †x-cms-id=992 †x-campaign=q3-push †x-internal-score=0.87
```

**Rules**:
- Custom keys: `†x-*` (e.g., `†x-cms-id`, `†x-tracking-ref`, `†x-team=engineering`)
- Parsers MUST preserve `x-` metadata in the parsed document structure
- Agents MAY safely ignore `x-` metadata that they don't understand
- The CTX specification will NEVER introduce an official key starting with `x-`
- Converters SHOULD pass through any existing custom metadata from source documents (HTML `data-*` attributes, custom meta tags, etc.) as `†x-*` fields

### 2.11 Commerce and Publisher Monetization

See Chapter 8.

---

## 3. Format Specification

### 3.1 Version Declaration

`§doc.ctx_v1.0` — MUST appear first. Parsers MUST reject unrecognized versions.

### 3.2 Document Header

```
§doc.ctx_v1.0 url=example.com/page title="Page Title" †date=2026-03-29 †type=article †lang=en †tokenizer-family=cl100k †id_namespace=example_42 †x-cms-id=4819
```

**Required**: version, `url`/`source`. **Recommended**: `title`, `†type`, `†tokenizer-family`. **Optional**: `†date`, `†lang`, `†author`, `†word_count`, `†hash`, `†original_etag`, `†continuation`, `†id_namespace`, `†x-*` (custom fields).

**Reserved metadata keys** (current and future CTX use): all keys NOT starting with `x-`. Publishers MUST use `†x-` prefix for custom keys.

### 3.3 Summary Block

At most one. Appears after header, before content.

### 3.4 Section Blocks

`§1`-`§4` with optional `id=` and optional `[skip]`.

### 3.5 Leaf Blocks

`§p` (paragraph — may contain `[refN]` citation pointers), `§code lang=X` (all literal), `§quote`, `§aside`.

### 3.6 Data Blocks (`∷`)

Close with `∷/`. Column type hints, strict encoding, pipe escaping, no leading/trailing pipes, JSON truncation safety, `†truncated=true`.

#### Empty Data Blocks (v1.0)

Converters SHOULD strip empty data blocks (zero rows/items) and empty semantic containers entirely to conserve tokens, unless the empty state itself carries critical semantic meaning (e.g., a search that returned zero results). When preserving an intentionally empty state, converters SHOULD add `†empty=true`:

```
∷ table cols=Name,Status †empty=true
∷/
```

Agents encountering `†empty=true` know the emptiness is intentional data (e.g., "no results"), not a conversion error.

### 3.7 Media References (`◆`)

Provenance: `†source=alt-text|caption|vlm:model|heuristic`. Optional `†confidence=0.0-1.0`.

### 3.8 Interactive Elements (`▸`)

`id=` RECOMMENDED. `purpose=` describes intent. `action=METHOD:/path`. `value=` for pre-filled state. `enctype=json|form|multipart` for submission encoding.

#### Form Submission Encoding

**Method-dependent serialization (v1.0)**:

For `POST`, `PUT`, and `PATCH` actions, agents serialize inputs according to the `enctype` attribute:

| `enctype` | MIME Type | Default? |
|-----------|-----------|----------|
| `json` | `application/json` | Yes (when omitted) |
| `form` | `application/x-www-form-urlencoded` | No |
| `multipart` | `multipart/form-data` | No (file uploads) |

**For `GET` and `DELETE` actions, agents MUST serialize input names and values as URL query parameters, regardless of `enctype`.** HTTP GET requests do not support request bodies — strict servers and WAFs will reject them.

```
# GET form → query parameters
▸ form.search id=form_search purpose="Product search"
  ▸ input.text id=inp_q name=query label="Search" value=headphones
  ▸ select id=sel_cat name=category label="Category" options=All,Electronics,Books value=All
  ▸ button.submit id=btn_search label="Search" action=GET:/api/search

# Agent sends: GET /api/search?query=headphones&category=All
```

```
# POST form → JSON body (default)
▸ form.profile id=form_profile purpose="Update profile" enctype=json
  ▸ input.text id=inp_name name=name label="Name" value="Jane Smith"
  ▸ button.submit id=btn_save label="Save" action=POST:/api/profile

# Agent sends: POST /api/profile
# Content-Type: application/json
# {"name": "Jane Smith"}
```

#### Multiline Input Values

`▸ input.textarea` uses indented child text for multiline content (same syntax as media fallbacks):

```
▸ input.textarea id=inp_bio name=bio label="Bio"
  First line of existing content.
  Second line of existing content.
```

### 3.9 Document References (`§ref`)

```
§ref id=ref1 url=example.com/source title="Source Article" †rel=source
§ref url=example.com/related title="Related Page" †rel=related
```

**Rules**:
- `§ref` blocks MAY carry `id=N` for inline citation matching (see 2.6)
- `§ref` blocks without `id=` are valid navigational metadata
- Conventionally placed at document end
- Never `[skip]`-annotated
- `†rel=` types: `continuation`, `source`, `data-source`, `related`, `parent`, `child`, `next`, `prev`, `spec`, `api`, `canonical`

### 3.10 Multi-Part Documents

`†continuation` in header + `§ref †rel=next`.

---

## 4. Escaping and Encoding

### 4.1 Delimiter Escaping

Reserved delimiters in body text doubled: `§§`=§, `††`=†, etc. Scope: leaf content and fallback text only.

### 4.2 Attribute Value Escaping

Inside quoted values: `\"` = literal quote, `\\` = literal backslash, all other `\X` = literal `\X`.

### 4.3 Underscore Disambiguation

`§code`: all literal. Prose: matched `_pairs_` = emphasis; `variable_name` = literal.

### 4.4 Encoding

UTF-8, no BOM, LF line endings.

---

## 5. Content Type Conversion Examples

### 5.1 Web Article with Inline Citations

```
§doc.ctx_v1.0 url=example.com/2026/03/28/ai-agents title="AI Agents Transform Browsing" †date=2026-03-28 †type=article †tokenizer-family=cl100k †x-section=technology

§summary tokens=85
  How AI agents are changing web browsing. Covers token economy,
  industry responses, and the case for standardized formats.

†commerce
  †paywall tier=premium
  †billing endpoint=https://example.com/api/agent-access
  †cost per_read=0.003 currency=USD

§nav [skip]
  Home | Tech | Business | Science

§content.article
  §1 AI Agents Are Transforming How We Browse
    §p The way humans interact with the internet is undergoing a
    fundamental shift. A recent study [ref1] found that AI agents now
    mediate over 30% of enterprise web interactions.

    §2 The Token Economy Problem
      §p Every page an agent reads costs tokens. The Jina Reader
      project [ref2] was among the first to address this with a
      dedicated content extraction API. Firecrawl [ref3] followed
      with a web scraping approach.

    §2 Promoted: AI Newsletter [skip]
      §p Subscribe to our weekly AI roundup...

    §2 Industry Response
      ∷ table cols=Project,Approach,Status
        Jina Reader  | Reader API         | Production
        Firecrawl    | Web scraping       | Production
        CTX          | Format standard    | v1.0 spec
      ∷/

§footer [skip]
  Copyright, privacy, terms

§ref id=ref1 url=example.com/agent-study title="Agent Adoption Study" †rel=source
§ref id=ref2 url=jina.ai/reader title="Jina Reader" †rel=related
§ref id=ref3 url=firecrawl.dev title="Firecrawl" †rel=related
```

### 5.2 E-Commerce Product

```
§doc.ctx_v1.0 url=shop.example.com/product/42 title="1960s Omega Seamaster" †type=product †id_namespace=shop_42 †x-sku=OMG-SEA-166002

§content.product
  §1 1960s Omega Seamaster Automatic — Ref. 166.002

  ∷ kv
    Price: 4800.00
    Condition: Excellent (serviced 2025)
    Year: circa 1965
  ∷/

  §p The Seamaster 166.002 represents Omega's mid-1960s aesthetic.
  See the complete buying guide [ref1] for authentication details.

  §2 Price History
    ∷ table cols=Date:date,Condition,Price:currency,Source
      2025-11-08 | Good       | 3900.00 | Chrono24
      2025-08-22 | Excellent  | 5200.00 | Auction
    ∷/

  ▸ button.action id=btn_cart label="Add to Cart" action=POST:/api/cart/add/42
  ▸ button.action id=btn_offer label="Make Offer" action=MODAL:offer-form

§ref id=ref1 url=shop.example.com/guide/seamaster title="Buying Guide" †rel=related
```

### 5.3 Search Form (GET Serialization)

```
§doc.ctx_v1.0 url=example.com/search title="Search" †type=application

§content.application
  §1 Product Search

  ▸ form.search id=form_search purpose="Find products"
    ▸ input.text id=inp_q name=query label="Search" placeholder="e.g. vintage watches"
    ▸ select id=sel_cat name=category label="Category" options=All,Watches,Jewelry,Accessories value=All
    ▸ select id=sel_sort name=sort label="Sort by" options=Relevance,Price,Date value=Relevance
    ▸ button.submit id=btn_search label="Search" action=GET:/api/search

  §p Agent submits as: GET /api/search?query=vintage+watches&category=All&sort=Relevance
```

### 5.4 Pre-Filled Form with Textarea

```
§doc.ctx_v1.0 url=app.example.com/settings title="Account Settings" †type=application

§content.application
  §1 Account Settings

  ▸ form.settings id=form_settings purpose="Update preferences" enctype=json
    ▸ input.text id=inp_name name=display_name label="Display Name" value="Jane Smith"
    ▸ input.email id=inp_email name=email label="Email" value="jane@example.com"
    ▸ input.checkbox id=chk_dark name=dark_mode label="Dark mode" value=true
    ▸ input.textarea id=inp_bio name=bio label="Bio"
      Software engineer focused on distributed systems
      and ML infrastructure.
    ▸ button.submit id=btn_save label="Save Changes" action=POST:/api/settings
```

### 5.5 Empty Search Results (v1.0)

```
§doc.ctx_v1.0 url=example.com/search?q=xyzzy title="Search Results" †type=application

§content.application
  §1 Search Results for "xyzzy"

  ∷ table cols=Name,Price:currency,Status †empty=true
  ∷/

  §p No products matched your search. Try broadening your query.
```

### 5.6 Delta Response

```
§delta action=POST:/api/cart/add/42 †status=success †original_url=shop.example.com/product/42

§toast message="Item added to cart" †duration=transient

§update target=#btn_cart
  ▸ button.action id=btn_cart label="In Cart (1)" action=GET:/cart †state=disabled
```

### 5.7 Auth Challenge

```
§doc.ctx_v1.0 url=private.example.com/dashboard †type=error

§error type=auth-required
  †http_status=401
  †detail=Authentication required.

§auth-challenge
  †method=bearer
  †token_endpoint=https://private.example.com/oauth/token
  †scopes=read:dashboard
```

---

## 6. Token Efficiency Analysis

### 6.1 Theoretical (Single Article)

| Format | Tokens | % of HTML |
|--------|--------|-----------|
| Raw HTML | ~45,000 | 100% |
| Markdown | ~4,500 | 10% |
| **CTX** | **~3,400** | **7.5%** |

Inline citations add ~25 tokens for 10 links — far less than Markdown's 40+ tokens for the same links, and they preserve spatial context.

### 6.2 Measured (4-Page Benchmark)

Tested with real pages using the reference implementation (`fast` tier, DOM rules only):

| Page | Raw HTML | CTX | Byte Reduction | ~HTML Tokens | ~CTX Tokens | Token Savings |
|------|----------|-----|----------------|--------------|-------------|---------------|
| example.com | 528 B | 354 B | 33.0% | ~165 | ~88 | 46.4% |
| Wikipedia: Python (PL) | 620,681 B | 90,043 B | 85.5% | ~193,962 | ~22,510 | 88.4% |
| Wikipedia: Shohei Ohtani | 1,180,170 B | 150,152 B | 87.3% | ~368,803 | ~37,538 | 89.8% |
| Wikipedia: Transformer (DL) | 713,491 B | 138,443 B | 80.6% | ~222,965 | ~34,610 | 84.5% |

Token estimates use conservative ratios: ~3.2 chars/token for HTML (tag-heavy), ~4.0 chars/token for CTX (natural language).

**Aggregate**: 2,514,870 bytes HTML → 378,992 bytes CTX (**84.9% byte reduction**, **~87.9% token savings**).

### 6.3 Measured (100-Site Test)

Tested across 100 real-world websites in 10 categories using the `fast` extraction tier:

| Category | Sites | Pass Rate | Avg Byte Reduction |
|----------|-------|-----------|-------------------|
| marketing | 10 | 100% | 99.5% |
| tech | 10 | 100% | 95.5% |
| government | 10 | 90% | 97.9% |
| news | 10 | 90% | 96.2% |
| sports | 10 | 90% | 90.7% |
| finance | 10 | 80% | 95.4% |
| search | 10 | 80% | 92.5% |
| ecommerce | 10 | 70% | 79.6% |
| entertainment | 10 | 70% | 99.6% |
| edge cases | 10 | 40% | 62.4% |

Overall: 81 pass, 13 partial, 4 fail, 2 timeout. High-reduction categories (news, entertainment, marketing, sports) benefit most because their HTML is dominated by navigation, ads, and scripts that CTX strips entirely. Lower-reduction categories (edge cases, ecommerce) contain minimal-markup pages or heavy client-side rendering.

### 6.4 Cost Projections

At $3/M input tokens (Claude Sonnet 4 pricing):

| Scenario | HTML Cost | CTX Cost | Saved |
|----------|-----------|----------|-------|
| Single Wikipedia article (Ohtani) | $1.11 | $0.11 | $0.99 |
| 50 pages/hour agent workload | $55.28/hr | $6.69/hr | **$48.59/hr** |
| 1,000 pages/day research batch | $1,105.65 | $133.72 | **$971.93** |

---

## 7. HTTP Content Negotiation

```http
GET /article HTTP/1.1
Accept: text/ctx
X-Agent-Context-Window: 128000
X-Agent-Tokenizer: cl100k
X-Agent-Depth: full
```

MIME type: `text/ctx`. Extension: `.ctx`.

---

## 8. Commerce and Publisher Monetization

`†commerce` declares billing endpoints. HTTP 402 flow. Absent = unrestricted.

---

## 9. Authentication Challenge

`§auth-challenge †method=bearer|basic|api-key|form`. Auth resolves 401, commerce resolves 402.

---

## 10. Interaction Responses and State Deltas

**Two payload types**: Document (`§doc...`) or Delta (`§delta...`). Never mixed. Selectors: `#id` (preferred) or `type.path`.

---

## 11. Converter Architecture

### 11.1 Pipeline

Source → Fetch → Extract → Classify → Annotate → Normalize → Escape → Compress → CTX

The **Annotate** stage now includes: inline citation pointer generation from `<a>` tags in body content.

The **Normalize** stage: data encoding, boolean normalization, pipe stripping, empty block removal.

### 11.2 Boolean Normalization

`true/yes/y/1/on/✅` → `true`. `false/no/n/0/off/❌/empty` → `false`. Ambiguous → `false` + `†note=ambiguous-bool`.

### 11.3 Citation Generation

When the converter encounters an `<a href="...">` tag inside article body text (within `<p>`, `<li>`, etc.):
1. Assign a sequential citation ID (ref1, ref2, ref3...)
2. Replace the `<a>` tag with the anchor text followed by `[refN]` in the `§p` output
3. Emit a `§ref id=refN url=... †rel=related` block at the document end

Links in `<nav>`, `<footer>`, `<aside>`, `<header>`, and other non-content zones are NOT converted to citations — they become `[skip]` blocks or are dropped entirely.

### 11.4 Empty Block Stripping

Converters SHOULD strip empty data blocks and empty containers to save tokens. Exception: preserve with `†empty=true` when the empty state is semantically meaningful (search with zero results, form with no options, etc.).

### 11.5 Extraction Flattening

`▸ form` blocks should contain only inputs and buttons. Non-input content extracted as sibling blocks.

### 11.6 Extraction Tiers

| Tier | Method | Speed | AI Required |
|------|--------|-------|-------------|
| `fast` | DOM rules | <100ms | No |
| `smart` | Rules + NER | <1s | No (default) |
| `full` | Rules + NER + LLM/VLM | 2-5s | Yes |

---

## 12. Error Handling

`§error type=` with types: `extraction-failed`, `fetch-failed`, `auth-required`, `format-unsupported`, `truncated`, `vision-failed`. Partial error documents allowed.

---

## 13. Security Considerations

1. Converters escape delimiters; frameworks sandbox CTX as DATA; reject multiple `§doc` headers
2. Validate URLs, HTTPS, reject `javascript:` URIs
3. Don't auto-submit from untrusted sources; verify action domains
4. HTTPS for billing/token endpoints; spending limits

---

## 14. Format Comparison

| | HTML | Markdown | XML | JSON | CTX v1.0 |
|---|---|---|---|---|---|
| **Token efficiency** | Poor | Good | Fair | Fair | Best |
| **Structure** | High | Low | Excellent | Schema | Excellent |
| **Inline citations** | Full | Full | Possible | None | Native [refN] |
| **Multimodal** | Full | Text-only | Possible | Possible | Native |
| **Commerce** | Ads | None | None | None | Native |
| **Auth** | Cookies | None | None | None | Native |
| **Form state** | Full | None | Full | None | Native |
| **Custom metadata** | data-* | None | Namespace | Any key | †x-* |
| **Error handling** | HTTP | None | Schema | Schema | Native |

---

## 15. Competitive Landscape

Chapter 14 compares CTX against data formats (HTML, Markdown, XML, JSON). This chapter compares CTX against existing **tools and services** that convert web content for AI consumption.

| | Jina Reader | Firecrawl | Crawl4AI | Trafilatura | CTX v1.0 |
|---|---|---|---|---|---|
| **Output format** | Markdown | Markdown/JSON | Markdown | Markdown/JSON/XML | CTX |
| **Token efficiency vs HTML** | ~90% | ~90% | ~90% | ~67% | ~92% |
| **Inline citations** | `[text](url)` 4+ tok/link | `[text](url)` | `[text](url)` | None | `[refN]` 2-3 tok/link |
| **Semantic content typing** | None | None | None | None | `§content.article/product/...` |
| **Skip annotations** | Content stripped entirely | Stripped | Filter-based | Stripped | `§nav [skip]` — preserved |
| **Interactive elements** | Dropped | `/interact` endpoint | Dropped | Dropped | Native `▸ form/button` |
| **Commerce/Auth** | Not addressed | Not addressed | Not addressed | Not addressed | Native `†commerce`, `§auth-challenge` |
| **Formal spec** | No | No | No | No | EBNF grammar, versioned |
| **Self-hosted** | Cloud API | Cloud + self-host | Self-host | Self-host | Self-host |
| **Approach** | Extraction tool | Scraping platform | Crawler framework | Extraction library | Format specification |

**Key differentiators**: CTX is a format specification, not a tool — it defines how content should be structured for LLMs, regardless of the extraction pipeline. Existing tools focus on extraction (getting content out of HTML) but output to general-purpose formats (Markdown, JSON) that were not designed for transformer consumption. CTX addresses the output format itself: single-token delimiters, semantic typing, skip annotations that preserve structure without wasting tokens, and native support for commerce, auth, and interactive elements that other tools either drop or handle out-of-band.

---

## 16. Canonical Parsing Algorithm

### 16.1 Attribute Tokenization

Quoted values terminate at unescaped `"`. Unquoted terminate at space. `\"` → `"`, `\\` → `\`, other `\X` → `\X`.

### 16.2 Citation Pointer Parsing

Citation pointers `[refN]` in `§p` text are plain text. Parsers MAY extract them for cross-referencing with `§ref id=refN` blocks but are not required to — the LLM will naturally associate `[ref1]` in prose with `§ref id=ref1` at the document end.

### 16.3 Textarea Value Extraction

Read indented lines until indent returns to parent level. Blank lines preserved.

### 16.4 GET vs POST Serialization

```
function build_request(form, action):
    method, path = action.split(":", 1)

    if method in ("GET", "DELETE"):
        params = urlencode({input.name: input.value for input in form.inputs})
        return Request(method, path + "?" + params)

    else:  // POST, PUT, PATCH
        enctype = form.enctype or "json"
        if enctype == "json":
            body = json({input.name: input.value for input in form.inputs})
            return Request(method, path, body, "application/json")
        elif enctype == "form":
            body = urlencode({input.name: input.value for input in form.inputs})
            return Request(method, path, body, "application/x-www-form-urlencoded")
        elif enctype == "multipart":
            body = multipart({input.name: input.value for input in form.inputs})
            return Request(method, path, body, "multipart/form-data")
```

### 16.5 Key Subroutines

Hierarchy: depth markers canonical. Escaping: `§§→§`, `\"→"`, `\\→\`. Column types: split commas, split `:`, default `string`. JSON repair: close brackets, trim commas. Table rows: strip leading/trailing pipes. Skip: sections with `[skip]` strip subtree. Empty blocks: strip unless `†empty=true`.

---

## 17. Formal Grammar (EBNF)

```ebnf
(* CTX v1.0 EBNF Grammar *)

payload         = document | delta_response ;

(* === Document === *)

document        = doc_header NL
                  [ summary ]
                  [ commerce ]
                  [ auth_challenge ]
                  { doc_block }
                  { ref } ;

doc_header      = "§doc.ctx_v" version { " " field } ;
version         = DIGIT "." DIGIT ;
field           = key "=" attr_value | "†" key "=" attr_value ;

summary         = "§summary" { " " attr } NL indented_text ;
commerce        = "†commerce" NL { "  †" key { " " attr_value } NL } ;
auth_challenge  = "§auth-challenge" NL { "  †" key "=" attr_value NL } ;

doc_block       = container | section | leaf | data_block | media_block
                | interactive_block | skip_block | error_block ;

container       = "§content." type_name NL { indented_doc_block } ;

skip_block      = "§" skip_type " [skip]" [ NL indented_text ] ;
skip_type       = "nav" | "sidebar" | "footer" | "ad" | "auth" | "cookie" ;

section         = indent "§" depth " " text [ " " id_attr ] [ " [skip]" ]
                  NL { indented_doc_block } ;
depth           = "1" | "2" | "3" | "4" ;

leaf            = indent leaf_prefix " " text NL ;
leaf_prefix     = "§p" | "§quote" | "§aside"
                | "§code" [ " lang=" IDENT ] ;

(* Note: [refN] citation pointers in §p text are plain text, not structural *)

data_block      = indent data_open NL
                  { indent data_line NL }
                  indent data_close ;
data_open       = ( "∷" | "::" ) " " data_type { " " data_attr } ;
data_close      = "∷/" | "::/" ;
data_type       = "table" | "json" | "list" | "kv" ;

data_attr       = "cols=" typed_cols
                | key "=" attr_value
                | id_attr ;

typed_cols      = col_def { "," col_def } ;
col_def         = IDENT [ ":" type_hint ] ;
type_hint       = "string" | "int" | "float" | "bool"
                | "date" | "datetime" | "url" | "currency" ;

data_line       = ? text with \| for literal pipes ;
                    leading/trailing unescaped pipes stripped ? ;

media_block     = indent ( "◆" | "<>" ) " " media_type
                  { " " attr } NL
                  { indent "  " text NL } ;
media_type      = "image" | "video" | "audio" | "chart" | "attachment" ;

interactive_block = indent ( "▸" | ">>" ) " " interactive_type
                    { " " attr } NL
                    [ indented_text ]
                    { indented_interactive } ;
interactive_type  = IDENT [ "." IDENT ] ;
indented_interactive = indent "  " interactive_block ;

ref             = "§ref" { " " attr } ;

error_block     = "§error type=" error_type NL
                  { "  †" key "=" attr_value NL } ;
error_type      = "extraction-failed" | "fetch-failed" | "auth-required"
                | "format-unsupported" | "truncated" | "vision-failed" ;


(* === Delta Response === *)

delta_response  = delta_header NL
                  { toast_block | update_block } ;

delta_header    = "§delta" { " " attr } ;
toast_block     = "§toast" { " " attr } NL ;
update_block    = "§update target=" target_selector NL
                  { indented_doc_block } ;

target_selector = "#" IDENT
                | IDENT { "." IDENT } ;


(* === Shared Primitives === *)

attr            = key "=" attr_value | id_attr ;
id_attr         = "id=" IDENT ;
key             = IDENT | "x-" IDENT ;

attr_value      = quoted_value | unquoted_value ;
quoted_value    = '"' { QCHAR } '"' ;
QCHAR           = ? any char except newline or unescaped " ;
                    \" = literal quote ;
                    \\ = literal backslash ;
                    all other \X = literal \X ? ;
unquoted_value  = { ? any char except space or newline ? } ;

text            = { TEXT_CHAR } ;
TEXT_CHAR       = ? any char except newline ;
                    reserved delimiters doubled for escaping ? ;

IDENT           = LETTER { LETTER | DIGIT | "_" | "-" | "." } ;
type_name       = IDENT { "." IDENT } ;
indent          = { "  " } ;
indented_text   = { indent "  " text NL } ;
indented_doc_block = indent "  " doc_block ;
NL              = "\n" ;
DIGIT           = "0"-"9" ;
LETTER          = "a"-"z" | "A"-"Z" ;
```

---

## 18. Reference Implementation Roadmap

### Phase 1 — Completed (March 2026)

- Python `ctx` package: converter pipeline, parser, emitter, CLI tools, HTTP service
- Tested across 100 real-world websites: 81% pass, 13% partial, 4% fail, 2% timeout (see Chapter 22)
- Three extraction tiers: `fast` (DOM rules, <100ms), `smart` (DOM + NER, <1s), `full` (DOM + NER + VLM, 2-5s)
- FastAPI service on port 8200 with Redis caching, transparent proxy mode
- Memory stable at 172 MB regardless of conversion volume

### Phase 2 — In Progress

- `ctx-convert` CLI and `ctx-parse` CLI (done)
- Browser extension, editor extensions (planned)
- Systemd service deployment (ready)

### Phase 3 — Planned

- Agent framework integrations (LangChain, CrewAI, OpenAI Agents SDK)
- Publisher SDKs
- IETF Internet-Draft
- Head-to-head benchmarks vs Jina Reader, Firecrawl, Trafilatura

### CTX Compliance

Test suite covers: attribute quoting, backslash escaping, citation pointer generation and matching, GET query serialization, POST JSON body, textarea extraction, empty block handling, `x-` metadata passthrough, leading/trailing pipe stripping, section-level skip, data normalization, JSON repair, document/delta separation.

---

## 19. Internationalization

UTF-8 only. All Unicode scripts valid. LF line endings.

---

## 20. Governance and Extensibility

### 20.1 Core Grammar Freeze

As of v1.0, the core grammar (delimiters, block types, depth markers, attribute syntax, escaping rules, payload types) is frozen. Future versions (v1.1, v1.2) MAY add new block types or attributes but MUST NOT change the syntax of existing ones.

### 20.2 Content Type Registry

The Fox Valley AI Foundation maintains a living registry of `§content.*` subtypes in the `registry/` directory of the reference repository (github.com/mtecnic/ctx). Community members may propose new subtypes via pull request. Subtypes in the registry are documented but not mandated — parsers MUST treat any unknown subtype as `§content.reference`.

### 20.3 Custom Metadata

Publishers use `†x-*` for domain-specific metadata (see 2.10). The `x-` namespace is permanently reserved for custom use and will never conflict with official CTX keys.

### 20.4 Versioning Policy

- **Patch versions** (v1.0.1): Clarifications, typo fixes, additional examples. No grammar changes.
- **Minor versions** (v1.1, v1.2): New optional block types, new attributes, new `†rel` values. Backward-compatible — a v1.0 parser can read v1.1 documents (ignoring unknown blocks).
- **Major versions** (v2.0): Breaking grammar changes. Major versions require a new parser.

---

## 21. Changelog

### v1.0-rc2 (March 2026)
- Reference implementation completed and tested across 100 real-world sites (81% pass, 13% partial, 4% fail, 2% timeout)
- Added competitive landscape comparison (vs Jina Reader, Firecrawl, Crawl4AI, Trafilatura) — Chapter 15
- Updated token efficiency analysis with real benchmark data (4-page benchmark + 100-site category breakdown) — Chapter 6
- Updated implementation roadmap to reflect completed Phase 1 — Chapter 18
- Added 100-site test results summary — Chapter 22

### v1.0-rc1 (March 2026)
- Added inline citation pointers: `[refN]` in body text mapped to `§ref id=refN` blocks (preserves spatial link context without Markdown syntax)
- Added custom metadata namespace: `†x-*` prefix for publisher/domain-specific keys (prevents future collisions)
- Added GET vs POST serialization rule: GET/DELETE use query parameters, POST/PUT/PATCH use body with enctype
- Added empty data block guidance: strip by default, preserve with `†empty=true` when semantically meaningful
- Added Chapter 20: Governance and Extensibility (grammar freeze, content type registry, versioning policy)
- Updated EBNF: `key` production now includes `"x-" IDENT` for custom metadata
- Updated `§ref` to support `id=N` for citation matching
- Added citation generation algorithm to converter pipeline
- Added web article example with inline citations
- Added search form example demonstrating GET serialization
- Added empty search results example
- Renamed Open Questions to Governance; all prior open questions either resolved or deferred to registry process

### v0.9 (March 2026)
- Textarea multiline values, backslash escaping, form enctype, extraction flattening

### v0.8 (March 2026)
- Quoted attributes, form value=, section-level [skip], table row pipe stripping

### v0.7 (March 2026)
- Grammar root fork (document vs delta), cols= binding, boolean normalization

### v0.6 (March 2026)
- Auth challenge, strict data encoding, JSON truncation, †id_namespace

### v0.5 (March 2026)
- Block identifiers, column type hints

### v0.4 (March 2026)
- Escaping, error handling, security, EBNF, §summary, media provenance

### v0.3 (March 2026)
- Vendor-neutral rewrite, container exemption

### v0.2 (March 2026)
- Depth markers, inline annotations, †commerce, §ref

### v0.1 (March 2026)
- Initial draft

---

## 22. 100-Site Test Results

The reference implementation was tested against 100 real-world websites across 10 categories using the `fast` extraction tier (DOM rules only, no AI). Full results are in `tests/REPORT_100.md`.

### Overall

| Status | Count | % |
|--------|-------|---|
| Pass | 81 | 81% |
| Partial | 13 | 13% |
| Fail | 4 | 4% |
| Error (timeout) | 2 | 2% |

### Pass Rate by Category

| Category | Pass | Partial | Fail | Error | Avg Byte Reduction |
|----------|------|---------|------|-------|--------------------|
| marketing | 10 | 0 | 0 | 0 | 99.5% |
| tech | 10 | 0 | 0 | 0 | 95.5% |
| government | 9 | 1 | 0 | 0 | 97.9% |
| news | 9 | 0 | 0 | 1 | 96.2% |
| sports | 9 | 1 | 0 | 0 | 90.7% |
| finance | 8 | 1 | 1 | 0 | 95.4% |
| search | 8 | 2 | 0 | 0 | 92.5% |
| ecommerce | 7 | 2 | 0 | 1 | 79.6% |
| entertainment | 7 | 2 | 1 | 0 | 99.6% |
| edge cases | 4 | 4 | 2 | 0 | 62.4% |

### Iteration History

Testing progressed through three rounds of implementation fixes:

| Round | Pass Rate | Key Fixes |
|-------|-----------|-----------|
| 1 | 67% | Initial converter pipeline |
| 2 | 80% | Skip block deduplication, SPA fallback, content-type validation |
| 3 | 81% | Citation breadth (beyond `<p>` tags), title fallback heuristics |

### Top Issues Found

- **no_refs** (77 sites): Most sites use `<a>` tags outside `<p>` containers — citation generation needs broader link detection
- **too_many_skip** (53 sites): Heavy-nav sites generate many skip blocks — cap at 5, merge duplicates
- **low_reduction** (10 sites): Minimal-markup pages or text-heavy content where HTML is already close to plain text
- **SPA rendering**: Client-side-rendered sites (IMDb, Google Finance) return empty content with DOM-only extraction

### Memory Profile

Stable at 172 MB under sustained load, zero growth across 100 consecutive conversions. The converter pipeline processes and discards each page without accumulating state.

---

## License

This specification is released under **CC BY 4.0**. The reference implementation is licensed under the **Apache License 2.0**.

**Fox Valley AI Foundation** — foxfoundation.ai | github.com/mtecnic/ctx