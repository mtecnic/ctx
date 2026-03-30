# Copyright 2026 Fox Valley AI Foundation
# SPDX-License-Identifier: Apache-2.0

"""Service configuration from environment variables."""

from __future__ import annotations

import os


class Config:
    PORT: int = int(os.environ.get("CTX_PORT", "8200"))
    HOST: str = os.environ.get("CTX_HOST", "0.0.0.0")
    REDIS_URL: str = os.environ.get("CTX_REDIS_URL", "redis://localhost:6379/1")
    VLLM_URL: str = os.environ.get("CTX_VLLM_URL", "http://localhost:8000/v1")
    DEFAULT_TIER: str = os.environ.get("CTX_DEFAULT_TIER", "smart")
    CACHE_TTL: int = int(os.environ.get("CTX_CACHE_TTL", "3600"))  # 1 hour
    CACHE_TTL_FULL: int = int(os.environ.get("CTX_CACHE_TTL_FULL", "14400"))  # 4 hours
    WORKERS: int = int(os.environ.get("CTX_WORKERS", "2"))


config = Config()
