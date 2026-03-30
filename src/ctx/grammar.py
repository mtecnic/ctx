# Copyright 2026 Fox Valley AI Foundation
# SPDX-License-Identifier: Apache-2.0

"""CTX v1.0 grammar constants derived from the EBNF specification."""

# --- Delimiters ---
DELIMITERS = {
    "section": "\u00a7",     # §
    "metadata": "\u2020",   # †
    "media": "\u25c6",      # ◆
    "interactive": "\u25b8", # ▸
    "data": "\u2237",       # ∷
}

ASCII_FALLBACKS = {
    "media": "<>",
    "interactive": ">>",
    "data": "::",
}

# All reserved delimiter chars (for escaping)
RESERVED_DELIMITERS = set(DELIMITERS.values())

# --- Block types ---
SKIP_TYPES = frozenset({"nav", "sidebar", "footer", "ad", "auth", "cookie"})

LEAF_TYPES = frozenset({"p", "code", "quote", "aside"})

DATA_TYPES = frozenset({"table", "json", "list", "kv"})

MEDIA_TYPES = frozenset({"image", "video", "audio", "chart", "attachment"})

ERROR_TYPES = frozenset({
    "extraction-failed", "fetch-failed", "auth-required",
    "format-unsupported", "truncated", "vision-failed",
})

REL_TYPES = frozenset({
    "continuation", "source", "data-source", "related",
    "parent", "child", "next", "prev", "spec", "api", "canonical",
})

# --- Content subtypes ---
KNOWN_CONTENT_TYPES = frozenset({
    "article", "product", "email", "video",
    "application", "reference",
})

# --- Column type hints ---
COLUMN_TYPE_HINTS = frozenset({
    "string", "int", "float", "bool",
    "date", "datetime", "url", "currency",
})

# --- Boolean normalization ---
BOOL_TRUE = frozenset({"true", "yes", "y", "1", "on", "\u2705"})   # ✅
BOOL_FALSE = frozenset({"false", "no", "n", "0", "off", "\u274c", ""})  # ❌

# --- Depth range ---
MIN_DEPTH = 1
MAX_DEPTH = 4

# --- Auth methods ---
AUTH_METHODS = frozenset({"bearer", "basic", "api-key", "form"})

# --- Version ---
CTX_VERSION = "1.0"
DOC_PREFIX = f"\u00a7doc.ctx_v{CTX_VERSION}"  # §doc.ctx_v1.0

# --- Extraction tiers ---
EXTRACTION_TIERS = frozenset({"fast", "smart", "full"})
DEFAULT_TIER = "smart"
