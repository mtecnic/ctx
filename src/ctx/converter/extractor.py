# Copyright 2026 Fox Valley AI Foundation
# SPDX-License-Identifier: Apache-2.0

"""HTML content extraction — the heavy lifter of the converter pipeline."""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field
from urllib.parse import urljoin

from bs4 import BeautifulSoup, NavigableString, Tag, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
def _strip_math_annotations(soup: BeautifulSoup) -> None:
    """Strip LaTeX annotations from Wikipedia-style math elements.

    Wikipedia renders math as <span class="mwe-math-element"> containing both
    a <math> tree with <annotation encoding="application/x-tex"> and a fallback
    <img> with LaTeX in the alt text. We keep only the rendered math symbols
    and discard the raw LaTeX source.
    """
    # Kill all <annotation> tags (LaTeX source like {\displaystyle E})
    for ann in soup.find_all("annotation"):
        ann.decompose()

    # Kill math fallback images whose alt is LaTeX
    for img in soup.find_all("img", class_="mwe-math-fallback-image-inline"):
        img.decompose()
    for img in soup.find_all("img", class_="mwe-math-fallback-image-display"):
        img.decompose()

    # Unwrap <math> and <semantics> tags — keep their text children
    for tag_name in ("semantics", "math"):
        for tag in soup.find_all(tag_name):
            tag.unwrap()
from readability import Document as ReadabilityDoc

from ..models import CTXBlock

# Max skip blocks per document to avoid noise
MAX_SKIP_BLOCKS = 5


@dataclass
class ExtractionResult:
    """Raw extraction output before classification/annotation."""

    title: str = ""
    url: str = ""
    date: str = ""
    author: str = ""
    lang: str = ""
    description: str = ""
    content_blocks: list[CTXBlock] = field(default_factory=list)
    skip_blocks: list[CTXBlock] = field(default_factory=list)
    links: list[dict[str, str]] = field(default_factory=list)
    forms: list[CTXBlock] = field(default_factory=list)
    media: list[CTXBlock] = field(default_factory=list)
    tables: list[CTXBlock] = field(default_factory=list)
    meta: dict[str, str] = field(default_factory=dict)


def extract(html: str, url: str = "", tier: str = "fast") -> ExtractionResult:
    """Extract structured content from HTML."""
    result = ExtractionResult(url=url)

    if not html or not html.strip():
        return result

    # Parse full HTML for metadata and skip blocks
    soup = BeautifulSoup(html, "lxml")
    _extract_metadata(soup, result, url)
    _extract_skip_blocks(soup, result)

    # Use readability for main content extraction
    content_html = ""
    try:
        rdoc = ReadabilityDoc(html)
        result.title = result.title or rdoc.short_title()
        content_html = rdoc.summary()
    except Exception:
        pass

    # Parse the extracted content
    content_soup = BeautifulSoup(content_html, "lxml") if content_html else None

    # Check if readability produced useful content
    readability_ok = False
    if content_soup:
        text_len = len(content_soup.get_text(strip=True))
        readability_ok = text_len > 50

    # Fallback: use full body if readability produced nothing useful
    if not readability_ok:
        body = soup.find("body") or soup
        content_soup = BeautifulSoup(str(body), "lxml")

    # Extract forms from the FULL soup (readability strips them)
    _extract_forms(soup, result, url)

    # Extract tables from content
    _extract_tables(content_soup, result)

    # Extract media from content
    _extract_media(content_soup, result, url)

    # Extract text content (headings, paragraphs, code, quotes)
    _extract_text_content(content_soup, result, url)

    # Fallback: if still no paragraphs, try extracting text from divs
    if not any(b.block_type == "p" for b in result.content_blocks):
        _extract_div_text(content_soup, result, url)

    # Fallback: if STILL no content, try JSON-LD structured data
    if not any(b.block_type in ("p",) for b in result.content_blocks):
        _extract_jsonld_content(soup, result)

    # Fallback: if STILL no content, extract all visible text as one paragraph
    if not any(b.block_type in ("p", "section", "code", "quote") for b in result.content_blocks):
        _extract_visible_text(soup, result)

    # Title fallback: try <h1> if no title from <title>/OG/JSON-LD
    if not result.title:
        h1 = soup.find("h1")
        if h1:
            result.title = h1.get_text(strip=True)[:200]

    return result


