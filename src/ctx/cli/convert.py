# Copyright 2026 Fox Valley AI Foundation
# SPDX-License-Identifier: Apache-2.0

"""ctx-convert CLI — convert URLs or HTML files to CTX format."""

from __future__ import annotations

import asyncio
import sys

import click


@click.command("ctx-convert")
@click.argument("source", required=False)
@click.option("--stdin", is_flag=True, help="Read HTML from stdin")
@click.option("--source-url", default="", help="Source URL when converting from file/stdin")
@click.option("--tier", type=click.Choice(["fast", "smart", "full"]), default="smart")
@click.option("--target", type=click.Choice(["unicode", "ascii"]), default="unicode")
@click.option("--strip-skip/--keep-skip", default=True, help="Strip [skip] block content")
@click.option("--vllm-url", default="http://localhost:8000/v1", help="vLLM API URL")
@click.option("-o", "--output", type=click.Path(), default=None, help="Output file")
def main(
    source: str | None,
    stdin: bool,
    source_url: str,
    tier: str,
    target: str,
    strip_skip: bool,
    vllm_url: str,
    output: str | None,
):
    """Convert a URL or HTML file to CTX format.

    \b
    Examples:
        ctx-convert https://example.com/article
        ctx-convert ./page.html --source-url https://example.com
        cat page.html | ctx-convert --stdin
        ctx-convert https://example.com --tier full -o article.ctx
    """
    from ..converter.pipeline import convert

    if stdin:
        html = sys.stdin.read()
        result = asyncio.run(convert(
            html,
            tier=tier,
            target=target,
            strip_skip=strip_skip,
            vllm_url=vllm_url,
            source_url=source_url,
        ))
    elif source and not source.startswith(("http://", "https://", "//")):
        # Local file
        import os
        if os.path.isfile(source):
            with open(source) as f:
                html = f.read()
            result = asyncio.run(convert(
                html,
                tier=tier,
                target=target,
                strip_skip=strip_skip,
                vllm_url=vllm_url,
                source_url=source_url or source,
            ))
        else:
            # Assume it's a URL without scheme
            result = asyncio.run(convert(
                source,
                tier=tier,
                target=target,
                strip_skip=strip_skip,
                vllm_url=vllm_url,
            ))
    elif source:
        result = asyncio.run(convert(
            source,
            tier=tier,
            target=target,
            strip_skip=strip_skip,
            vllm_url=vllm_url,
        ))
    else:
        click.echo("Error: provide a URL, file path, or use --stdin", err=True)
        sys.exit(1)

    if output:
        with open(output, "w") as f:
            f.write(result)
        click.echo(f"Written to {output}", err=True)
    else:
        click.echo(result, nl=False)


if __name__ == "__main__":
    main()
