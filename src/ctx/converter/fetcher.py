# Copyright 2026 Fox Valley AI Foundation
# SPDX-License-Identifier: Apache-2.0

"""URL fetching with content negotiation."""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx


@dataclass
class FetchResult:
    html: str
    url: str  # final URL after redirects
    status: int
    content_type: str
    headers: dict[str, str] = field(default_factory=dict)
    error: str = ""


# Use a realistic browser User-Agent to avoid 403 blocks from WAFs.
# Many sites (Bloomberg, NOAA, Congress.gov, Canva, ESPN) reject
# non-browser user agents outright.
_DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
}


_HTML_CONTENT_TYPES = frozenset({
    "text/html", "application/xhtml+xml", "text/plain", "text/xml",
    "application/xml", "application/json",
})


def _is_html_like(content_type: str) -> bool:
    """Check if the content-type header indicates parseable text content."""
    if not content_type:
        return True  # missing content-type — assume HTML
    ct = content_type.split(";")[0].strip().lower()
    return ct in _HTML_CONTENT_TYPES


async def fetch(source: str, timeout: float = 20.0) -> FetchResult:
    """Fetch a URL and return the HTML content.

    Returns a FetchResult with error field set on failure instead of raising.
    """
    url = source if "://" in source else f"https://{source}"

    async with httpx.AsyncClient(
        follow_redirects=True,
        max_redirects=10,
        timeout=timeout,
        headers=_DEFAULT_HEADERS,
        verify=False,
    ) as client:
        try:
            resp = await client.get(url)
        except httpx.TimeoutException:
            return FetchResult(
                html="", url=url, status=0, content_type="",
                error=f"Timeout after {timeout}s",
            )
        except httpx.ConnectError as e:
            return FetchResult(
                html="", url=url, status=0, content_type="",
                error=f"Connection failed: {e}",
            )
        except httpx.TooManyRedirects:
            return FetchResult(
                html="", url=url, status=0, content_type="",
                error="Too many redirects",
            )
        except Exception as e:
            return FetchResult(
                html="", url=url, status=0, content_type="",
                error=f"{type(e).__name__}: {e}",
            )

        ct = resp.headers.get("content-type", "")

        # Reject non-HTML content (binary images, raw JSON APIs, etc.)
        if not _is_html_like(ct):
            return FetchResult(
                html="", url=str(resp.url), status=resp.status_code,
                content_type=ct,
                error=f"Non-HTML content-type: {ct}",
            )

        if resp.status_code >= 400:
            return FetchResult(
                html=resp.text,
                url=str(resp.url),
                status=resp.status_code,
                content_type=ct,
                headers=dict(resp.headers),
                error=f"HTTP {resp.status_code}",
            )

        return FetchResult(
            html=resp.text,
            url=str(resp.url),
            status=resp.status_code,
            content_type=ct,
            headers=dict(resp.headers),
        )