def _extract_metadata(soup: BeautifulSoup, result: ExtractionResult, url: str) -> None:
    """Extract page metadata from <head>."""
    title_tag = soup.find("title")
    if title_tag:
        result.title = title_tag.get_text(strip=True)

    for meta in soup.find_all("meta"):
        name = meta.get("name", "") or meta.get("property", "")
        content = meta.get("content", "")
        if not name or not content:
            continue
        name_lower = name.lower()

        if name_lower in ("description", "og:description"):
            result.description = result.description or content
        elif name_lower in ("author", "article:author"):
            result.author = content
        elif name_lower in ("article:published_time", "date", "og:article:published_time"):
            result.date = content
        elif name_lower in ("og:title",):
            result.title = result.title or content
        elif name_lower in ("og:type",):
            result.meta["og_type"] = content
        elif name_lower in ("og:locale", "language"):
            result.lang = content[:2].lower()

        result.meta[name_lower] = content

    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        result.lang = result.lang or str(html_tag["lang"])[:2].lower()

    # JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            import json
            data = json.loads(script.string or "")
            if isinstance(data, list):
                data = data[0] if data else {}
            if isinstance(data, dict):
                result.meta["jsonld_type"] = data.get("@type", "")
                if "headline" in data:
                    result.title = result.title or data["headline"]
                if "datePublished" in data:
                    result.date = result.date or data["datePublished"]
                if "author" in data:
                    author = data["author"]
                    if isinstance(author, dict):
                        result.author = result.author or author.get("name", "")
                    elif isinstance(author, str):
                        result.author = result.author or author
                    elif isinstance(author, list) and author:
                        a = author[0]
                        if isinstance(a, dict):
                            result.author = result.author or a.get("name", "")
        except (json.JSONDecodeError, TypeError, IndexError):
            pass


def _extract_skip_blocks(soup: BeautifulSoup, result: ExtractionResult) -> None:
    """Identify nav, footer, sidebar, ad blocks.

    Caps at MAX_SKIP_BLOCKS to avoid noise from complex layouts.
    Only takes top-level elements — children of seen elements excluded.
    """
    seen_tags: set[int] = set()
    seen_text_prefixes: set[str] = set()  # dedup by text prefix

    def _is_descendant_of_seen(tag: Tag) -> bool:
        parent = tag.parent
        while parent:
            if id(parent) in seen_tags:
                return True
            parent = parent.parent
        return False

    def _add_skip(subtype: str, text: str) -> None:
        if len(result.skip_blocks) >= MAX_SKIP_BLOCKS:
            return
        prefix = text[:80]
        if prefix in seen_text_prefixes:
            return  # dedup: same text already captured
        seen_text_prefixes.add(prefix)
        result.skip_blocks.append(CTXBlock(
            block_type="skip", subtype=subtype, skip=True, text=text,
        ))

    skip_map = {"nav": "nav", "footer": "footer"}
    for tag_name, skip_type in skip_map.items():
        for tag in soup.find_all(tag_name):
            if len(result.skip_blocks) >= MAX_SKIP_BLOCKS:
                return
            if _is_descendant_of_seen(tag):
                continue
            seen_tags.add(id(tag))
            text = tag.get_text(separator=" ", strip=True)[:200]
            if text:
                _add_skip(skip_type, text)

    for tag in soup.find_all(attrs={"role": "complementary"}):
        if len(result.skip_blocks) >= MAX_SKIP_BLOCKS:
            return
        if _is_descendant_of_seen(tag):
            continue
        seen_tags.add(id(tag))
        text = tag.get_text(separator=" ", strip=True)[:200]
        if text:
            _add_skip("sidebar", text)

    for tag in soup.find_all(class_=re.compile(r"sidebar|aside|ad-|advertisement", re.I)):
        if len(result.skip_blocks) >= MAX_SKIP_BLOCKS:
            return
        if _is_descendant_of_seen(tag):
            continue
        seen_tags.add(id(tag))
        text = tag.get_text(separator=" ", strip=True)[:200]
        if text:
            _add_skip("sidebar", text)


def _extract_forms(soup: BeautifulSoup, result: ExtractionResult, url: str) -> None:
    """Extract form elements as interactive blocks."""
    for form in soup.find_all("form"):
        action = form.get("action", "")
        method = (form.get("method", "GET")).upper()
        form_id = form.get("id", "")

        if action and not action.startswith(("http", "/")):
            action = urljoin(url, action)

        form_block = CTXBlock(
            block_type="form",
            subtype=_classify_form(form),
            attributes={},
        )
        if form_id:
            form_block.attributes["id"] = f"form_{form_id}"
        if action:
            form_block.attributes["_action"] = f"{method}:{action}"

        for inp in form.find_all(["input", "select", "textarea", "button"]):
            child = _extract_input(inp, method, action)
            if child:
                form_block.children.append(child)

        if form_block.children:
            result.forms.append(form_block)


