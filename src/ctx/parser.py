# Copyright 2026 Fox Valley AI Foundation
# SPDX-License-Identifier: Apache-2.0

"""CTX parser — parse .ctx text into CTXDocument/CTXDelta models.

Implements the canonical parsing algorithm from spec chapters 15-16.
"""

from __future__ import annotations

import re

from .escaping import unquote_attr
from .grammar import (
    CTX_VERSION,
    DATA_TYPES,
    DELIMITERS,
    ERROR_TYPES,
    LEAF_TYPES,
    SKIP_TYPES,
)
from .models import CTXBlock, CTXDelta, CTXDocument


def parse(text: str) -> CTXDocument | CTXDelta:
    """Parse CTX text into a document or delta model."""
    lines = text.splitlines()
    if not lines:
        raise ValueError("Empty CTX document")

    first_line = lines[0].strip()

    # Determine payload type
    if first_line.startswith("\u00a7delta"):
        return _parse_delta(lines)
    elif first_line.startswith("\u00a7doc.ctx_v"):
        return _parse_document(lines)
    else:
        raise ValueError(f"Invalid CTX: first line must be §doc.ctx_v* or §delta, got: {first_line[:50]}")


def _parse_document(lines: list[str]) -> CTXDocument:
    """Parse a full CTX document."""
    idx = 0
    total = len(lines)

    # 1. Parse header
    header, idx = _parse_header(lines, idx)

    doc = CTXDocument(
        version=header.attributes.get("version", CTX_VERSION),
        header=header,
    )

    # 2. Parse remaining blocks
    while idx < total:
        line = lines[idx]
        stripped = line.strip()

        if not stripped:
            idx += 1
            continue

        # Summary
        if stripped.startswith("\u00a7summary"):
            block, idx = _parse_summary(lines, idx)
            doc.summary = block
            continue

        # Commerce
        if stripped.startswith("\u2020commerce"):
            block, idx = _parse_commerce(lines, idx)
            doc.commerce = block
            continue

        # Auth challenge
        if stripped.startswith("\u00a7auth-challenge"):
            block, idx = _parse_auth_challenge(lines, idx)
            doc.auth_challenge = block
            continue

        # Error
        if stripped.startswith("\u00a7error"):
            block, idx = _parse_error(lines, idx)
            doc.errors.append(block)
            continue

        # Ref
        if stripped.startswith("\u00a7ref"):
            block = _parse_ref(stripped)
            doc.refs.append(block)
            idx += 1
            continue

        # Content container
        if stripped.startswith("\u00a7content."):
            block, idx = _parse_content(lines, idx)
            doc.content.append(block)
            continue

        # Skip block
        skip_match = re.match(r"\u00a7(\w+)\s+\[skip\]", stripped)
        if skip_match and skip_match.group(1) in SKIP_TYPES:
            block, idx = _parse_skip(lines, idx, skip_match.group(1))
            doc.content.append(block)
            continue

        # Section at top level
        sec_match = re.match(r"\u00a7([1-4])\s+(.+)", stripped)
        if sec_match:
            block, idx = _parse_section(lines, idx)
            doc.content.append(block)
            continue

        # Leaf block at top level
        if any(stripped.startswith(f"\u00a7{lt}") for lt in LEAF_TYPES):
            block, idx = _parse_leaf(lines, idx)
            doc.content.append(block)
            continue

        # Data block
        if stripped.startswith(("\u2237 ", ":: ")):
            block, idx = _parse_data(lines, idx)
            doc.content.append(block)
            continue

        # Interactive block
        if stripped.startswith(("\u25b8 ", ">> ")):
            block, idx = _parse_interactive(lines, idx)
            doc.content.append(block)
            continue

        # Media block
        if stripped.startswith(("\u25c6 ", "<> ")):
            block, idx = _parse_media(lines, idx)
            doc.content.append(block)
            continue

        # Unknown line — skip
        idx += 1

    return doc


def _parse_delta(lines: list[str]) -> CTXDelta:
    """Parse a delta response."""
    idx = 0
    attrs = _tokenize_attrs(lines[0][len("\u00a7delta"):].strip())
    delta = CTXDelta(header=CTXBlock(block_type="delta", attributes=attrs))
    idx = 1

    while idx < len(lines):
        line = lines[idx].strip()
        if not line:
            idx += 1
            continue

        if line.startswith("\u00a7toast"):
            attrs = _tokenize_attrs(line[len("\u00a7toast"):].strip())
            delta.toasts.append(CTXBlock(block_type="toast", attributes=attrs))
            idx += 1

        elif line.startswith("\u00a7update"):
            attrs = _tokenize_attrs(line[len("\u00a7update"):].strip())
            block = CTXBlock(block_type="update", attributes=attrs)
            idx += 1
            # Collect children
            while idx < len(lines) and lines[idx].startswith("  "):
                child_line = lines[idx]
                child_stripped = child_line.strip()
                if child_stripped.startswith(("\u25b8 ", ">> ")):
                    child, idx = _parse_interactive(lines, idx)
                    block.children.append(child)
                else:
                    idx += 1
            delta.updates.append(block)
        else:
            idx += 1

    return delta


