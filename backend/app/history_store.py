"""Shared conversation-history store.

Phase-1 deliverable: Provides a thin abstraction around LangChain's
`InMemoryChatMessageHistory` so that multiple endpoints (chat & agent)
can share the same underlying cache without being coupled to a concrete
implementation.
"""
from __future__ import annotations

from typing import Dict, Protocol
import os

from langchain_core.chat_history import InMemoryChatMessageHistory, BaseChatMessageHistory
from langchain_core.messages import BaseMessage
from app.config import logger
# Conditional import to avoid heavy deps when not needed
try:
    from app.history_store_mongo import MongoHistoryStore  # noqa: F401
except Exception:  # pragma: no cover – optional dependency not available yet
    MongoHistoryStore = None  # type: ignore
    #logger.error("MongoHistoryStore is not available")


class AbstractHistoryStore(Protocol):
    """Contract for a history-storage backend."""

    def get(self, session_id: str) -> BaseChatMessageHistory:  # pragma: no cover
        """Return (and create if necessary) the history for *session_id*."""
        ...

    def clear(self, session_id: str) -> None:  # pragma: no cover
        """Remove the conversation identified by *session_id* if it exists."""
        ...


class InMemoryHistoryStore(AbstractHistoryStore):
    """Process-local dictionary-based store – good enough for dev & unit tests."""

    _store: Dict[str, InMemoryChatMessageHistory]

    # -----------------------------------------------------------------
    # Helper: ensure message.content is always a string (Gemini safeguard)
    # -----------------------------------------------------------------
    class _SafeChatHistory(InMemoryChatMessageHistory):
        """In-memory history that prevents list-style content from being stored."""

        @staticmethod
        def _flatten_content(msg: BaseMessage):  # type: ignore[override]
            if isinstance(getattr(msg, "content", None), list):
                msg.content = "\n".join(map(str, msg.content))  # type: ignore[attr-defined]

        def add_message(self, message: BaseMessage):  # type: ignore[override]
            self._flatten_content(message)
            super().add_message(message)

        def __init__(self, **data):  # type: ignore[override]
            super().__init__(**data)
            # Repair any legacy bad messages already present
            for m in self.messages:
                self._flatten_content(m)

    def __init__(self) -> None:
        self._store = {}

    # ---------------------------------------------------------------------
    # API
    # ---------------------------------------------------------------------
    def get(self, session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in self._store:
            self._store[session_id] = self._SafeChatHistory()
        # DEBUG observability – helpful in production support
        try:
            from app.config import logger  # local import avoids circularity

            logger.debug(
                "HistoryStore.get(session=%s) -> size=%d", session_id, len(self._store)
            )
        except Exception:
            # Never break functional flow because of logging issues
            pass

        return self._store[session_id]

    def clear(self, session_id: str) -> None:
        self._store.pop(session_id, None)

    # ---------------------------------------------------------------------
    # Convenience helpers
    # ---------------------------------------------------------------------
    def __len__(self) -> int:  # pragma: no cover
        return len(self._store)

    def __contains__(self, session_id: str) -> bool:  # pragma: no cover
        return session_id in self._store


# ---------------------------------------------------------------------
# Backend selection (env-flag)
# ---------------------------------------------------------------------

backend_choice = os.getenv("HISTORY_BACKEND", "mongo").lower()

if backend_choice == "mongo" and MongoHistoryStore is not None:
    DEFAULT_HISTORY_STORE = MongoHistoryStore()  # type: ignore
else:
    DEFAULT_HISTORY_STORE = InMemoryHistoryStore()

__all__ = [
    "AbstractHistoryStore",
    "InMemoryHistoryStore",
    "DEFAULT_HISTORY_STORE",
] 