def _classify_form(form: Tag) -> str:
    action = (form.get("action", "") or "").lower()
    classes = " ".join(form.get("class", [])).lower()
    text = form.get_text(strip=True).lower()[:200]

    if "search" in action or "search" in classes or "search" in text:
        return "search"
    if "login" in action or "login" in classes or "sign in" in text:
        return "login"
    if "register" in action or "signup" in classes or "sign up" in text:
        return "register"
    if "contact" in action or "contact" in classes:
        return "contact"
    if "settings" in action or "profile" in classes or "preferences" in text:
        return "settings"
    return "generic"


def _extract_input(tag: Tag, form_method: str, form_action: str) -> CTXBlock | None:
    tag_name = tag.name

    if tag_name == "input":
        inp_type = (tag.get("type", "text")).lower()
        if inp_type in ("hidden", "submit"):
            if inp_type == "submit":
                return CTXBlock(
                    block_type="button",
                    subtype="submit",
                    attributes={
                        k: v for k, v in {
                            "id": tag.get("id", ""),
                            "label": tag.get("value", "Submit"),
                            "action": f"{form_method}:{form_action}" if form_action else "",
                        }.items() if v
                    },
                )
            return None
        name = tag.get("name", "")
        if not name:
            return None
        attrs: dict[str, str] = {}
        if tag.get("id"):
            attrs["id"] = f"inp_{tag['id']}"
        attrs["name"] = name
        if tag.get("placeholder"):
            attrs["label"] = tag["placeholder"]
        elif tag.get("aria-label"):
            attrs["label"] = tag["aria-label"]
        if tag.get("value"):
            attrs["value"] = tag["value"]
        return CTXBlock(block_type="input", subtype=inp_type, attributes=attrs)

    if tag_name == "select":
        name = tag.get("name", "")
        if not name:
            return None
        options = [opt.get_text(strip=True) for opt in tag.find_all("option")]
        selected = ""
        for opt in tag.find_all("option", selected=True):
            selected = opt.get_text(strip=True)
        attrs = {"name": name, "options": ",".join(options[:20])}
        if tag.get("id"):
            attrs["id"] = f"sel_{tag['id']}"
        if selected:
            attrs["value"] = selected
        if tag.get("aria-label"):
            attrs["label"] = tag["aria-label"]
        return CTXBlock(block_type="select", attributes=attrs)

    if tag_name == "textarea":
        name = tag.get("name", "")
        if not name:
            return None
        text = tag.get_text() or ""
        attrs = {"name": name}
        if tag.get("id"):
            attrs["id"] = f"inp_{tag['id']}"
        if tag.get("placeholder"):
            attrs["label"] = tag["placeholder"]
        return CTXBlock(block_type="input", subtype="textarea", attributes=attrs, text=text)

    if tag_name == "button":
        btn_type = tag.get("type", "button")
        label = tag.get_text(strip=True) or "Button"
        attrs_btn: dict[str, str] = {"label": label}
        if tag.get("id"):
            attrs_btn["id"] = f"btn_{tag['id']}"
        if btn_type == "submit" and form_action:
            attrs_btn["action"] = f"{form_method}:{form_action}"
        return CTXBlock(block_type="button", subtype=btn_type, attributes=attrs_btn)

    return None

    # Clean math markup before extraction
    _strip_math_annotations(content_soup)

def _extract_tables(soup: BeautifulSoup, result: ExtractionResult) -> None:
    for table in soup.find_all("table"):
        rows: list[str] = []
        cols: list[str] = []

        for th in table.find_all("th"):
            cols.append(th.get_text(strip=True))

        for tr in table.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if not cells:
                continue
            if all(c.name == "th" for c in cells) and cols:
                continue
            if not cols and all(c.name == "th" for c in cells):
                cols = [c.get_text(strip=True) for c in cells]
                continue
            row_text = " | ".join(c.get_text(strip=True) for c in cells)
            rows.append(row_text)

        if not rows and not cols:
            continue

        attrs: dict[str, str] = {}
        if cols:
            attrs["cols"] = ",".join(cols)
        if not rows:
            attrs["empty"] = "true"

        result.tables.append(CTXBlock(
            block_type="data", subtype="table", attributes=attrs, lines=rows,
        ))


