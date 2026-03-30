# Copyright 2026 Fox Valley AI Foundation
# SPDX-License-Identifier: Apache-2.0

"""Content type classification — determines §content.* subtype."""

from __future__ import annotations

import re

from .extractor import ExtractionResult


def classify(result: ExtractionResult) -> str:
    """Classify content type based on extraction result.

    Returns one of: article, product, application, video, reference
    """
    scores: dict[str, float] = {
        "article": 0.0,
        "product": 0.0,
        "application": 0.0,
        "video": 0.0,
        "reference": 0.5,  # default baseline
    }

    meta = result.meta

    # JSON-LD type
    jsonld = meta.get("jsonld_type", "").lower()
    if jsonld in ("article", "newsarticle", "blogposting", "reportage"):
        scores["article"] += 3.0
    elif jsonld in ("product", "offer"):
        scores["product"] += 3.0
    elif jsonld in ("videoobject",):
        scores["video"] += 3.0

    # OG type
    og_type = meta.get("og:type", "").lower()
    if og_type == "article":
        scores["article"] += 2.0
    elif og_type in ("product", "product.item"):
        scores["product"] += 2.0
    elif og_type in ("video", "video.other"):
        scores["video"] += 2.0

    # Content signals
    paragraph_count = sum(1 for b in result.content_blocks if b.block_type == "p")
    heading_count = sum(1 for b in result.content_blocks if b.block_type == "section")

    # Articles: lots of paragraphs, headings, date, author
    if paragraph_count >= 3:
        scores["article"] += 1.5
    if heading_count >= 2:
        scores["article"] += 0.5
    if result.date:
        scores["article"] += 1.0
    if result.author:
        scores["article"] += 1.0

    # Products: price patterns, cart forms
    all_text = " ".join(b.text for b in result.content_blocks)
    if re.search(r"\$[\d,]+\.?\d*|\d+\.\d{2}\s*(USD|EUR|GBP)", all_text):
        scores["product"] += 2.0
    if any("cart" in (f.attributes.get("_action", "")).lower() for f in result.forms):
        scores["product"] += 2.0

    # Application: lots of forms, few paragraphs
    if result.forms and paragraph_count < 3:
        scores["application"] += 2.0
    if len(result.forms) >= 2:
        scores["application"] += 1.0

    # Video: video media blocks
    video_count = sum(1 for m in result.media if m.subtype == "video")
    if video_count > 0:
        scores["video"] += 2.0

    # Return highest scoring type
    return max(scores, key=scores.get)  # type: ignore[arg-type]
