"""Initialise MongoDB indexes for the chat history store.

Run once after provisioning a new environment:

    python -m backend.scripts.init_indexes

The script reads `MONGODB_URI` from the environment (or .env file loaded by
Pydantic Settings) and creates the required indexes idempotently.
"""
from __future__ import annotations

import asyncio
import os

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()


MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("MONGODB_DB", "documentor")

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI not set – cannot connect to Atlas")


async def main():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]

    # Collection choice: flat `messages` collection (one doc per message).
    coll = db["messages"]

    # 1) Compound index to optimise session look-ups and ordering by insertion.
    # Order 1 = ASC, we also add created_at so queries can use sort.
    await coll.create_index([("session_id", 1), ("created_at", 1)])

    # 2) Optional TTL index (disabled by default) – uncomment if you wish to
    #    auto-purge old messages.
    # await coll.create_index("created_at", expireAfterSeconds=60*60*24*30)

    print("✅ MongoDB indexes ensured for collection 'messages'")
    client.close()


if __name__ == "__main__":
    asyncio.run(main()) 