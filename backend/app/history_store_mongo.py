"""MongoDB-backed chat history store.

Implements the same contract as *InMemoryHistoryStore* but persists every
message in a flat *messages* collection so multiple API replicas can share the
conversation log and the data survives process restarts.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import List

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import BaseMessage, messages_from_dict, messages_to_dict

from app.mongo import get_mongo_client
from app.history_store import AbstractHistoryStore

# MongoDB / Atlas constants ---------------------------------------------------
DB_NAME = "documentor"
COLLECTION_NAME = "messages"


# Helpers ---------------------------------------------------------------------

def _serialise_message(msg: BaseMessage) -> dict:  # noqa: D401
    """Convert a LangChain *BaseMessage* into the dict format stored in Mongo."""
    d = messages_to_dict([msg])[0]  # type: ignore[arg-type]
    return {
        "session_id": None,  # filled by caller
        "message": d,
        "created_at": datetime.now(timezone.utc),
    }


def _deserialise_messages(raw: List[dict]) -> List[BaseMessage]:
    return messages_from_dict([doc["message"] for doc in raw])


# Proxy wrapper ---------------------------------------------------------------

class _PersistentChatHistory(ChatMessageHistory):
    """`ChatMessageHistory` that writes to Mongo on every message append."""

    def __init__(self, session_id: str, store: "MongoHistoryStore", initial: List[BaseMessage]):
        super().__init__(initial)  # type: ignore[arg-type]
        self._session_id = session_id
        self._store = store

    def add_message(self, message: BaseMessage) -> None:  # type: ignore[override]
        super().add_message(message)
        # Fire-and-forget persistence to avoid blocking (best-effort)
        try:
            self._store.append(self._session_id, message)
        except Exception:  # pragma: no cover – never crash user flow
            pass


# Store implementation --------------------------------------------------------

class MongoHistoryStore(AbstractHistoryStore):
    """Conversation-history store backed by MongoDB Atlas."""

    def __init__(self, db_name: str = DB_NAME, collection: str = COLLECTION_NAME):
        self._client = get_mongo_client()
        self._coll = self._client[db_name][collection]

    # ------------------------------------------------------------------
    # Public API (sync signature, runs async ops via asyncio)
    # ------------------------------------------------------------------
    def get(self, session_id: str):  # type: ignore[override]
        """Return `ChatMessageHistory` for *session_id*, creating it if necessary."""
        raw_docs = asyncio.run(self._async_fetch(session_id))
        msgs = _deserialise_messages(raw_docs)
        return _PersistentChatHistory(session_id, self, msgs)

    def append(self, session_id: str, message: BaseMessage):
        asyncio.run(self._async_append(session_id, message))

    def clear(self, session_id: str) -> None:
        asyncio.run(self._async_clear(session_id))

    # ------------------------------------------------------------------
    # Internal async helpers
    # ------------------------------------------------------------------
    async def _async_fetch(self, session_id: str):
        cursor = self._coll.find({"session_id": session_id}).sort("created_at", 1)
        return await cursor.to_list(length=None)

    async def _async_append(self, session_id: str, message: BaseMessage):
        doc = _serialise_message(message)
        doc["session_id"] = session_id
        await self._coll.insert_one(doc)

    async def _async_clear(self, session_id: str):
        await self._coll.delete_many({"session_id": session_id}) 