def _extract_media(soup: BeautifulSoup, result: ExtractionResult, base_url: str) -> None:
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src or src.startswith("data:"):
            continue
        if not src.startswith("http"):
            src = urljoin(base_url, src)
        alt = img.get("alt", "")
        attrs: dict[str, str] = {"url": src}
        if alt:
            attrs["source"] = "alt-text"
        result.media.append(CTXBlock(
            block_type="media", subtype="image", attributes=attrs, text=alt or "Image",
        ))

    for vid in soup.find_all("video"):
        src = vid.get("src", "")
        if not src:
            source = vid.find("source")
            if source:
                src = source.get("src", "")
        if src and not src.startswith("http"):
            src = urljoin(base_url, src)
        result.media.append(CTXBlock(
            block_type="media", subtype="video",
            attributes={"url": src} if src else {},
            text=vid.get("alt", "Video"),
        ))


# Tags to skip when walking the DOM for text content
_SKIP_PARENT_TAGS = frozenset({
    "table", "tr", "td", "th", "form", "nav", "footer",
    "script", "style", "noscript", "svg", "head",
})

# Tags that contain article-like text but aren't <p>
_DIV_TEXT_TAGS = frozenset({"div", "span", "section", "article", "main", "td", "li"})


def _extract_text_content(soup: BeautifulSoup, result: ExtractionResult, base_url: str) -> None:
    """Extract headings, paragraphs, code blocks, and blockquotes."""
    body = soup.find("body") or soup

    for element in body.descendants:
        if not isinstance(element, Tag):
            continue

        if element.parent and element.parent.name in _SKIP_PARENT_TAGS:
            continue

        if element.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            depth = min(int(element.name[1]), 4)
            text = element.get_text(strip=True)
            if text:
                heading_id = element.get("id", "")
                attrs = {"id": heading_id} if heading_id else {}
                result.content_blocks.append(CTXBlock(
                    block_type="section", depth=depth, text=text, attributes=attrs,
                ))

        elif element.name == "p":
            if element.parent and element.parent.name in ("blockquote", "figcaption"):
                continue
            text, links = _extract_paragraph_with_links(element, base_url)
            if text.strip():
                result.content_blocks.append(CTXBlock(block_type="p", text=text.strip()))
                result.links.extend(links)

        elif element.name in ("pre", "code"):
            if element.name == "code" and element.parent and element.parent.name == "pre":
                continue
            code_text = element.get_text()
            lang = ""
            code_el = element.find("code") if element.name == "pre" else element
            if code_el and code_el.get("class"):
                for cls in code_el["class"]:
                    if cls.startswith("language-") or cls.startswith("lang-"):
                        lang = cls.split("-", 1)[1]
                        break
            if code_text.strip():
                attrs = {"lang": lang} if lang else {}
                result.content_blocks.append(CTXBlock(
                    block_type="code", text=code_text.rstrip(), attributes=attrs,
                ))

        elif element.name == "blockquote":
            text = element.get_text(separator="\n", strip=True)
            if text:
                result.content_blocks.append(CTXBlock(block_type="quote", text=text))

        elif element.name in ("ul", "ol"):
            if element.parent and element.parent.name in ("ul", "ol", "nav"):
                continue
            items = []
            for li in element.find_all("li", recursive=False):
                item_text, links = _extract_paragraph_with_links(li, base_url)
                if item_text.strip():
                    items.append(item_text.strip())
                    result.links.extend(links)
            if items:
                result.content_blocks.append(CTXBlock(
                    block_type="data", subtype="list", lines=items,
                ))


def _extract_div_text(soup: BeautifulSoup, result: ExtractionResult, base_url: str) -> None:
    """Fallback: extract text from div/span/article/section elements.

    Used when no <p> tags are found (common in SPAs and modern frameworks
    that use <div> for everything).
    """
    body = soup.find("body") or soup
    seen_text: set[str] = set()

    # Priority containers: <article> and <main> get a lower threshold
    _priority_tags = frozenset({"article", "main"})

    for element in body.descendants:
        if not isinstance(element, Tag):
            continue
        if element.name not in _DIV_TEXT_TAGS:
            continue
        if element.parent and element.parent.name in _SKIP_PARENT_TAGS:
            continue

        direct_text = element.find(string=True, recursive=False)
        if not direct_text:
            continue

        text, links = _extract_paragraph_with_links(element, base_url)
        text = text.strip()

        # Priority containers (article, main) get lower threshold
        min_len = 20 if element.name in _priority_tags else 40
        if len(text) < min_len:
            continue

        text_key = text[:100]
        if text_key in seen_text:
            continue
        seen_text.add(text_key)

        result.content_blocks.append(CTXBlock(block_type="p", text=text))
        result.links.extend(links)

        if len(result.content_blocks) > 50:
            break


