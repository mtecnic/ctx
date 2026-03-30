# Copyright 2026 Fox Valley AI Foundation
# SPDX-License-Identifier: Apache-2.0

"""Annotation stage — skip blocks, citation generation, depth mapping."""

from __future__ import annotations

import re

from ..models import CTXBlock
from .extractor import ExtractionResult


def annotate(result: ExtractionResult, content_type: str) -> list[CTXBlock]:
    """Build the final block tree with citations and proper structure.

    Returns the top-level list of blocks for the document.
    """
    blocks: list[CTXBlock] = []

    # Skip blocks first
    for skip in result.skip_blocks:
        blocks.append(skip)

    # Content container
    content = CTXBlock(
        block_type="content",
        subtype=content_type,
    )

    # Citation registry — maps link index to refN
    citation_map: dict[int, int] = {}
    ref_counter = 0
    refs: list[CTXBlock] = []
    link_pattern = re.compile(r"\[__link:(\d+)\]")

    def _register_citations(text: str) -> None:
        """Scan text for [__link:N] placeholders and register refs."""
        nonlocal ref_counter
        for match in link_pattern.finditer(text):
            link_idx = int(match.group(1))
            if link_idx not in citation_map and link_idx < len(result.links):
                ref_counter += 1
                citation_map[link_idx] = ref_counter
                link = result.links[link_idx]
                refs.append(CTXBlock(
                    block_type="ref",
                    attributes={
                        "id": f"ref{ref_counter}",
                        "url": link["url"],
                        "title": link["text"],
                        "rel": "related",
                    },
                ))

    def _replace_citations(text: str) -> str:
        """Replace [__link:N] placeholders with [refN] citation pointers."""
        def _sub(m: re.Match) -> str:
            idx = int(m.group(1))
            if idx in citation_map:
                return f"[ref{citation_map[idx]}]"
            return ""
        return link_pattern.sub(_sub, text)

    # Process ALL content blocks for citations — not just §p
    for block in result.content_blocks:
        # Process text field (paragraphs, sections, quotes, etc.)
        if block.text and link_pattern.search(block.text):
            _register_citations(block.text)
            new_text = _replace_citations(block.text)
            block = CTXBlock(
                block_type=block.block_type,
                subtype=block.subtype,
                depth=block.depth,
                text=new_text,
                attributes=block.attributes,
                skip=block.skip,
                children=block.children,
                lines=block.lines,
            )

        # Process lines (list items, data rows)
        if block.lines:
            new_lines = []
            changed = False
            for line in block.lines:
                if link_pattern.search(line):
                    _register_citations(line)
                    new_lines.append(_replace_citations(line))
                    changed = True
                else:
                    new_lines.append(line)
            if changed:
                block = CTXBlock(
                    block_type=block.block_type,
                    subtype=block.subtype,
                    depth=block.depth,
                    text=block.text,
                    attributes=block.attributes,
                    lines=new_lines,
                )

        content.children.append(block)

    # Add tables
    for table in result.tables:
        content.children.append(table)

    # Add media
    for media in result.media:
        content.children.append(media)

    # Add forms
    for form in result.forms:
        content.children.append(form)

    # Synthetic §1 from title when no headings found
    has_sections = any(b.block_type == "section" for b in content.children)
    if not has_sections and result.title:
        content.children.insert(0, CTXBlock(
            block_type="section",
            depth=1,
            text=result.title,
        ))

    blocks.append(content)
    blocks.extend(refs)

    return blocks


def build_section_tree(blocks: list[CTXBlock]) -> list[CTXBlock]:
    """Nest content blocks under their section headings by depth."""
    if not blocks:
        return blocks

    content_block = None
    other_blocks = []
    for b in blocks:
        if b.block_type == "content":
            content_block = b
        else:
            other_blocks.append(b)

    if not content_block:
        return blocks

    root_children: list[CTXBlock] = []
    section_stack: list[CTXBlock] = []

    for child in content_block.children:
        if child.block_type == "section":
            depth = child.depth or 1
            while section_stack and (section_stack[-1].depth or 1) >= depth:
                section_stack.pop()
            if section_stack:
                section_stack[-1].children.append(child)
            else:
                root_children.append(child)
            section_stack.append(child)
        else:
            if section_stack:
                section_stack[-1].children.append(child)
            else:
                root_children.append(child)

    content_block.children = root_children

    result = []
    for b in other_blocks:
        if b.block_type in ("skip", "nav", "footer", "sidebar"):
            result.append(b)
    result.append(content_block)
    for b in other_blocks:
        if b.block_type == "ref":
            result.append(b)
    return result
