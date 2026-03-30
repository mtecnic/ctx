# Copyright 2026 Fox Valley AI Foundation
# SPDX-License-Identifier: Apache-2.0

"""Normalization stage — boolean normalization, empty block stripping, whitespace."""

from __future__ import annotations

from ..grammar import BOOL_FALSE, BOOL_TRUE
from ..models import CTXBlock


def normalize_bool(value: str) -> str:
    """Normalize boolean-like values to 'true' or 'false'."""
    v = value.strip().lower()
    if v in BOOL_TRUE:
        return "true"
    if v in BOOL_FALSE:
        return "false"
    return value  # not a boolean, pass through


def normalize_blocks(blocks: list[CTXBlock]) -> list[CTXBlock]:
    """Normalize a list of blocks in-place.

    - Strip empty data blocks (unless †empty=true is warranted)
    - Normalize boolean attribute values
    - Collapse redundant whitespace in text
    """
    result = []
    for block in blocks:
        # Recursively normalize children
        if block.children:
            block.children = normalize_blocks(block.children)

        # Strip empty data blocks
        if block.block_type == "data" and not block.lines:
            if block.attributes.get("empty") == "true":
                result.append(block)
            continue  # drop empty data blocks without †empty=true

        # Normalize text whitespace
        if block.text:
            # Collapse multiple spaces (but preserve newlines for code/textarea)
            if block.block_type not in ("code",):
                lines = block.text.splitlines()
                normalized = []
                for line in lines:
                    # Collapse runs of spaces
                    line = " ".join(line.split())
                    normalized.append(line)
                block.text = "\n".join(normalized)

        # Normalize boolean-like attribute values
        bool_attrs = {"value"}  # attrs that might contain booleans
        for key in bool_attrs:
            if key in block.attributes:
                val = block.attributes[key]
                if val.lower() in BOOL_TRUE | BOOL_FALSE:
                    block.attributes[key] = normalize_bool(val)

        result.append(block)

    return result
