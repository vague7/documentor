"""MongoDB helpers.

Provides a lazily-initialised *singleton* `AsyncIOMotorClient` that other
modules can import without risking multiple connection pools.
"""
from __future__ import annotations

import os
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore

__all__ = ["get_mongo_client"]


_client: Optional[AsyncIOMotorClient] = None


def get_mongo_client() -> AsyncIOMotorClient:
    """Return a process-wide `AsyncIOMotorClient` instance.

    The connection string is read from the ``MONGODB_URI`` environment variable.
    This helper never raises on repeated calls and delays network IO until the
    first actual operation (Motor's lazy connection behaviour).
    """
    global _client

    if _client is None:
        mongo_uri = os.getenv("MONGODB_URI")
        if not mongo_uri:
            raise RuntimeError("Environment variable MONGODB_URI not set.")

        _client = AsyncIOMotorClient(mongo_uri)
        
    print("MongoDB client initialized")
    return _client 