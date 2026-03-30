# Copyright 2026 Fox Valley AI Foundation
# SPDX-License-Identifier: Apache-2.0

"""CTX escaping and encoding (spec Chapter 4)."""

from .grammar import RESERVED_DELIMITERS


def escape_body(text: str) -> str:
    """Double reserved delimiters in leaf/body text.

    §→§§, †→††, ◆→◆◆, ▸→▸▸, ∷→∷∷
    """
    result = text
    for d in RESERVED_DELIMITERS:
        result = result.replace(d, d + d)
    return result


def unescape_body(text: str) -> str:
    """Collapse doubled delimiters back to singles."""
    result = text
    for d in RESERVED_DELIMITERS:
        result = result.replace(d + d, d)
    return result


def quote_attr(value: str) -> str:
    """Quote an attribute value if it contains spaces.

    Escapes \\ and \" inside quoted values.
    """
    if not value:
        return '""'
    if " " not in value and '"' not in value and "\\" not in value:
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def unquote_attr(value: str) -> str:
    """Unquote and unescape an attribute value."""
    if not value:
        return ""
    if value.startswith('"') and value.endswith('"'):
        inner = value[1:-1]
        result = []
        i = 0
        while i < len(inner):
            if inner[i] == "\\" and i + 1 < len(inner):
                next_ch = inner[i + 1]
                if next_ch == '"':
                    result.append('"')
                elif next_ch == "\\":
                    result.append("\\")
                else:
                    # all other \X → literal \X
                    result.append("\\")
                    result.append(next_ch)
                i += 2
            else:
                result.append(inner[i])
                i += 1
        return "".join(result)
    return value


def format_attrs(attrs: dict[str, str], meta_keys: set[str] | None = None) -> str:
    """Format a dict of attributes into CTX attribute string.

    Keys in meta_keys get the † prefix.
    """
    if meta_keys is None:
        meta_keys = set()
    parts = []
    for key, val in attrs.items():
        prefix = "\u2020" if key in meta_keys or key.startswith("x-") else ""
        quoted = quote_attr(val)
        parts.append(f"{prefix}{key}={quoted}")
    return " ".join(parts)


def escape_pipe(text: str) -> str:
    """Escape literal pipes in data block cell values."""
    return text.replace("|", "\\|")


def unescape_pipe(text: str) -> str:
    """Unescape pipes in data block cell values."""
    return text.replace("\\|", "|")
