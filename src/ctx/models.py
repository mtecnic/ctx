# Copyright 2026 Fox Valley AI Foundation
# SPDX-License-Identifier: Apache-2.0

"""Pydantic models for CTX document structure."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CTXBlock(BaseModel):
    """A single block in a CTX document tree."""

    block_type: str  # "doc", "section", "p", "code", "quote", "aside",
                     # "data", "media", "interactive", "ref", "error",
                     # "content", "summary", "commerce", "auth-challenge",
                     # "skip", "toast", "update", "delta", "nav", "footer", etc.
    subtype: str = ""           # e.g. "article" for content.article, "table" for data
    depth: int | None = None    # 1-4 for sections
    attributes: dict[str, str] = Field(default_factory=dict)
    skip: bool = False
    children: list[CTXBlock] = Field(default_factory=list)
    text: str = ""              # leaf text content (may span multiple lines)
    lines: list[str] = Field(default_factory=list)  # for data rows, textarea lines


class CTXDocument(BaseModel):
    """A parsed CTX document."""

    version: str = "1.0"
    header: CTXBlock
    summary: CTXBlock | None = None
    commerce: CTXBlock | None = None
    auth_challenge: CTXBlock | None = None
    content: list[CTXBlock] = Field(default_factory=list)
    refs: list[CTXBlock] = Field(default_factory=list)
    errors: list[CTXBlock] = Field(default_factory=list)


class CTXDelta(BaseModel):
    """A delta response (state update)."""

    header: CTXBlock
    toasts: list[CTXBlock] = Field(default_factory=list)
    updates: list[CTXBlock] = Field(default_factory=list)