# --- Header parsing ---

def _parse_header(lines: list[str], idx: int) -> tuple[CTXBlock, int]:
    first = lines[idx].strip()
    # Extract version
    ver_match = re.match(r"\u00a7doc\.ctx_v(\d+\.\d+)\s*(.*)", first)
    if not ver_match:
        raise ValueError(f"Invalid header: {first[:80]}")
    version = ver_match.group(1)
    rest = ver_match.group(2)
    attrs = _tokenize_attrs(rest)
    attrs["version"] = version
    return CTXBlock(block_type="doc", attributes=attrs), idx + 1


# --- Block parsers ---

def _parse_summary(lines: list[str], idx: int) -> tuple[CTXBlock, int]:
    line = lines[idx].strip()
    attrs = _tokenize_attrs(line[len("\u00a7summary"):].strip())
    idx += 1
    text_lines = []
    while idx < len(lines) and lines[idx].startswith("  "):
        text_lines.append(lines[idx].strip())
        idx += 1
    return CTXBlock(
        block_type="summary",
        attributes=attrs,
        text="\n".join(text_lines),
    ), idx


def _parse_commerce(lines: list[str], idx: int) -> tuple[CTXBlock, int]:
    block = CTXBlock(block_type="commerce")
    idx += 1
    while idx < len(lines) and lines[idx].startswith("  "):
        line = lines[idx].strip()
        if line.startswith("\u2020"):
            parts = line[1:].split(None, 1)
            subtype = parts[0] if parts else ""
            attrs = _tokenize_attrs(parts[1] if len(parts) > 1 else "")
            block.children.append(CTXBlock(
                block_type="commerce-item",
                subtype=subtype,
                attributes=attrs,
            ))
        idx += 1
    return block, idx


def _parse_auth_challenge(lines: list[str], idx: int) -> tuple[CTXBlock, int]:
    attrs: dict[str, str] = {}
    idx += 1
    while idx < len(lines) and lines[idx].startswith("  "):
        line = lines[idx].strip()
        if line.startswith("\u2020"):
            kv = _tokenize_attrs(line[1:])
            attrs.update(kv)
        idx += 1
    return CTXBlock(block_type="auth-challenge", attributes=attrs), idx


def _parse_error(lines: list[str], idx: int) -> tuple[CTXBlock, int]:
    line = lines[idx].strip()
    attrs = _tokenize_attrs(line[len("\u00a7error"):].strip())
    idx += 1
    while idx < len(lines) and lines[idx].startswith("  "):
        inner = lines[idx].strip()
        if inner.startswith("\u2020"):
            kv = _tokenize_attrs(inner[1:])
            attrs.update(kv)
        idx += 1
    return CTXBlock(block_type="error", attributes=attrs), idx


def _parse_ref(line: str) -> CTXBlock:
    rest = line[len("\u00a7ref"):].strip()
    attrs = _tokenize_attrs(rest)
    return CTXBlock(block_type="ref", attributes=attrs)


def _parse_skip(lines: list[str], idx: int, skip_type: str) -> tuple[CTXBlock, int]:
    idx += 1
    text_lines = []
    while idx < len(lines) and lines[idx].startswith("  "):
        text_lines.append(lines[idx].strip())
        idx += 1
    return CTXBlock(
        block_type="skip",
        subtype=skip_type,
        skip=True,
        text="\n".join(text_lines),
    ), idx


def _parse_content(lines: list[str], idx: int) -> tuple[CTXBlock, int]:
    line = lines[idx].strip()
    match = re.match(r"\u00a7content\.(\S+)", line)
    subtype = match.group(1) if match else "reference"
    block = CTXBlock(block_type="content", subtype=subtype)
    idx += 1

    while idx < len(lines):
        if not lines[idx].startswith("  "):
            # Check if this is a non-indented block that belongs outside content
            stripped = lines[idx].strip()
            if stripped and (
                stripped.startswith("\u00a7ref")
                or stripped.startswith("\u00a7footer")
                or stripped.startswith("\u00a7nav")
                or stripped.startswith("\u00a7error")
                or not stripped
            ):
                break
            # Some docs don't indent under §content — try to parse anyway
            if stripped.startswith("\u00a7"):
                child, idx = _parse_content_child(lines, idx)
                if child:
                    block.children.append(child)
                continue
            break

        child, idx = _parse_content_child(lines, idx)
        if child:
            block.children.append(child)

    return block, idx


