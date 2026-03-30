# ctx

Reference implementation of the [CTX (Context Transfer Format)](specification.md) — a universal interchange format optimized for LLM consumption. Converts HTML web pages into token-efficient structured documents that preserve content, citations, and hierarchy while stripping everything an LLM doesn't need.

A typical Wikipedia article drops from **1.2 MB of raw HTML to 150 KB of CTX** — an **87% reduction** in bytes, **~90% fewer tokens**.

```
§doc.ctx_v1.0 url=en.wikipedia.org/wiki/Shohei_Ohtani title="Shohei Ohtani - Wikipedia" †type=article †lang=en

§nav [skip]
  Main menu...

§content.article
  §p _Shohei Ohtani_ (born July 5, 1994) is a Japanese professional
  baseball [ref1] designated hitter [ref2] and pitcher [ref3] for the
  Los Angeles Dodgers [ref4] of Major League Baseball [ref5] (MLB)...

  §2 Early life
    §p Ohtani was born on July 5, 1994, in Mizusawa...
  §2 Professional career
    §3 Los Angeles Dodgers (2024-present)
      §4 2024: 50-50 season, World Series champion
        §p ...

§ref id=ref1 url=en.wikipedia.org/wiki/Baseball title=baseball †rel=related
§ref id=ref2 url=en.wikipedia.org/wiki/Designated_hitter title="designated hitter" †rel=related
```

## Install

```bash
# Clone and set up
git clone https://github.com/foxvalleyai/ctx.git
cd ctx
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

Requires Python 3.12+. Tested on Python 3.14.

## Quick Start

### CLI

```bash
# Convert a URL to CTX
ctx-convert https://example.com/article

# Convert with tier selection
ctx-convert https://en.wikipedia.org/wiki/Python --tier fast

# Convert a local HTML file
ctx-convert ./page.html --source-url https://example.com/page

# Pipe mode
curl -s https://example.com | ctx-convert --stdin

# Save to file
ctx-convert https://example.com -o article.ctx

# ASCII fallback delimiters (for systems that don't handle Unicode well)
ctx-convert https://example.com --target ascii
```

```bash
# Validate a CTX file
ctx-parse article.ctx --validate

# Parse to JSON
ctx-parse article.ctx --json

# Show document tree
ctx-parse article.ctx --tree

# Extract references only
ctx-parse article.ctx --refs
```

### Python Library

```python
import asyncio
from ctx.converter.pipeline import convert

async def main():
    # Convert a URL
    ctx_text = await convert("https://example.com/article", tier="smart")
    print(ctx_text)

    # Convert raw HTML
    ctx_text = await convert(
        "<html><body><h1>Hello</h1><p>World</p></body></html>",
        source_url="https://example.com",
    )

asyncio.run(main())
```

```python
from ctx.parser import parse
from ctx.emitter import emit

# Parse CTX text into a structured document
doc = parse(ctx_text)
print(doc.header.attributes["title"])
print(len(doc.refs))

# Emit back to CTX text
roundtripped = emit(doc)
```

### HTTP Service

```bash
# Start the service
uvicorn ctx.service.app:app --host 0.0.0.0 --port 8200

# Or with multiple workers
uvicorn ctx.service.app:app --host 0.0.0.0 --port 8200 --workers 4
```

**Endpoints:**

```bash
# Health check
curl localhost:8200/health

# Convert via GET
curl "localhost:8200/convert?url=https://example.com&tier=fast"

# Convert via POST (URL)
curl -X POST localhost:8200/convert \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://example.com/article"}'

# Convert via POST (raw HTML)
curl -X POST localhost:8200/convert \
  -H 'Content-Type: application/json' \
  -d '{"html": "<html>...</html>", "source_url": "https://example.com"}'

# Transparent proxy — fetch and convert in one step
curl "localhost:8200/proxy/en.wikipedia.org/wiki/Large_language_model"

# Parse CTX to JSON
curl -X POST localhost:8200/parse \
  -H 'Content-Type: text/ctx' \
  -d '§doc.ctx_v1.0 url=example.com ...'

# Cache stats (requires Redis)
curl localhost:8200/cache/stats
```

**Query parameters** (on `/convert` and `/proxy`):

| Param        | Values                    | Default   |
|--------------|---------------------------|-----------|
| `tier`       | `fast`, `smart`, `full`   | `smart`   |
| `target`     | `unicode`, `ascii`        | `unicode` |
| `strip_skip` | `true`, `false`           | `true`    |

**Response headers:**

| Header         | Value        | Description              |
|----------------|--------------|--------------------------|
| `Content-Type` | `text/ctx`   | CTX MIME type            |
| `X-CTX-Cache`  | `hit`/`miss` | Redis cache status       |

## Extraction Tiers

| Tier     | Method                | Speed    | AI Required | Use Case                               |
|----------|-----------------------|----------|-------------|----------------------------------------|
| `fast`   | DOM rules only        | <500ms   | No          | Bulk conversion, low latency           |
| `smart`  | DOM + regex NER       | <1s      | No          | Default — good balance of quality/speed|
| `full`   | DOM + NER + VLM       | 2-5s     | Yes         | Rich pages with images, charts         |

The `full` tier sends images to a local VLM (e.g., Qwen3-VL on vLLM) for alt-text generation when existing descriptions are missing or generic. Configure with `CTX_VLLM_URL`.

## Configuration

Environment variables:

| Variable            | Default                       | Description                    |
|---------------------|-------------------------------|--------------------------------|
| `CTX_PORT`          | `8200`                        | Service port                   |
| `CTX_HOST`          | `0.0.0.0`                     | Bind address                   |
| `CTX_REDIS_URL`     | `redis://localhost:6379/1`    | Redis URL for caching          |
| `CTX_VLLM_URL`      | `http://localhost:8000/v1`    | vLLM API for `full` tier       |
| `CTX_DEFAULT_TIER`  | `smart`                       | Default extraction tier        |
| `CTX_CACHE_TTL`     | `3600`                        | Cache TTL in seconds (1h)      |
| `CTX_CACHE_TTL_FULL`| `14400`                       | Cache TTL for `full` tier (4h) |

