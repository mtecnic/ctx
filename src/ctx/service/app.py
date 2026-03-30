# Copyright 2026 Fox Valley AI Foundation
# SPDX-License-Identifier: Apache-2.0

"""FastAPI application for CTX converter service."""

from __future__ import annotations

from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI

from .config import config
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown: initialize Redis connection."""
    try:
        app.state.redis = aioredis.from_url(
            config.REDIS_URL,
            decode_responses=True,
        )
        await app.state.redis.ping()
    except Exception:
        app.state.redis = None  # Redis unavailable, run without cache

    yield

    if app.state.redis:
        await app.state.redis.aclose()


app = FastAPI(
    title="CTX Converter Service",
    version="1.0.0",
    description="Convert web content to CTX (Context Transfer Format) for token-efficient LLM consumption.",
    lifespan=lifespan,
)

app.include_router(router)