def _parse_content_child(lines: list[str], idx: int) -> tuple[CTXBlock | None, int]:
    """Parse a single child block inside a content container."""
    if idx >= len(lines):
        return None, idx

    stripped = lines[idx].strip()
    if not stripped:
        return None, idx + 1

    # Section
    sec_match = re.match(r"\u00a7([1-4])\s+(.+)", stripped)
    if sec_match:
        return _parse_section(lines, idx)

    # Leaf
    if any(stripped.startswith(f"\u00a7{lt}") for lt in LEAF_TYPES):
        return _parse_leaf(lines, idx)

    # Data
    if stripped.startswith(("\u2237 ", ":: ")):
        return _parse_data(lines, idx)

    # Interactive
    if stripped.startswith(("\u25b8 ", ">> ")):
        return _parse_interactive(lines, idx)

    # Media
    if stripped.startswith(("\u25c6 ", "<> ")):
        return _parse_media(lines, idx)

    # Skip block inside content
    skip_match = re.match(r"\u00a7(\w+)\s+\[skip\]", stripped)
    if skip_match:
        return _parse_skip(lines, idx, skip_match.group(1))

    return None, idx + 1


def _parse_section(lines: list[str], idx: int) -> tuple[CTXBlock, int]:
    stripped = lines[idx].strip()
    match = re.match(r"\u00a7([1-4])\s+(.+)", stripped)
    if not match:
        return CTXBlock(block_type="section", depth=1, text=stripped), idx + 1

    depth = int(match.group(1))
    rest = match.group(2)

    # Check for [skip]
    skip = False
    if rest.endswith("[skip]"):
        skip = True
        rest = rest[:-len("[skip]")].strip()

    # Check for id=
    attrs: dict[str, str] = {}
    id_match = re.search(r"\bid=(\S+)", rest)
    if id_match:
        attrs["id"] = unquote_attr(id_match.group(1))
        rest = rest[:id_match.start()].strip()

    block = CTXBlock(
        block_type="section",
        depth=depth,
        text=rest,
        skip=skip,
        attributes=attrs,
    )
    idx += 1
    base_indent = _indent_level(lines[idx - 1])

    # Parse children (indented deeper)
    while idx < len(lines):
        if not lines[idx].strip():
            idx += 1
            continue
        child_indent = _indent_level(lines[idx])
        if child_indent <= base_indent:
            break
        child, idx = _parse_content_child(lines, idx)
        if child:
            block.children.append(child)

    return block, idx


def _parse_leaf(lines: list[str], idx: int) -> tuple[CTXBlock, int]:
    stripped = lines[idx].strip()

    for lt in LEAF_TYPES:
        prefix = f"\u00a7{lt}"
        if stripped.startswith(prefix):
            rest = stripped[len(prefix):].strip()

            if lt == "code":
                # Code blocks: may have lang= and multiline content
                attrs: dict[str, str] = {}
                if rest.startswith("lang="):
                    lang_match = re.match(r"lang=(\S+)\s*(.*)", rest)
                    if lang_match:
                        attrs["lang"] = lang_match.group(1)
                        rest = lang_match.group(2)

                idx += 1
                code_lines = []
                while idx < len(lines) and lines[idx].startswith("  "):
                    code_lines.append(lines[idx][2:])  # strip 2-space indent
                    idx += 1
                text = "\n".join(code_lines) if code_lines else rest
                return CTXBlock(block_type="code", text=text, attributes=attrs), idx

            idx += 1
            return CTXBlock(block_type=lt, text=rest), idx

    return CTXBlock(block_type="p", text=stripped), idx + 1


