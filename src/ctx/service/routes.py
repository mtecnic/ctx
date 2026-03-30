# Copyright 2026 Fox Valley AI Foundation
# SPDX-License-Identifier: Apache-2.0

"""API routes for CTX converter service."""

from __future__ import annotations

import hashlib
from typing import Annotated

from fastapi import APIRouter, Header, Query, Request, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from ..converter.pipeline import convert
from .config import config

router = APIRouter()


class ConvertRequest(BaseModel):
    url: str | None = None
    html: str | None = None
    source_url: str | None = None


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "tiers": ["fast", "smart", "full"],
        "default_tier": config.DEFAULT_TIER,
    }


@router.post("/convert", response_class=PlainTextResponse)
async def convert_post(
    request: Request,
    body: ConvertRequest,
    tier: str = Query(default=None),
    target: str = Query(default="unicode"),
    strip_skip: bool = Query(default=True),
):
    """Convert URL or raw HTML to CTX format."""
    tier = tier or config.DEFAULT_TIER
    source = body.url or body.html or ""
    if not source:
        return PlainTextResponse("Missing 'url' or 'html' in request body", status_code=400)

    source_url = body.source_url or ""
    cache_key = _cache_key(body.url or source_url or "raw", tier) if body.url else ""

    # Check cache
    cached = await _cache_get(request, cache_key) if cache_key else None
    if cached is not None:
        return PlainTextResponse(
            cached,
            media_type="text/ctx",
            headers={"X-CTX-Cache": "hit"},
        )

    result = await convert(
        source,
        tier=tier,
        target=target,
        strip_skip=strip_skip,
        vllm_url=config.VLLM_URL,
        source_url=source_url,
    )

    # Store in cache
    if cache_key:
        ttl = config.CACHE_TTL_FULL if tier == "full" else config.CACHE_TTL
        await _cache_set(request, cache_key, result, ttl)

    return PlainTextResponse(
        result,
        media_type="text/ctx",
        headers={"X-CTX-Cache": "miss"},
    )


@router.get("/convert", response_class=PlainTextResponse)
async def convert_get(
    request: Request,
    url: str = Query(..., description="URL to convert"),
    tier: str = Query(default=None),
    target: str = Query(default="unicode"),
    strip_skip: bool = Query(default=True),
):
    """Convert a URL to CTX format via query parameter."""
    tier = tier or config.DEFAULT_TIER
    cache_key = _cache_key(url, tier)

    cached = await _cache_get(request, cache_key)
    if cached is not None:
        return PlainTextResponse(
            cached,
            media_type="text/ctx",
            headers={"X-CTX-Cache": "hit"},
        )

    result = await convert(
        url,
        tier=tier,
        target=target,
        strip_skip=strip_skip,
        vllm_url=config.VLLM_URL,
    )

    ttl = config.CACHE_TTL_FULL if tier == "full" else config.CACHE_TTL
    await _cache_set(request, cache_key, result, ttl)

    return PlainTextResponse(
        result,
        media_type="text/ctx",
        headers={"X-CTX-Cache": "miss"},
    )


@router.get("/proxy/{url:path}", response_class=PlainTextResponse)
async def proxy(
    request: Request,
    url: str,
    tier: str = Query(default=None),
    target: str = Query(default="unicode"),
    strip_skip: bool = Query(default=True),
):
    """Transparent proxy — fetch URL and return CTX."""
    tier = tier or config.DEFAULT_TIER

    # Reconstruct full URL (path parameter strips the scheme)
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    cache_key = _cache_key(url, tier)
    cached = await _cache_get(request, cache_key)
    if cached is not None:
        return PlainTextResponse(
            cached,
            media_type="text/ctx",
            headers={"X-CTX-Cache": "hit"},
        )

    result = await convert(
        url,
        tier=tier,
        target=target,
        strip_skip=strip_skip,
        vllm_url=config.VLLM_URL,
    )

    ttl = config.CACHE_TTL_FULL if tier == "full" else config.CACHE_TTL
    await _cache_set(request, cache_key, result, ttl)

    return PlainTextResponse(
        result,
        media_type="text/ctx",
        headers={"X-CTX-Cache": "miss"},
    )


@router.post("/parse")
async def parse_ctx(request: Request):
    """Parse a CTX document and return its structure as JSON."""
    body = await request.body()
    text = body.decode("utf-8")

    from ..parser import parse
    doc = parse(text)
    return doc.model_dump()


@router.get("/cache/stats")
async def cache_stats(request: Request):
    """Return cache statistics."""
    redis_client = getattr(request.app.state, "redis", None)
    if not redis_client:
        return {"status": "disabled", "reason": "Redis not available"}

    try:
        info = await redis_client.info("keyspace")
        db_info = info.get("db1", {})
        return {
            "status": "enabled",
            "keys": db_info.get("keys", 0),
            "expires": db_info.get("expires", 0),
        }
    except Exception as e:
        return {"status": "error", "reason": str(e)}


# --- Cache helpers ---

def _cache_key(url: str, tier: str) -> str:
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
    return f"ctx:{url_hash}:{tier}"


async def _cache_get(request: Request, key: str) -> str | None:
    redis_client = getattr(request.app.state, "redis", None)
    if not redis_client or not key:
        return None
    try:
        return await redis_client.get(key)
    except Exception:
        return None


async def _cache_set(request: Request, key: str, value: str, ttl: int) -> None:
    redis_client = getattr(request.app.state, "redis", None)
    if not redis_client or not key:
        return
    try:
        await redis_client.set(key, value, ex=ttl)
    except Exception:
        pass