def _extract_jsonld_content(soup: BeautifulSoup, result: ExtractionResult) -> None:
    """Fallback: extract content from JSON-LD structured data.

    Many movie/music/product/article pages embed rich descriptions in
    JSON-LD that readability can't parse (SPAs, JS-rendered content).
    """
    import json

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                for item in data:
                    _extract_from_jsonld_object(item, result)
            elif isinstance(data, dict):
                _extract_from_jsonld_object(data, result)
        except (json.JSONDecodeError, TypeError):
            pass


def _extract_from_jsonld_object(data: dict, result: ExtractionResult) -> None:
    """Extract text content from a single JSON-LD object."""
    if not isinstance(data, dict):
        return

    # Text fields to extract, in priority order
    text_fields = [
        "articleBody", "description", "abstract", "reviewBody",
        "text", "backstory",
    ]
    for field in text_fields:
        value = data.get(field, "")
        if isinstance(value, str) and len(value) > 30:
            # Avoid duplicating the og:description we already have
            if value == result.description:
                continue
            result.content_blocks.append(CTXBlock(block_type="p", text=value[:3000]))
            return  # one substantial text per JSON-LD object is enough

    # Try nested objects (e.g., mainEntity, review)
    for key in ("mainEntity", "review", "itemReviewed"):
        nested = data.get(key)
        if isinstance(nested, dict):
            _extract_from_jsonld_object(nested, result)
        elif isinstance(nested, list):
            for item in nested[:3]:  # cap at 3 nested items
                if isinstance(item, dict):
                    _extract_from_jsonld_object(item, result)


def _extract_visible_text(soup: BeautifulSoup, result: ExtractionResult) -> None:
    """Last-resort fallback: extract all visible text as paragraphs.

    Used when both <p> and div-text extraction produce nothing.
    Common for JS-rendered SPAs where the HTML is mostly empty scaffolding.
    """
    body = soup.find("body") or soup

    # Strip script/style/nav/footer
    for tag in body.find_all(["script", "style", "noscript", "nav", "footer", "svg"]):
        tag.decompose()

    text = body.get_text(separator="\n", strip=True)
    if not text or len(text) < 30:
        return

    # Split into chunks by double newlines or long gaps
    paragraphs = re.split(r"\n{2,}", text)
    for para in paragraphs:
        para = para.strip()
        if len(para) >= 30:
            result.content_blocks.append(CTXBlock(block_type="p", text=para[:2000]))
            if len(result.content_blocks) > 30:
                break


def _extract_paragraph_with_links(
    element: Tag, base_url: str
) -> tuple[str, list[dict[str, str]]]:
    """Extract text from an element, collecting inline links for citation generation."""
    parts: list[str] = []
    links: list[dict[str, str]] = []

    for child in element.children:
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif isinstance(child, Tag):
            if child.name == "a":
                href = child.get("href", "")
                text = child.get_text(strip=True)
                if href and text:
                    if not href.startswith(("http", "//", "#", "javascript:", "mailto:")):
                        href = urljoin(base_url, href)
                    if href.startswith(("#", "javascript:", "mailto:")):
                        parts.append(text)
                    else:
                        links.append({"url": href, "text": text})
                        parts.append(f"{text} [__link:{len(links) - 1}]")
                else:
                    parts.append(child.get_text())
            elif child.name in ("em", "i"):
                parts.append(f"_{child.get_text(strip=True)}_")
            elif child.name in ("strong", "b"):
                parts.append(f"_{child.get_text(strip=True)}_")
            elif child.name in ("code",):
                parts.append(child.get_text())
            elif child.name == "br":
                parts.append("\n")
            elif child.name in ("span", "div", "time"):
                # Recurse into inline containers
                inner_text, inner_links = _extract_paragraph_with_links(child, base_url)
                parts.append(inner_text)
                links.extend(inner_links)
            else:
                parts.append(child.get_text())

    return "".join(parts), links