def _parse_data(lines: list[str], idx: int) -> tuple[CTXBlock, int]:
    stripped = lines[idx].strip()
    # Remove delimiter prefix
    if stripped.startswith("\u2237 "):
        rest = stripped[2:]
    elif stripped.startswith(":: "):
        rest = stripped[3:]
    else:
        rest = stripped

    # Parse type and attributes
    parts = rest.split(None, 1)
    subtype = parts[0] if parts else "table"
    attrs = _tokenize_attrs(parts[1] if len(parts) > 1 else "")

    idx += 1
    data_lines: list[str] = []
    while idx < len(lines):
        line = lines[idx].strip()
        if line in ("\u2237/", "::/"):
            idx += 1
            break
        if line:
            # Strip leading/trailing pipes
            line = line.strip()
            if line.startswith("|"):
                line = line[1:]
            if line.endswith("|") and not line.endswith("\\|"):
                line = line[:-1]
            data_lines.append(line.strip())
        idx += 1

    return CTXBlock(
        block_type="data",
        subtype=subtype,
        attributes=attrs,
        lines=data_lines,
    ), idx


def _parse_interactive(lines: list[str], idx: int) -> tuple[CTXBlock, int]:
    stripped = lines[idx].strip()
    if stripped.startswith("\u25b8 "):
        rest = stripped[2:]
    elif stripped.startswith(">> "):
        rest = stripped[3:]
    else:
        rest = stripped

    # Parse type.subtype and attributes
    parts = rest.split(None, 1)
    type_str = parts[0] if parts else "button"
    attrs = _tokenize_attrs(parts[1] if len(parts) > 1 else "")

    type_parts = type_str.split(".", 1)
    block_type = type_parts[0]
    subtype = type_parts[1] if len(type_parts) > 1 else ""

    block = CTXBlock(
        block_type=block_type,
        subtype=subtype,
        attributes=attrs,
    )
    idx += 1
    base_indent = _indent_level(lines[idx - 1])

    # Parse children and textarea content
    text_lines = []
    while idx < len(lines):
        if not lines[idx].strip():
            idx += 1
            continue
        child_indent = _indent_level(lines[idx])
        if child_indent <= base_indent:
            break
        child_stripped = lines[idx].strip()
        if child_stripped.startswith(("\u25b8 ", ">> ")):
            child, idx = _parse_interactive(lines, idx)
            block.children.append(child)
        else:
            # Textarea content or other indented text
            text_lines.append(child_stripped)
            idx += 1

    if text_lines:
        block.text = "\n".join(text_lines)

    return block, idx


def _parse_media(lines: list[str], idx: int) -> tuple[CTXBlock, int]:
    stripped = lines[idx].strip()
    if stripped.startswith("\u25c6 "):
        rest = stripped[2:]
    elif stripped.startswith("<> "):
        rest = stripped[3:]
    else:
        rest = stripped

    parts = rest.split(None, 1)
    subtype = parts[0] if parts else "image"
    attrs = _tokenize_attrs(parts[1] if len(parts) > 1 else "")

    idx += 1
    # Fallback text
    text_lines = []
    while idx < len(lines) and lines[idx].startswith("  "):
        text_lines.append(lines[idx].strip())
        idx += 1

    return CTXBlock(
        block_type="media",
        subtype=subtype,
        attributes=attrs,
        text="\n".join(text_lines),
    ), idx


# --- Attribute tokenizer (spec §15.1) ---

def _tokenize_attrs(text: str) -> dict[str, str]:
    """Parse attribute string into dict.

    Handles: key=value, key="quoted value", †key=value, †x-custom=value
    """
    attrs: dict[str, str] = {}
    if not text:
        return attrs

    i = 0
    n = len(text)

    while i < n:
        # Skip whitespace
        while i < n and text[i] == " ":
            i += 1
        if i >= n:
            break

        # Skip † prefix
        if text[i] == "\u2020":
            i += 1

        # Read key
        key_start = i
        while i < n and text[i] not in ("=", " "):
            i += 1
        key = text[key_start:i]

        if not key:
            i += 1
            continue

        if i >= n or text[i] != "=":
            # Key without value (flag)
            attrs[key] = "true"
            continue

        i += 1  # skip =

        if i >= n:
            attrs[key] = ""
            break

        # Read value
        if text[i] == '"':
            # Quoted value
            i += 1
            val_chars = []
            while i < n:
                if text[i] == "\\" and i + 1 < n:
                    next_ch = text[i + 1]
                    if next_ch == '"':
                        val_chars.append('"')
                    elif next_ch == "\\":
                        val_chars.append("\\")
                    else:
                        val_chars.append("\\")
                        val_chars.append(next_ch)
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    val_chars.append(text[i])
                    i += 1
            attrs[key] = "".join(val_chars)
        else:
            # Unquoted value
            val_start = i
            while i < n and text[i] != " ":
                i += 1
            attrs[key] = text[val_start:i]

    return attrs


def _indent_level(line: str) -> int:
    """Count leading 2-space indents."""
    spaces = len(line) - len(line.lstrip(" "))
    return spaces // 2
