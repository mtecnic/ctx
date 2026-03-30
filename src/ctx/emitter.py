# Copyright 2026 Fox Valley AI Foundation
# SPDX-License-Identifier: Apache-2.0

"""CTX emitter — serialize CTXDocument/CTXDelta to .ctx text."""

from __future__ import annotations

from .escaping import escape_body, escape_pipe, quote_attr
from .grammar import ASCII_FALLBACKS, DELIMITERS
from .models import CTXBlock, CTXDelta, CTXDocument

# Metadata keys that get the † prefix when emitting
META_KEYS = frozenset({
    "date", "type", "lang", "author", "word_count", "hash",
    "original_etag", "continuation", "id_namespace", "tokenizer-family",
    "rel", "source", "confidence", "state", "duration",
    "truncated", "empty", "note", "status", "original_url",
    "http_status", "detail", "method", "token_endpoint", "scopes",
    "paywall", "billing", "cost",
})


def _is_meta(key: str) -> bool:
    return key in META_KEYS or key.startswith("x-")


class Emitter:
    """Emits CTX text from document models."""

    def __init__(self, target: str = "unicode"):
        self.target = target
        if target == "ascii":
            self.d_media = ASCII_FALLBACKS["media"]
            self.d_interactive = ASCII_FALLBACKS["interactive"]
            self.d_data = ASCII_FALLBACKS["data"]
            self.d_data_close = "::/"
        else:
            self.d_media = DELIMITERS["media"]
            self.d_interactive = DELIMITERS["interactive"]
            self.d_data = DELIMITERS["data"]
            self.d_data_close = "\u2237/"  # ∷/
        self.d_section = DELIMITERS["section"]
        self.d_meta = DELIMITERS["metadata"]

    def emit_document(self, doc: CTXDocument) -> str:
        lines: list[str] = []
        self._emit_header(doc.header, lines)
        if doc.summary:
            self._emit_summary(doc.summary, lines)
        if doc.commerce:
            self._emit_commerce(doc.commerce, lines)
        if doc.auth_challenge:
            self._emit_auth_challenge(doc.auth_challenge, lines)
        for block in doc.content:
            self._emit_block(block, lines, indent=0)
        for block in doc.errors:
            self._emit_error(block, lines)
        for ref in doc.refs:
            self._emit_ref(ref, lines)
        return "\n".join(lines) + "\n"

    def emit_delta(self, delta: CTXDelta) -> str:
        lines: list[str] = []
        attrs = self._format_attrs(delta.header.attributes)
        lines.append(f"{self.d_section}delta{' ' + attrs if attrs else ''}")
        lines.append("")
        for toast in delta.toasts:
            attrs = self._format_attrs(toast.attributes)
            lines.append(f"{self.d_section}toast{' ' + attrs if attrs else ''}")
        for update in delta.updates:
            target = update.attributes.get("target", "")
            lines.append(f"{self.d_section}update target={target}")
            for child in update.children:
                self._emit_block(child, lines, indent=1)
        return "\n".join(lines) + "\n"

    def _emit_header(self, header: CTXBlock, lines: list[str]) -> None:
        parts = [f"{self.d_section}doc.ctx_v{header.attributes.get('version', '1.0')}"]
        for key, val in header.attributes.items():
            if key == "version":
                continue
            prefix = self.d_meta if _is_meta(key) else ""
            parts.append(f"{prefix}{key}={quote_attr(val)}")
        lines.append(" ".join(parts))
        lines.append("")

    def _emit_summary(self, summary: CTXBlock, lines: list[str]) -> None:
        attrs = self._format_attrs(summary.attributes)
        lines.append(f"{self.d_section}summary{' ' + attrs if attrs else ''}")
        if summary.text:
            for line in summary.text.splitlines():
                lines.append(f"  {line}")
        lines.append("")

    def _emit_commerce(self, commerce: CTXBlock, lines: list[str]) -> None:
        lines.append(f"{self.d_meta}commerce")
        for child in commerce.children:
            attrs = self._format_attrs(child.attributes)
            lines.append(f"  {self.d_meta}{child.subtype}{' ' + attrs if attrs else ''}")
        lines.append("")

    def _emit_auth_challenge(self, auth: CTXBlock, lines: list[str]) -> None:
        lines.append(f"{self.d_section}auth-challenge")
        for key, val in auth.attributes.items():
            lines.append(f"  {self.d_meta}{key}={quote_attr(val)}")
        lines.append("")

    def _emit_block(self, block: CTXBlock, lines: list[str], indent: int = 0) -> None:
        pad = "  " * indent
        bt = block.block_type

        if bt == "content":
            subtype = f".{block.subtype}" if block.subtype else ""
            lines.append(f"{pad}{self.d_section}content{subtype}")
            for child in block.children:
                self._emit_block(child, lines, indent + 1)
            return

        if bt == "skip":
            lines.append(f"{pad}{self.d_section}{block.subtype} [skip]")
            if block.text:
                for line in block.text.splitlines():
                    lines.append(f"{pad}  {line}")
            return

        if bt == "section":
            depth = block.depth or 1
            skip = " [skip]" if block.skip else ""
            id_attr = f" id={quote_attr(block.attributes['id'])}" if "id" in block.attributes else ""
            lines.append(f"{pad}{self.d_section}{depth} {block.text}{id_attr}{skip}")
            for child in block.children:
                self._emit_block(child, lines, indent + 1)
            return

        if bt == "p":
            text = escape_body(block.text) if block.text else ""
            # citation pointers [refN] are plain text, don't double-escape brackets
            lines.append(f"{pad}{self.d_section}p {text}")
            return

        if bt == "code":
            lang = f" lang={block.attributes['lang']}" if "lang" in block.attributes else ""
            lines.append(f"{pad}{self.d_section}code{lang}")
            if block.text:
                for line in block.text.splitlines():
                    lines.append(f"{pad}  {line}")
            return

        if bt == "quote":
            lines.append(f"{pad}{self.d_section}quote {block.text}")
            return

        if bt == "aside":
            lines.append(f"{pad}{self.d_section}aside {block.text}")
            return

        if bt == "data":
            attrs = self._format_attrs(block.attributes)
            lines.append(f"{pad}{self.d_data} {block.subtype}{' ' + attrs if attrs else ''}")
            for row in block.lines:
                cells = [escape_pipe(c.strip()) for c in row.split("|")]
                lines.append(f"{pad}  {'  | '.join(cells)}")
            lines.append(f"{pad}{self.d_data_close}")
            return

        if bt == "media":
            attrs = self._format_attrs(block.attributes)
            lines.append(f"{pad}{self.d_media} {block.subtype}{' ' + attrs if attrs else ''}")
            if block.text:
                for line in block.text.splitlines():
                    lines.append(f"{pad}  {line}")
            return

        if bt == "interactive":
            subtype = f".{block.subtype}" if block.subtype else ""
            type_name = block.attributes.pop("_type", block.block_type)
            if "_type" in block.attributes:
                del block.attributes["_type"]
            raw_type = block.attributes.pop("raw_type", "")
            if not raw_type:
                raw_type = f"{bt}{subtype}"
            attrs = self._format_attrs(block.attributes)
            lines.append(f"{pad}{self.d_interactive} {raw_type}{' ' + attrs if attrs else ''}")
            if block.text:
                for line in block.text.splitlines():
                    lines.append(f"{pad}  {line}")
            for child in block.children:
                self._emit_block(child, lines, indent + 1)
            return

        if bt == "form":
            subtype = f".{block.subtype}" if block.subtype else ""
            attrs = self._format_attrs(block.attributes)
            lines.append(f"{pad}{self.d_interactive} form{subtype}{' ' + attrs if attrs else ''}")
            for child in block.children:
                self._emit_block(child, lines, indent + 1)
            return

        if bt in ("input", "select", "button"):
            subtype = f".{block.subtype}" if block.subtype else ""
            attrs = self._format_attrs(block.attributes)
            lines.append(f"{pad}{self.d_interactive} {bt}{subtype}{' ' + attrs if attrs else ''}")
            if block.text:
                for line in block.text.splitlines():
                    lines.append(f"{pad}  {line}")
            return

    def _emit_error(self, block: CTXBlock, lines: list[str]) -> None:
        etype = block.attributes.get("type", "extraction-failed")
        lines.append(f"{self.d_section}error type={etype}")
        for key, val in block.attributes.items():
            if key == "type":
                continue
            lines.append(f"  {self.d_meta}{key}={quote_attr(val)}")
        lines.append("")

    def _emit_ref(self, ref: CTXBlock, lines: list[str]) -> None:
        parts = [f"{self.d_section}ref"]
        for key, val in ref.attributes.items():
            prefix = self.d_meta if _is_meta(key) else ""
            parts.append(f"{prefix}{key}={quote_attr(val)}")
        lines.append(" ".join(parts))

    def _format_attrs(self, attrs: dict[str, str]) -> str:
        parts = []
        for key, val in attrs.items():
            prefix = self.d_meta if _is_meta(key) else ""
            parts.append(f"{prefix}{key}={quote_attr(val)}")
        return " ".join(parts)


def emit(doc: CTXDocument | CTXDelta, target: str = "unicode") -> str:
    """Emit a CTX document or delta as text."""
    emitter = Emitter(target=target)
    if isinstance(doc, CTXDelta):
        return emitter.emit_delta(doc)
    return emitter.emit_document(doc)