Redis is optional — the service runs without it (no caching).

## Converter Pipeline

The HTML-to-CTX pipeline implements [Chapter 11](specification.md#11-converter-architecture) of the spec:

```
Source → Fetch → Extract → Classify → Annotate → Normalize → Emit → CTX
```

| Stage         | Module                    | What It Does                                              |
|---------------|---------------------------|-----------------------------------------------------------|
| **Fetch**     | `converter/fetcher.py`    | Async HTTP with `Accept: text/ctx` content negotiation    |
| **Extract**   | `converter/extractor.py`  | readability-lxml + BeautifulSoup DOM traversal            |
| **Classify**  | `converter/classifier.py` | Score-based detection: article, product, application, etc |
| **Annotate**  | `converter/annotator.py`  | `[refN]` citation generation, `[skip]` blocks, section nesting |
| **Normalize** | `converter/normalizer.py` | Boolean normalization, empty block stripping              |
| **Emit**      | `emitter.py`              | CTXDocument model → spec-compliant `.ctx` text            |

**Citation generation**: Inline `<a>` tags in article body paragraphs become `text [refN]` pointers with corresponding `§ref id=refN url=... †rel=related` blocks at the document end. Links in nav, footer, and sidebar are NOT converted to citations.

**Skip annotation**: `<nav>`, `<footer>`, `<aside>`, and ad containers become `§nav [skip]`, `§footer [skip]`, etc. Content is truncated to save tokens.

**Section nesting**: `<h1>`-`<h4>` map to `§1`-`§4` with proper parent-child hierarchy.

## Project Structure

```
ctx/
├── specification.md              # CTX v1.0 format specification
├── TESTING.md                    # Benchmark results and visual comparisons
├── README.md
├── pyproject.toml
├── src/ctx/
│   ├── __init__.py
│   ├── grammar.py                # Delimiter constants, type registries
│   ├── models.py                 # Pydantic: CTXDocument, CTXBlock, CTXDelta
│   ├── escaping.py               # §§→§, attribute quoting (spec ch.4)
│   ├── parser.py                 # .ctx → CTXDocument (spec ch.15-16)
│   ├── emitter.py                # CTXDocument → .ctx text
│   ├── converter/
│   │   ├── pipeline.py           # Pipeline orchestrator
│   │   ├── fetcher.py            # Async URL fetching
│   │   ├── extractor.py          # HTML content extraction
│   │   ├── classifier.py         # Content type detection
│   │   ├── annotator.py          # Citations, skip blocks, section tree
│   │   ├── normalizer.py         # Boolean/whitespace normalization
│   │   └── tiers.py              # fast/smart/full tier dispatch
│   ├── service/
│   │   ├── app.py                # FastAPI application
│   │   ├── routes.py             # API endpoints
│   │   └── config.py             # Environment config
│   └── cli/
│       ├── convert.py            # ctx-convert command
│       └── parse.py              # ctx-parse command
└── tests/
    └── fixtures/
```

## Deployment

### systemd (recommended for always-on)

```ini
# ~/.config/systemd/user/ctx-service.service
[Unit]
Description=CTX Converter Service
After=network-online.target

[Service]
ExecStart=/path/to/ctx/venv/bin/uvicorn ctx.service.app:app --host 0.0.0.0 --port 8200 --workers 2
WorkingDirectory=/path/to/ctx
Restart=always
RestartSec=5
Environment=CTX_REDIS_URL=redis://localhost:6379/1
Environment=CTX_VLLM_URL=http://localhost:8000/v1

[Install]
WantedBy=default.target
```

```bash
systemctl --user enable --now ctx-service.service
systemctl --user status ctx-service
journalctl --user -u ctx-service -f
```

### Docker

```dockerfile
FROM python:3.14-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .
EXPOSE 8200
CMD ["uvicorn", "ctx.service.app:app", "--host", "0.0.0.0", "--port", "8200", "--workers", "2"]
```

## Benchmarks

Tested against real-world pages using the `fast` extraction tier:

| Page                        | Raw HTML    | CTX         | Reduction | ~Token Savings |
|-----------------------------|-------------|-------------|-----------|----------------|
| example.com                 | 528 B       | 354 B       | 33%       | ~46%           |
| Wikipedia: Python (PL)      | 620 KB      | 90 KB       | 85%       | ~88%           |
| Wikipedia: Shohei Ohtani    | 1,180 KB    | 150 KB      | 87%       | ~90%           |
| Wikipedia: Transformer (DL) | 713 KB      | 138 KB      | 81%       | ~85%           |

See [TESTING.md](TESTING.md) for the full report with visual comparisons and cost projections.

## Specification

The CTX format specification is at [specification.md](specification.md). Key sections for implementers:

- **Chapter 3** — Format specification (block types, attributes)
- **Chapter 4** — Escaping rules
- **Chapter 11** — Converter pipeline architecture
- **Chapter 15** — Canonical parsing algorithm
- **Chapter 16** — Formal EBNF grammar

## License

This implementation is released under the **Apache License 2.0**. The CTX specification is released under **CC BY 4.0**.

---

**Fox Valley AI Foundation** — [foxfoundation.ai](https://foxfoundation.ai) | [github.com/foxvalleyai/ctx-spec](https://github.com/foxvalleyai/ctx-spec)
