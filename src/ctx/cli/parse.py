# Copyright 2026 Fox Valley AI Foundation
# SPDX-License-Identifier: Apache-2.0

"""ctx-parse CLI — parse and validate CTX documents."""

from __future__ import annotations

import json
import sys

import click


@click.command("ctx-parse")
@click.argument("file", type=click.Path(exists=True))
@click.option("--validate", is_flag=True, help="Validate and report errors")
@click.option("--json-out", "json_output", is_flag=True, help="Output as JSON")
@click.option("--tree", is_flag=True, help="Show document structure tree")
@click.option("--refs", is_flag=True, help="Extract just the §ref blocks")
def main(file: str, validate: bool, json_output: bool, tree: bool, refs: bool):
    """Parse a CTX file and display its structure.

    \b
    Examples:
        ctx-parse article.ctx --validate
        ctx-parse article.ctx --json
        ctx-parse article.ctx --tree
        ctx-parse article.ctx --refs
    """
    from ..parser import parse

    with open(file) as f:
        text = f.read()

    doc = parse(text)

    if validate:
        errors = _validate(doc)
        if errors:
            for err in errors:
                click.echo(f"  ERROR: {err}", err=True)
            sys.exit(1)
        else:
            click.echo("Valid CTX document.")
        return

    if json_output:
        click.echo(json.dumps(doc.model_dump(), indent=2))
        return

    if refs:
        for ref in doc.refs:
            attrs = " ".join(f"{k}={v}" for k, v in ref.attributes.items())
            click.echo(f"\u00a7ref {attrs}")
        return

    if tree:
        _print_tree(doc)
        return

    # Default: summary
    click.echo(f"CTX v{doc.version}")
    click.echo(f"URL: {doc.header.attributes.get('url', '?')}")
    click.echo(f"Title: {doc.header.attributes.get('title', '?')}")
    click.echo(f"Type: {doc.header.attributes.get('type', '?')}")
    click.echo(f"Content blocks: {sum(len(c.children) for c in doc.content)}")
    click.echo(f"References: {len(doc.refs)}")


def _validate(doc):
    """Basic validation checks."""
    errors = []
    if not doc.header.attributes.get("url") and not doc.header.attributes.get("source"):
        errors.append("Missing required 'url' or 'source' in document header")
    if not doc.version:
        errors.append("Missing version in document header")

    # Check ref ID uniqueness
    ref_ids = [r.attributes.get("id", "") for r in doc.refs if r.attributes.get("id")]
    if len(ref_ids) != len(set(ref_ids)):
        errors.append("Duplicate §ref id values")

    return errors


def _print_tree(doc, indent=0):
    """Print document structure as a tree."""
    pad = "  " * indent
    click.echo(f"{pad}\u00a7doc.ctx_v{doc.version}")
    if doc.summary:
        click.echo(f"{pad}  \u00a7summary")
    for block in doc.content:
        _print_block(block, indent + 1)
    for ref in doc.refs:
        rid = ref.attributes.get("id", "")
        url = ref.attributes.get("url", "")
        click.echo(f"{pad}  \u00a7ref {rid} → {url}")


def _print_block(block, indent):
    pad = "  " * indent
    label = block.block_type
    if block.subtype:
        label += f".{block.subtype}"
    if block.depth:
        label = f"\u00a7{block.depth}"
    if block.skip:
        label += " [skip]"
    extra = ""
    if block.text:
        extra = f" — {block.text[:60]}{'...' if len(block.text) > 60 else ''}"
    click.echo(f"{pad}{label}{extra}")
    for child in block.children:
        _print_block(child, indent + 1)


if __name__ == "__main__":
    main()
