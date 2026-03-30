# Copyright 2026 Fox Valley AI Foundation
# SPDX-License-Identifier: Apache-2.0

"""CTX converter pipeline orchestrator.

Source → Fetch → Extract → Classify → Annotate → Normalize → Emit → CTX
"""

from __future__ import annotations

from ..emitter import emit
from ..grammar import CTX_VERSION
from ..models import CTXBlock, CTXDocument
from . import annotator, classifier, normalizer
from .extractor import ExtractionResult, extract
from .fetcher import FetchResult, fetch
from .tiers import apply_full_tier, apply_smart_tier


async def convert(
    source: str,
    *,
    tier: str = "smart",
    target: str = "unicode",
    strip_skip: bool = True,
    vllm_url: str = "http://localhost:8000/v1",
    source_url: str = "",
) -> str:
    """Convert a URL or raw HTML to CTX format.

    Returns CTX-formatted text. On fetch/extraction errors, returns a
    CTX document with §error blocks instead of raising.
    """
    # 1. Fetch (if URL) or use raw HTML
    is_url = source.startswith(("http://", "https://", "//")) or (
        "." in source.split("/")[0] and "<" not in source[:50]
    )

    if is_url:
        fetch_result = await fetch(source)
        html = fetch_result.html
        url = fetch_result.url

        # Handle fetch errors — still produce a CTX document with §error
        if fetch_result.error and not html:
            return _emit_error_doc(url, "fetch-failed", fetch_result.error)

        # For HTTP errors with content (e.g. 403 with a body), try to extract
        if fetch_result.error and html:
            # Try extraction, but note the error
            pass
    else:
        html = source
        url = source_url or "local"
        fetch_result = None

    # 2. Extract
    try:
        result: ExtractionResult = extract(html, url=url, tier=tier)
    except Exception as e:
        return _emit_error_doc(url, "extraction-failed", str(e))

    # 3. Apply tier-specific enhancements
    try:
        if tier in ("smart", "full"):
            apply_smart_tier(result)
        if tier == "full":
            await apply_full_tier(result, vllm_url=vllm_url)
    except Exception:
        pass  # Tier enhancements are optional, don't fail

    # 4. Classify
    content_type = classifier.classify(result)

    # 5. Annotate (citations, skip blocks, section tree)
    blocks = annotator.annotate(result, content_type)
    blocks = annotator.build_section_tree(blocks)

    # 6. Separate block types
    skip_blocks = [b for b in blocks if b.block_type == "skip"]
    content_blocks = [b for b in blocks if b.block_type == "content"]
    ref_blocks = [b for b in blocks if b.block_type == "ref"]

    # 7. Normalize
    content_blocks = normalizer.normalize_blocks(content_blocks)

    # 8. Strip skip content if requested
    if strip_skip:
        for b in skip_blocks:
            b.text = b.text[:80] + ("..." if len(b.text) > 80 else "") if b.text else ""

    # 9. Build document model
    header_attrs: dict[str, str] = {"version": CTX_VERSION, "url": url}
    if result.title:
        header_attrs["title"] = result.title
    if result.date:
        header_attrs["date"] = result.date
    header_attrs["type"] = content_type
    if result.lang:
        header_attrs["lang"] = result.lang
    if result.author:
        header_attrs["author"] = result.author

    # Note fetch error in header if we still got content
    errors = []
    if fetch_result and fetch_result.error:
        errors.append(CTXBlock(
            block_type="error",
            attributes={
                "type": "fetch-failed",
                "http_status": str(fetch_result.status),
                "detail": fetch_result.error,
            },
        ))

    doc = CTXDocument(
        version=CTX_VERSION,
        header=CTXBlock(block_type="doc", attributes=header_attrs),
        summary=CTXBlock(
            block_type="summary",
            attributes={"tokens": "80"},
            text=result.description,
        ) if result.description else None,
        content=skip_blocks + content_blocks,
        refs=ref_blocks,
        errors=errors,
    )

    # 10. Emit
    return emit(doc, target=target)


def _emit_error_doc(url: str, error_type: str, detail: str) -> str:
    """Produce a minimal CTX document with an error block."""
    doc = CTXDocument(
        version=CTX_VERSION,
        header=CTXBlock(block_type="doc", attributes={
            "version": CTX_VERSION,
            "url": url,
            "type": "error",
        }),
        errors=[CTXBlock(
            block_type="error",
            attributes={
                "type": error_type,
                "detail": detail,
            },
        )],
    )
    return emit(doc)
