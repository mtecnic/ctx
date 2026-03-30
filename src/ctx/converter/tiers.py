# Copyright 2026 Fox Valley AI Foundation
# SPDX-License-Identifier: Apache-2.0

"""Extraction tier dispatch — fast, smart, and full (VLM) tiers."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import httpx

from ..models import CTXBlock

if TYPE_CHECKING:
    from .extractor import ExtractionResult


# --- Smart tier NER patterns ---

PRICE_PATTERN = re.compile(
    r"(?:USD|EUR|GBP|JPY|\$|€|£|¥)\s*[\d,]+\.?\d*"
    r"|[\d,]+\.?\d*\s*(?:USD|EUR|GBP|JPY|dollars?|euros?|pounds?)",
    re.IGNORECASE,
)

DATE_PATTERN = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b"
    r"|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}\b",
    re.IGNORECASE,
)

SPONSORED_PATTERN = re.compile(
    r"\b(?:sponsored|promoted|advertisement|ad|partner\s+content)\b",
    re.IGNORECASE,
)


def apply_smart_tier(result: ExtractionResult) -> None:
    """Apply smart-tier NER enhancements to extraction result.

    Detects prices, dates, sponsored content. Runs regex-based
    patterns that don't require an LLM.
    """
    for block in result.content_blocks:
        if block.block_type == "section":
            # Detect promoted/sponsored sections
            if SPONSORED_PATTERN.search(block.text):
                block.skip = True

        elif block.block_type == "p":
            # Detect price mentions (useful for classifier)
            if PRICE_PATTERN.search(block.text):
                block.attributes["_has_price"] = "true"
            # Detect date mentions
            if DATE_PATTERN.search(block.text):
                block.attributes["_has_date"] = "true"


async def apply_full_tier(
    result: ExtractionResult,
    vllm_url: str = "http://localhost:8000/v1",
    model: str = "",
) -> None:
    """Apply full-tier VLM enhancements.

    Sends images to the local VLM for alt-text generation
    when existing descriptions are insufficient.
    """
    if not model:
        # Auto-detect model from vLLM
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{vllm_url}/models")
                data = resp.json()
                models = data.get("data", [])
                if models:
                    model = models[0].get("id", "")
        except Exception:
            return  # VLM unavailable, skip gracefully

    if not model:
        return

    # Process images that lack good alt text
    for media in result.media:
        if media.subtype != "image":
            continue
        # Only call VLM if alt text is generic or missing
        if media.text and media.text not in ("Image", "image", ""):
            continue

        img_url = media.attributes.get("url", "")
        if not img_url:
            continue

        try:
            description = await _describe_image(vllm_url, model, img_url)
            if description:
                media.text = description
                media.attributes["source"] = f"vlm:{model.split('/')[-1]}"
        except Exception:
            pass  # Keep original text on failure


async def _describe_image(vllm_url: str, model: str, image_url: str) -> str:
    """Call VLM to generate an image description."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{vllm_url}/chat/completions",
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url},
                            },
                            {
                                "type": "text",
                                "text": "Describe this image in one concise sentence for a text document. Focus on what the image shows, not how it looks.",
                            },
                        ],
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.1,
            },
        )
        data = resp.json()
        choices = data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "").strip()
    return ""
